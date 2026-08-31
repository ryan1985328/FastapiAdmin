"""Focused tests for the SMS foundation capability."""

from types import SimpleNamespace
from typing import Any

import pytest
from fakeredis import aioredis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.api.v1.module_storage.core.encrypt import decrypt_password
from app.api.v1.module_system.user.model import UserModel
from app.core.base_schema import AuthSchema, BatchSetAvailable
from app.core.exceptions import CustomException
from app.plugin.module_system.sms.constants import SMS_CODE_TTL, secret_digest
from app.plugin.module_system.sms.provider import (
    AliyunSmsProvider,
    MockSmsProvider,
    SmsProviderResult,
)
from app.plugin.module_system.sms.service import SmsService
from app.plugin.module_system.sms_channel.model import SmsChannelModel
from app.plugin.module_system.sms_channel.schema import SmsChannelCreateSchema, SmsChannelOutSchema, SmsChannelUpdateSchema
from app.plugin.module_system.sms_channel.service import SmsChannelService
from app.plugin.module_system.sms_log.model import SmsLogModel
from app.plugin.module_system.sms_log.service import SmsLogService
from app.plugin.module_system.sms_template.model import SmsTemplateModel
from app.plugin.module_system.sms_template.schema import SmsTemplateCreateSchema, SmsTemplateUpdateSchema
from app.plugin.module_system.sms_template.service import SmsTemplateService


class ScriptedFakeRedis(aioredis.FakeRedis):
    """Exercise the service's two Redis scripts when fakeredis lacks EVAL support."""

    async def eval(self, script: str, numkeys: int, *args: Any):  # type: ignore[override]
        keys = args[:numkeys]
        argv = args[numkeys:]
        if numkeys == 2:
            cooldown_key, count_key = keys
            if await self.exists(cooldown_key):
                return -1
            count = int(await self.get(count_key) or 0)
            if count >= int(argv[0]):
                return -2
            if not await self.set(cooldown_key, "1", ex=int(argv[1]), nx=True):
                return -1
            count = await self.incr(count_key)
            if count == 1:
                await self.expire(count_key, int(argv[2]))
            return count

        if numkeys == 1:
            code_key = keys[0]
            value = await self.get(code_key)
            if not value:
                return 0
            expected, separator, attempts_text = value.partition(":")
            if not separator:
                await self.delete(code_key)
                return 0
            if expected == str(argv[0]):
                await self.delete(code_key)
                return 1
            attempts = int(attempts_text or 0) + 1
            if attempts >= int(argv[1]):
                await self.delete(code_key)
                return -2
            ttl = await self.ttl(code_key)
            await self.set(code_key, f"{expected}:{attempts}", ex=ttl if ttl > 0 else None)
            return -1

        raise AssertionError(f"unexpected script key count: {numkeys}")


@pytest.fixture
async def sms_context():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool)
    async with engine.begin() as connection:
        for table in (UserModel.__table__, SmsChannelModel.__table__, SmsTemplateModel.__table__, SmsLogModel.__table__):
            await connection.run_sync(table.create)

    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    redis = ScriptedFakeRedis(decode_responses=True)
    async with session_factory() as db:
        yield db, redis
    await redis.aclose()
    await engine.dispose()


async def seed_sms_config(db: AsyncSession) -> tuple[SmsChannelModel, SmsTemplateModel]:
    channel = SmsChannelModel(
        name="test-aliyun",
        provider="aliyun",
        access_key_id="test-access-key",
        access_key_secret="encrypted-secret",
        sign_name="测试签名",
        status=0,
        is_default=True,
    )
    template = SmsTemplateModel(
        name="注册验证码",
        scene="register_code",
        provider="aliyun",
        provider_template_code="SMS_TEST_CODE",
        param_schema=["code"],
        status=0,
    )
    db.add_all([channel, template])
    await db.flush()
    return channel, template


def success_provider() -> MockSmsProvider:
    return MockSmsProvider(SmsProviderResult(provider="aliyun", success=True, code="OK", message="OK", request_id="rid-1"))


@pytest.mark.asyncio
async def test_send_code_uses_redis_ttl_cooldown_and_consumes_on_success(sms_context):
    db, redis = sms_context
    provider = success_provider()
    await seed_sms_config(db)
    service = SmsService(db, redis, provider_factory=lambda _channel: provider)

    response = await service.send_code(mobile=" 138-0013-8000 ", scene="register_code")

    assert response == {"expires_in": SMS_CODE_TTL, "resend_after": 60}
    call = provider.calls[0]
    assert call["mobile"] == "13800138000"
    code = str(call["params"]["code"])
    assert len(code) == 6 and code.isdigit()

    code_key = service.code_key("register_code", "13800138000")
    stored = await redis.get(code_key)
    assert stored is not None
    assert stored != f"code:{code}"
    assert len(stored.split(":", 1)[0]) == 64
    assert 0 < await redis.ttl(code_key) <= SMS_CODE_TTL
    assert 0 < await redis.ttl(service.cooldown_key("register_code", "13800138000")) <= 60

    with pytest.raises(CustomException) as resend_error:
        await service.send_code(mobile="13800138000", scene="register_code")
    assert resend_error.value.status_code == 429
    assert len(provider.calls) == 1

    assert await service.verify_code(mobile="13800138000", scene="register_code", code=code) is True
    assert await redis.get(code_key) is None
    with pytest.raises(CustomException) as reuse_error:
        await service.verify_code(mobile="13800138000", scene="register_code", code=code)
    assert reuse_error.value.status_code == 422

    logs = (await db.execute(select(SmsLogModel))).scalars().all()
    assert len(logs) == 1
    assert logs[0].status == 0
    assert logs[0].mobile == "13800138000"
    assert not hasattr(logs[0], "code")


@pytest.mark.asyncio
async def test_verify_code_limits_failures_and_hourly_reservation(sms_context):
    db, redis = sms_context
    provider = success_provider()
    await seed_sms_config(db)
    service = SmsService(db, redis, provider_factory=lambda _channel: provider)
    mobile = "13800138001"

    await redis.set(service.code_key("register_code", mobile), f"{secret_digest('code:123456')}:0", ex=SMS_CODE_TTL)
    for _ in range(4):
        with pytest.raises(CustomException) as error:
            await service.verify_code(mobile=mobile, scene="register_code", code="654321")
        assert error.value.status_code == 422
    with pytest.raises(CustomException) as locked_error:
        await service.verify_code(mobile=mobile, scene="register_code", code="654321")
    assert locked_error.value.status_code == 429
    assert await redis.get(service.code_key("register_code", mobile)) is None

    await redis.set(service.count_key("register_code", mobile), "5", ex=3600)
    with pytest.raises(CustomException) as limit_error:
        await service.send_code(mobile=mobile, scene="register_code")
    assert limit_error.value.status_code == 429
    assert not provider.calls


@pytest.mark.asyncio
async def test_provider_failure_cleans_code_but_keeps_audit_log(sms_context):
    db, redis = sms_context
    failure = MockSmsProvider(
        SmsProviderResult(provider="aliyun", success=False, code="isv.MOBILE_NUMBER_ILLEGAL", message="手机号非法", request_id="rid-fail"),
    )
    await seed_sms_config(db)
    service = SmsService(db, redis, provider_factory=lambda _channel: failure)
    mobile = "13800138002"

    with pytest.raises(CustomException) as send_error:
        await service.send_code(mobile=mobile, scene="register_code")
    assert send_error.value.status_code == 502
    assert await redis.get(service.code_key("register_code", mobile)) is None
    assert await redis.get(service.cooldown_key("register_code", mobile)) is None
    assert await redis.get(service.count_key("register_code", mobile)) == "1"

    logs = (await db.execute(select(SmsLogModel))).scalars().all()
    assert len(logs) == 1
    assert logs[0].status == 1
    assert logs[0].provider_code == "isv.MOBILE_NUMBER_ILLEGAL"
    assert not hasattr(logs[0], "code")


@pytest.mark.asyncio
async def test_admin_services_encrypt_secret_enforce_default_and_mask_logs(sms_context):
    db, redis = sms_context
    admin = AuthSchema()
    channels = SmsChannelService(admin, db)
    first = await channels.create(
        SmsChannelCreateSchema(
            name="first",
            provider="aliyun",
            access_key_id="id-1",
            access_key_secret="secret-1",
            sign_name="签名",
            is_default=True,
        )
    )
    first_row = await db.get(SmsChannelModel, first.id)
    assert first_row is not None
    assert first_row.access_key_secret != "secret-1"
    assert decrypt_password(first_row.access_key_secret) == "secret-1"
    await channels.update(first.id, SmsChannelUpdateSchema(sign_name="新签名", access_key_secret=""))
    await db.refresh(first_row)
    assert decrypt_password(first_row.access_key_secret) == "secret-1"

    second = await channels.create(
        SmsChannelCreateSchema(
            name="second",
            provider="aliyun",
            access_key_id="id-2",
            access_key_secret="secret-2",
            sign_name="签名",
        )
    )
    await channels.set_default(second.id)
    await db.refresh(first_row)
    second_row = await db.get(SmsChannelModel, second.id)
    assert second_row is not None
    assert first_row.is_default is False
    assert second_row.is_default is True

    await channels.set_available(BatchSetAvailable(ids=[second.id], status=1))
    await db.refresh(second_row)
    assert second_row.status == 1
    assert second_row.is_default is False
    with pytest.raises(CustomException) as disabled_error:
        await channels.set_default(second.id)
    assert disabled_error.value.status_code == 422

    templates = SmsTemplateService(admin, db)
    created_template = await templates.create(
        SmsTemplateCreateSchema(
            name="template-one",
            scene="register_code",
            provider="aliyun",
            provider_template_code="SMS_ONE",
            param_schema=["code"],
        )
    )
    updated_template = await templates.update(created_template.id, SmsTemplateUpdateSchema(name="template-one-updated"))
    assert updated_template.name == "template-one-updated"
    with pytest.raises(CustomException) as template_error:
        await templates.create(
            SmsTemplateCreateSchema(
                name="template-duplicate-scene",
                scene="register_code",
                provider="aliyun",
                provider_template_code="SMS_TWO",
                param_schema=["code"],
            )
        )
    assert template_error.value.status_code == 409

    provider = success_provider()
    await db.execute(
        SmsChannelModel.__table__.update().values(status=0, is_default=True).where(SmsChannelModel.id == second.id),
    )
    await db.flush()
    service = SmsService(db, redis, admin, provider_factory=lambda _channel: provider)
    await service.test_send(mobile="13800138003", scene="register_code", params={"code": "123456"})
    log_page = await SmsLogService(admin, db).page(1, 10)
    assert log_page.items[0].mobile == "138****8003"
    log_detail = await SmsLogService(admin, db).detail(log_page.items[0].id)
    assert log_detail.mobile == "13800138003"


def test_sms_admin_route_surface_is_read_only_for_logs(test_client, auth_headers):
    response = test_client.get("/system/sms_log/list", headers=auth_headers, params={"page_no": 1, "page_size": 10})
    assert response.status_code == 200, response.text
    assert test_client.post("/system/sms_log/create", headers=auth_headers, json={}).status_code == 404
    assert test_client.request("DELETE", "/system/sms_log/delete", headers=auth_headers, json=[1]).status_code == 404
    invalid_scene = test_client.post("/app/sms/send-code", json={"mobile": "13800138000", "scene": "unsupported"})
    assert invalid_scene.status_code == 422
    without_channel = test_client.post("/app/sms/send-code", json={"mobile": "13800138000", "scene": "register_code"})
    assert without_channel.status_code == 503


def test_sms_write_schema_accepts_secret_but_output_does_not():
    create = SmsChannelCreateSchema(
        name="channel",
        provider="aliyun",
        access_key_id="id",
        access_key_secret="secret-value",
        sign_name="签名",
    )
    assert create.access_key_secret == "secret-value"

    output = SmsChannelOutSchema(
        id=1,
        name="channel",
        provider="aliyun",
        access_key_id="id",
        sign_name="签名",
        status=0,
        is_default=False,
        has_secret=True,
    )
    assert "access_key_secret" not in output.model_dump()

    template = SmsTemplateCreateSchema(
        name="template",
        scene="register_code",
        provider="aliyun",
        provider_template_code="SMS_TEST_CODE",
        param_schema='["code"]',
    )
    assert template.param_schema == ["code"]


@pytest.mark.asyncio
async def test_aliyun_adapter_builds_v2_request_without_network(monkeypatch):
    from alibabacloud_dysmsapi20170525 import client as client_module
    from alibabacloud_dysmsapi20170525 import models as sms_models
    from alibabacloud_tea_openapi import models as open_api_models
    from alibabacloud_tea_util import models as util_models

    captured: dict[str, Any] = {}

    class FakeConfig:
        def __init__(self, **kwargs):
            captured["config"] = kwargs

    class FakeRequest:
        def __init__(self, **kwargs):
            captured["request"] = kwargs

    class FakeClient:
        def __init__(self, config):
            captured["client_config"] = config

        async def send_sms_with_options_async(self, request, runtime_options):
            captured["runtime_options"] = runtime_options
            return SimpleNamespace(body=SimpleNamespace(code="OK", message="OK", request_id="aliyun-rid"))

    class FakeRuntimeOptions:
        pass

    monkeypatch.setattr(open_api_models, "Config", FakeConfig)
    monkeypatch.setattr(sms_models, "SendSmsRequest", FakeRequest)
    monkeypatch.setattr(client_module, "Client", FakeClient)
    monkeypatch.setattr(util_models, "RuntimeOptions", FakeRuntimeOptions)

    result = await AliyunSmsProvider("access-id", "access-secret").send(
        mobile="13800138000",
        sign_name="测试签名",
        template_code="SMS_TEST_CODE",
        params={"code": "123456"},
    )

    assert result == SmsProviderResult(provider="aliyun", success=True, code="OK", message="OK", request_id="aliyun-rid")
    assert captured["config"] == {
        "access_key_id": "access-id",
        "access_key_secret": "access-secret",
        "endpoint": "dysmsapi.aliyuncs.com",
    }
    assert captured["request"] == {
        "phone_numbers": "13800138000",
        "sign_name": "测试签名",
        "template_code": "SMS_TEST_CODE",
        "template_param": '{"code":"123456"}',
    }
    assert isinstance(captured["runtime_options"], FakeRuntimeOptions)

    missing = await AliyunSmsProvider("", "").send(
        mobile="13800138000",
        sign_name="测试签名",
        template_code="SMS_TEST_CODE",
        params={"code": "123456"},
    )
    assert missing == SmsProviderResult(
        provider="aliyun",
        success=False,
        code="CONFIG_MISSING",
        message="阿里云短信渠道未配置完整的 AccessKey",
    )
