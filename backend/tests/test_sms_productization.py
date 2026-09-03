"""Focused tests for the fixed two-provider SMS settings contract."""

from typing import Any

import pytest
from fakeredis import aioredis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.api.v1.module_storage.core.encrypt import decrypt_password, encrypt_password
from app.api.v1.module_system.params.model import ParamsModel
from app.api.v1.module_system.user.model import UserModel
from app.common.enums import EnvironmentEnum
from app.config.setting import settings
from app.core.base_schema import AuthSchema
from app.core.exceptions import CustomException
from app.plugin.module_system.sms.constants import get_fixed_sms_code
from app.plugin.module_system.sms.provider import MockSmsProvider, SmsProviderResult, TencentSmsProvider
from app.plugin.module_system.sms.service import SmsService
from app.plugin.module_system.sms.settings_schema import (
    SmsProviderSettingsUpdateSchema,
    SmsSettingsUpdateSchema,
    SmsTemplateSettingsSchema,
)
from app.plugin.module_system.sms.settings_service import SmsSettingsService
from app.plugin.module_system.sms_channel.model import SmsChannelModel
from app.plugin.module_system.sms_log.model import SmsLogModel
from app.plugin.module_system.sms_template.model import SmsTemplateModel


@pytest.fixture
async def product_context():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool)
    async with engine.begin() as connection:
        for table in (
            UserModel.__table__,
            ParamsModel.__table__,
            SmsChannelModel.__table__,
            SmsTemplateModel.__table__,
            SmsLogModel.__table__,
        ):
            await connection.run_sync(table.create)

    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    redis = aioredis.FakeRedis(decode_responses=True)
    async with session_factory() as db:
        yield db, redis
    await redis.aclose()
    await engine.dispose()


def provider_config(provider: str, *, enabled: bool, secret: str | None = "secret-value") -> SmsProviderSettingsUpdateSchema:
    is_tencent = provider == "tencent"
    return SmsProviderSettingsUpdateSchema(
        enabled=enabled,
        access_key_id=f"{provider}-credential-id" if enabled else "",
        access_key_secret=secret if enabled else "",
        sms_sdk_app_id="1400000000" if is_tencent and enabled else None,
        sign_name="Starter 签名" if enabled else "",
        templates=SmsTemplateSettingsSchema(
            register_code=f"{provider}-register" if enabled else "",
            login_code=f"{provider}-login" if enabled else "",
            reset_password_code=f"{provider}-reset" if enabled else "",
        ),
    )


def settings_payload(*, sms_enabled: bool, active_provider: str = "aliyun", secret: str | None = "secret-value") -> SmsSettingsUpdateSchema:
    return SmsSettingsUpdateSchema(
        sms_enabled=sms_enabled,
        active_provider=active_provider,
        aliyun=provider_config("aliyun", enabled=True, secret=secret),
        tencent=provider_config("tencent", enabled=True, secret=secret),
    )


@pytest.mark.asyncio
async def test_settings_resolve_both_fixed_providers_and_all_auth_templates(product_context):
    db, redis = product_context
    payload = settings_payload(sms_enabled=True, active_provider="tencent")
    output = await SmsSettingsService(AuthSchema(), db).update(payload, redis)

    assert output.sms_enabled is True
    assert output.active_provider == "tencent"
    assert output.aliyun.enabled is True
    assert output.tencent.enabled is True
    assert output.aliyun.has_secret is True
    assert output.tencent.has_secret is True

    calls: dict[str, list[dict[str, Any]]] = {"aliyun": [], "tencent": []}
    providers = {
        provider: MockSmsProvider(
            SmsProviderResult(provider=provider, success=True, code="OK", message="ok", request_id=f"{provider}-rid"),
        )
        for provider in calls
    }
    service = SmsService(db, redis, provider_factory=lambda channel: providers[channel.provider])
    for scene, _template_code in (
        ("register_code", "tencent-register"),
        ("login_code", "tencent-login"),
        ("reset_password_code", "tencent-reset"),
    ):
        await service.test_send(mobile="13800138000", scene=scene, params={"code": "123456"})

    for call in providers["tencent"].calls:
        calls["tencent"].append(call)
    assert [call["template_code"] for call in calls["tencent"]] == [
        "tencent-register",
        "tencent-login",
        "tencent-reset",
    ]
    assert all(call["params"] == {"code": "123456"} for call in calls["tencent"])
    assert not providers["aliyun"].calls

    channels = (await db.execute(select(SmsChannelModel))).scalars().all()
    templates = (await db.execute(select(SmsTemplateModel))).scalars().all()
    assert sorted(channel.provider for channel in channels) == ["aliyun", "tencent"]
    assert len(templates) == 6


@pytest.mark.asyncio
async def test_secret_is_preserved_and_never_returned_as_plaintext(product_context):
    db, redis = product_context
    service = SmsSettingsService(AuthSchema(), db)
    await service.update(settings_payload(sms_enabled=False, secret="original-secret"), redis)

    second_payload = settings_payload(sms_enabled=False, secret="")
    output = await service.update(second_payload, redis)
    channel = (
        await db.execute(select(SmsChannelModel).where(SmsChannelModel.provider == "aliyun"))
    ).scalar_one()

    assert decrypt_password(channel.access_key_secret) == "original-secret"
    assert output.aliyun.has_secret is True
    assert "access_key_secret" not in output.model_dump()
    assert "secret-value" not in str(output.model_dump())


@pytest.mark.asyncio
async def test_global_off_stops_real_delivery_before_provider_resolution(product_context, monkeypatch):
    db, redis = product_context
    monkeypatch.setattr(settings, "APP_SMS_FIXED_CODE_ENABLED", False)

    provider_called = False

    def provider_factory(_channel):
        nonlocal provider_called
        provider_called = True
        return MockSmsProvider()

    with pytest.raises(CustomException) as error:
        await SmsService(db, redis, provider_factory=provider_factory).send_code(
            mobile="13800138000",
            scene="register_code",
        )

    assert error.value.status_code == 503
    assert "未启用" in error.value.msg
    assert provider_called is False


@pytest.mark.asyncio
async def test_selected_disabled_provider_fails_closed_with_clear_error(product_context, monkeypatch):
    db, redis = product_context
    monkeypatch.setattr(settings, "APP_SMS_FIXED_CODE_ENABLED", False)
    db.add_all(
        [
            ParamsModel(config_name="短信服务启用", config_key="sms_enabled", config_value="on", config_type=True, status=0),
            ParamsModel(config_name="短信当前供应商", config_key="sms_active_provider", config_value="tencent", config_type=True, status=0),
            SmsChannelModel(
                name="Starter 腾讯云短信",
                provider="tencent",
                access_key_id="secret-id",
                access_key_secret=encrypt_password("secret-key"),
                sms_sdk_app_id="1400000000",
                sign_name="Starter 签名",
                status=1,
                is_default=False,
            ),
        ],
    )
    for scene in ("register_code", "login_code", "reset_password_code"):
        db.add(
            SmsTemplateModel(
                name=scene,
                scene=scene,
                provider="tencent",
                provider_template_code=f"tencent-{scene}",
                param_schema=["code"],
                status=0,
            ),
        )
    await db.flush()

    with pytest.raises(CustomException) as error:
        await SmsService(db, redis).send_code(mobile="13800138000", scene="register_code")

    assert error.value.status_code == 503
    assert "腾讯云" in error.value.msg
    assert "停用" in error.value.msg


@pytest.mark.asyncio
async def test_tencent_adapter_maps_official_send_sms_request_without_network(monkeypatch):
    from tencentcloud.common import credential
    from tencentcloud.sms.v20210111 import models, sms_client

    captured: dict[str, Any] = {}

    class FakeCredential:
        def __init__(self, secret_id: str, secret_key: str):
            captured["credential"] = (secret_id, secret_key)

    class FakeRequest:
        pass

    class FakeClient:
        def __init__(self, cred, region: str):
            captured["client"] = (cred, region)

        def SendSms(self, request):
            captured["request"] = request
            return {
                "SendStatusSet": [{"Code": "Ok", "Message": "成功", "SerialNo": "serial-1"}],
                "RequestId": "request-1",
            }

    monkeypatch.setattr(credential, "Credential", FakeCredential)
    monkeypatch.setattr(models, "SendSmsRequest", FakeRequest)
    monkeypatch.setattr(sms_client, "SmsClient", FakeClient)

    result = await TencentSmsProvider("secret-id", "secret-key", "1400000000").send(
        mobile="13800138000",
        sign_name="Starter 签名",
        template_code="tencent-login",
        params={"code": "123456"},
    )

    request = captured["request"]
    assert result.success is True
    assert result.request_id == "request-1"
    assert request.SmsSdkAppId == "1400000000"
    assert request.SignName == "Starter 签名"
    assert request.TemplateId == "tencent-login"
    assert request.TemplateParamSet == ["123456"]
    assert request.PhoneNumberSet == ["+8613800138000"]


def test_fixed_code_remains_unavailable_in_production(monkeypatch):
    monkeypatch.setattr(settings, "APP_SMS_FIXED_CODE_ENABLED", True)
    monkeypatch.setattr(settings, "APP_SMS_FIXED_CODE", "123456")
    monkeypatch.setattr(settings, "ENVIRONMENT", EnvironmentEnum.PROD)

    assert get_fixed_sms_code() is None


def test_admin_surface_exposes_settings_and_read_only_logs(test_client, auth_headers):
    settings_response = test_client.get("/system/sms/settings", headers=auth_headers)
    assert settings_response.status_code == 200, settings_response.text
    settings_data = settings_response.json()["data"]
    assert settings_data["sms_enabled"] is False
    assert settings_data["active_provider"] in {"aliyun", "tencent"}
    assert "access_key_secret" not in str(settings_data)

    assert test_client.get("/system/sms_log/list", headers=auth_headers, params={"page_no": 1, "page_size": 10}).status_code == 200
    assert test_client.get("/system/sms_channel/list", headers=auth_headers).status_code == 404
    assert test_client.get("/system/sms_template/list", headers=auth_headers).status_code == 404
