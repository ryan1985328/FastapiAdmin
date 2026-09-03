"""Focused regression tests for the V1.x application-local time contract."""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest
from fakeredis import aioredis
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.api.v1.module_system.user.model import UserModel
from app.common.constant import DATETIME_DISPLAY_FMT
from app.common.enums import EnvironmentEnum
from app.config.setting import Settings, settings
from app.core.base_model import ModelMixin
from app.plugin.module_app.user.model import AppUserModel
from app.plugin.module_system.sms.provider import MockSmsProvider, SmsProviderResult
from app.plugin.module_system.sms.service import SmsService
from app.plugin.module_system.sms_channel.model import SmsChannelModel
from app.plugin.module_system.sms_log.model import SmsLogModel
from app.plugin.module_system.sms_template.model import SmsTemplateModel
from app.utils.time_util import application_now


@pytest.fixture
async def sms_context():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool)
    async with engine.begin() as connection:
        for table in (
            UserModel.__table__,
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


def response_data(response):
    body = response.json()
    assert body.get("success") is True, body
    return body["data"]


def parse_display_time(value: str) -> datetime:
    return datetime.strptime(value, DATETIME_DISPLAY_FMT)


def test_application_now_uses_configured_timezone_not_host_timezone(monkeypatch):
    for timezone_name in ("UTC", "Asia/Shanghai"):
        monkeypatch.setattr(settings, "APPLICATION_TIMEZONE", timezone_name)
        actual = application_now()
        expected = datetime.now(ZoneInfo(timezone_name)).replace(tzinfo=None)

        assert actual.tzinfo is None
        assert abs((actual - expected).total_seconds()) < 2


def test_model_mixin_defaults_use_naive_application_local_values():
    columns = AppUserModel.__table__.c
    values = [
        columns.created_time.default.arg(None),
        columns.updated_time.default.arg(None),
        columns.updated_time.onupdate.arg(None),
    ]
    now = application_now()

    assert all(value.tzinfo is None for value in values)
    assert all(abs((value - now).total_seconds()) < 2 for value in values)
    assert ModelMixin.created_time is not None


def test_invalid_application_timezone_is_rejected():
    with pytest.raises(ValidationError, match="APPLICATION_TIMEZONE"):
        Settings(ENVIRONMENT=EnvironmentEnum.DEV, APPLICATION_TIMEZONE="Invalid/Timezone")


def test_app_user_registration_and_admin_api_share_application_local_time(
    test_client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    username = f"timezone_{uuid4().hex[:12]}"
    before = application_now() - timedelta(seconds=2)
    response = test_client.post(
        "/app/auth/register",
        json={"username": username, "password": "Timezone123!", "nickname": "Timezone User"},
    )
    after = application_now() + timedelta(seconds=2)

    assert response.status_code == 200, response.text
    registered = response_data(response)
    created_time = parse_display_time(registered["created_time"])
    assert before <= created_time <= after

    listed = test_client.get(
        "/system/app_user/list",
        headers=auth_headers,
        params={"page_no": 1, "page_size": 100, "keyword": username},
    )
    assert listed.status_code == 200, listed.text
    items = response_data(listed)["items"]
    admin_item = next(item for item in items if item["id"] == registered["id"])
    assert admin_item["created_time"] == registered["created_time"]
    assert admin_item["updated_time"] == registered["updated_time"]


def test_admin_login_updates_last_login_in_application_local_time(
    test_client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    before = application_now() - timedelta(seconds=2)
    with (
        patch("app.api.v1.module_system.auth.service._write_login_log", new=AsyncMock(return_value=None)),
        patch("app.core.router_class._write_operation_log_async", new=AsyncMock(return_value=None)),
    ):
        login = test_client.post(
            "/system/auth/login",
            data={"username": "admin", "password": "admin123"},
        )
    after = application_now() + timedelta(seconds=2)

    assert login.status_code == 200, login.text
    listed = test_client.get(
        "/system/user/list",
        headers=auth_headers,
        params={"page_no": 1, "page_size": 100, "username": "admin"},
    )
    assert listed.status_code == 200, listed.text
    admin = next(item for item in response_data(listed)["items"] if item["username"] == "admin")
    last_login = parse_display_time(admin["last_login"])
    assert before <= last_login <= after


@pytest.mark.asyncio
async def test_sms_persisted_sent_at_uses_application_local_time(sms_context):
    db, redis = sms_context
    template = SmsTemplateModel(
        name="register_code",
        scene="register_code",
        provider="aliyun",
        provider_template_code="aliyun-register",
        param_schema=["code"],
        status=0,
    )
    db.add(template)
    await db.flush()

    service = SmsService(
        db,
        redis,
        provider_factory=lambda _channel: MockSmsProvider(),
    )
    before = application_now() - timedelta(seconds=2)
    log = await service._write_log(
        mobile="13800138000",
        scene="register_code",
        template=template,
        result=SmsProviderResult(provider="aliyun", success=True, code="OK", message="ok"),
    )
    after = application_now() + timedelta(seconds=2)

    assert log.sent_at is not None
    assert log.sent_at.tzinfo is None
    assert before <= log.sent_at <= after
    stored = (await db.execute(select(SmsLogModel).where(SmsLogModel.id == log.id))).scalar_one()
    assert stored.sent_at == log.sent_at
