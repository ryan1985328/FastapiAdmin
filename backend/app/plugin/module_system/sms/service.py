"""Provider-neutral SMS sending and verification-code lifecycle."""

import secrets
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from typing import Any

from redis.asyncio.client import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.module_storage.core.encrypt import decrypt_password
from app.core.base_schema import AuthSchema
from app.core.exceptions import CustomException

from ..sms_channel.model import SmsChannelModel
from ..sms_log.model import SmsLogModel
from ..sms_template.model import SmsTemplateModel
from .constants import (
    SMS_CODE_TTL,
    SMS_HOURLY_LIMIT,
    SMS_MAX_VERIFY_FAILURES,
    SMS_PROVIDER_ALIYUN,
    SMS_RESEND_INTERVAL,
    get_fixed_sms_code,
    mobile_hash,
    normalize_mobile,
    secret_digest,
    validate_scene,
)
from .provider import SmsProvider, SmsProviderResult, create_provider
from .settings_service import read_sms_runtime_config

ProviderFactory = Callable[[SmsChannelModel], SmsProvider]

_RESERVE_SCRIPT = """
if redis.call('exists', KEYS[1]) == 1 then
    return -1
end
local count = tonumber(redis.call('get', KEYS[2]) or '0')
if count >= tonumber(ARGV[1]) then
    return -2
end
local reserved = redis.call('set', KEYS[1], '1', 'EX', ARGV[2], 'NX')
if not reserved then
    return -1
end
count = redis.call('incr', KEYS[2])
if count == 1 then
    redis.call('expire', KEYS[2], ARGV[3])
end
return count
"""

_VERIFY_SCRIPT = """
local value = redis.call('get', KEYS[1])
if not value then
    return 0
end
local separator = string.find(value, ':')
if not separator then
    redis.call('del', KEYS[1])
    return 0
end
local expected = string.sub(value, 1, separator - 1)
local attempts = tonumber(string.sub(value, separator + 1)) or 0
if expected == ARGV[1] then
    redis.call('del', KEYS[1])
    return 1
end
attempts = attempts + 1
if attempts >= tonumber(ARGV[2]) then
    redis.call('del', KEYS[1])
    return -2
end
redis.call('set', KEYS[1], expected .. ':' .. attempts, 'KEEPTTL')
return -1
"""


class SmsService:
    """Reusable SMS capability; business modules only provide scene + params."""

    def __init__(
        self,
        db: AsyncSession,
        redis: Redis,
        auth: AuthSchema | None = None,
        provider_factory: ProviderFactory | None = None,
    ) -> None:
        self.db = db
        self.redis = redis
        self.auth = auth or AuthSchema()
        self.provider_factory = provider_factory or self._default_provider_factory

    @staticmethod
    def code_key(scene: str, mobile: str) -> str:
        return f"sms:code:{scene}:{mobile_hash(mobile)}"

    @staticmethod
    def cooldown_key(scene: str, mobile: str) -> str:
        return f"sms:cooldown:{scene}:{mobile_hash(mobile)}"

    @staticmethod
    def count_key(scene: str, mobile: str) -> str:
        return f"sms:count:{scene}:{mobile_hash(mobile)}:hour"

    async def _resolve_channel(self, channel_id: int | None = None, provider: str | None = None) -> SmsChannelModel:
        base = [SmsChannelModel.is_deleted.is_(False)]
        if channel_id is not None:
            result = await self.db.execute(select(SmsChannelModel).where(SmsChannelModel.id == channel_id, *base))
            channel = result.scalars().first()
            if not channel:
                raise CustomException(msg="短信渠道不存在", status_code=404)
            if provider and channel.provider != provider:
                raise CustomException(msg="短信渠道与当前供应商不一致", status_code=422)
            if channel.status == 1:
                raise CustomException(msg="当前短信供应商已停用", status_code=503)
            return channel

        if provider:
            result = await self.db.execute(
                select(SmsChannelModel).where(
                    SmsChannelModel.provider == provider,
                    SmsChannelModel.is_deleted.is_(False),
                ).order_by(SmsChannelModel.id.asc()),
            )
            channels = list(result.scalars().all())
            if len(channels) > 1:
                raise CustomException(msg="当前短信供应商存在多个配置，已停止短信发送", status_code=500)
            channel = channels[0] if channels else None
            if not channel:
                if provider == SMS_PROVIDER_ALIYUN:
                    raise CustomException(msg="当前短信供应商（阿里云）未配置", status_code=503)
                raise CustomException(msg="当前短信供应商（腾讯云）未配置", status_code=503)
            if channel.status == 1:
                display = "阿里云" if provider == SMS_PROVIDER_ALIYUN else "腾讯云"
                raise CustomException(msg=f"当前短信供应商（{display}）已停用", status_code=503)
            return channel

        result = await self.db.execute(
            select(SmsChannelModel).where(
                SmsChannelModel.status == 0,
                SmsChannelModel.is_deleted.is_(False),
            ).order_by(SmsChannelModel.is_default.desc(), SmsChannelModel.id.asc()),
        )
        channels = list(result.scalars().all())
        channel = channels[0] if channels else None
        if not channel:
            raise CustomException(msg="未配置可用的短信渠道", status_code=503)
        return channel

    async def _resolve_template(self, scene: str, provider: str) -> SmsTemplateModel:
        result = await self.db.execute(
            select(SmsTemplateModel).where(
                SmsTemplateModel.scene == scene,
                SmsTemplateModel.provider == provider,
                SmsTemplateModel.status == 0,
                SmsTemplateModel.is_deleted.is_(False),
            ),
        )
        templates = list(result.scalars().all())
        if len(templates) > 1:
            raise CustomException(msg=f"短信模板配置重复: {scene}", status_code=500)
        template = templates[0] if templates else None
        if not template:
            raise CustomException(msg=f"未配置启用的短信模板: {scene}", status_code=503)
        if not str(template.provider_template_code or "").strip():
            raise CustomException(msg=f"短信模板编码未配置: {scene}", status_code=503)
        return template

    @staticmethod
    def _validate_params(template: SmsTemplateModel, params: Mapping[str, Any]) -> dict[str, Any]:
        expected = template.param_schema
        if not isinstance(expected, list) or any(not isinstance(item, str) for item in expected):
            raise CustomException(msg="短信模板参数定义无效", status_code=500)
        actual = dict(params)
        expected_set = set(expected)
        actual_set = set(actual)
        missing = expected_set - actual_set
        extra = actual_set - expected_set
        if missing:
            raise CustomException(msg=f"短信模板缺少参数: {', '.join(sorted(missing))}", status_code=422)
        if extra:
            raise CustomException(msg=f"短信模板包含未声明参数: {', '.join(sorted(extra))}", status_code=422)
        return actual

    @staticmethod
    def _default_provider_factory(channel: SmsChannelModel) -> SmsProvider:
        return create_provider(
            channel.provider,
            channel.access_key_id,
            decrypt_password(channel.access_key_secret),
            sms_sdk_app_id=channel.sms_sdk_app_id,
        )

    async def _call_provider(
        self,
        channel: SmsChannelModel,
        *,
        mobile: str,
        template: SmsTemplateModel,
        params: dict[str, Any],
    ) -> SmsProviderResult:
        try:
            provider = self.provider_factory(channel)
            result = await provider.send(
                mobile=mobile,
                sign_name=channel.sign_name,
                template_code=template.provider_template_code,
                params=params,
            )
            if result.provider != channel.provider:
                return SmsProviderResult(
                    provider=channel.provider,
                    success=False,
                    code="PROVIDER_RESULT_INVALID",
                    message="短信供应商返回结果无效",
                )
            return result
        except CustomException as exc:
            return SmsProviderResult(
                provider=channel.provider,
                success=False,
                code="CONFIG_INVALID",
                message=exc.msg,
            )
        except Exception:
            return SmsProviderResult(
                provider=channel.provider,
                success=False,
                code="PROVIDER_EXCEPTION",
                message="短信供应商调用异常",
            )

    async def _write_log(self, mobile: str, scene: str, template: SmsTemplateModel, result: SmsProviderResult) -> SmsLogModel:
        user_id = self.auth.user.id if self.auth.user and self.auth.user.id > 0 else None
        log = SmsLogModel(
            mobile=mobile,
            scene=scene,
            template_code=template.provider_template_code,
            provider=result.provider,
            status=0 if result.success else 1,
            provider_request_id=result.request_id,
            provider_code=result.code,
            provider_message=result.message,
            sent_at=datetime.now(UTC),
            created_id=user_id,
            updated_id=user_id,
        )
        self.db.add(log)
        await self.db.flush()
        return log

    async def _send_resolved(
        self,
        channel: SmsChannelModel,
        template: SmsTemplateModel,
        mobile: str,
        scene: str,
        params: dict[str, Any],
    ) -> SmsProviderResult:
        result = await self._call_provider(channel, mobile=mobile, template=template, params=params)
        await self._write_log(mobile, scene, template, result)
        return result

    async def test_send(
        self,
        *,
        mobile: str,
        scene: str,
        params: Mapping[str, Any],
        channel_id: int | None = None,
        provider: str | None = None,
    ) -> SmsProviderResult:
        normalized_mobile = normalize_mobile(mobile)
        normalized_scene = validate_scene(scene)
        runtime = await read_sms_runtime_config(self.db)
        if not runtime.sms_enabled:
            raise CustomException(msg="短信服务未启用，请先在短信配置中开启", status_code=503)
        selected_provider = provider or runtime.active_provider
        channel = await self._resolve_channel(channel_id=channel_id, provider=selected_provider)
        template = await self._resolve_template(normalized_scene, channel.provider)
        normalized_params = self._validate_params(template, params)
        return await self._send_resolved(channel, template, normalized_mobile, normalized_scene, normalized_params)

    async def _reserve(self, scene: str, mobile: str) -> None:
        result = await self.redis.eval(
            _RESERVE_SCRIPT,
            2,
            self.cooldown_key(scene, mobile),
            self.count_key(scene, mobile),
            SMS_HOURLY_LIMIT,
            SMS_RESEND_INTERVAL,
            3600,
        )
        if int(result) == -1:
            raise CustomException(msg="验证码发送过于频繁，请稍后再试", status_code=429)
        if int(result) == -2:
            raise CustomException(msg="该手机号本小时验证码发送次数已达上限", status_code=429)

    async def _store_code(self, scene: str, mobile: str, code: str) -> None:
        try:
            await self.redis.set(
                name=self.code_key(scene, mobile),
                value=f"{secret_digest(f'code:{code}')}:0",
                ex=SMS_CODE_TTL,
            )
        except Exception as exc:
            await self.redis.delete(self.cooldown_key(scene, mobile))
            raise CustomException(msg="验证码状态保存失败", status_code=503) from exc

    async def send_code(self, *, mobile: str, scene: str) -> dict[str, int | str]:
        normalized_mobile = normalize_mobile(mobile)
        normalized_scene = validate_scene(scene)
        fixed_code = get_fixed_sms_code()
        if fixed_code is not None:
            await self._reserve(normalized_scene, normalized_mobile)
            await self._store_code(normalized_scene, normalized_mobile, fixed_code)
            return {
                "expires_in": SMS_CODE_TTL,
                "resend_after": SMS_RESEND_INTERVAL,
                "debug_code": fixed_code,
            }

        runtime = await read_sms_runtime_config(self.db)
        if not runtime.sms_enabled:
            raise CustomException(msg="短信服务未启用，请先在短信配置中开启", status_code=503)
        channel = await self._resolve_channel(provider=runtime.active_provider)
        template = await self._resolve_template(normalized_scene, channel.provider)
        code = f"{secrets.randbelow(1_000_000):06d}"
        params = self._validate_params(template, {"code": code})

        await self._reserve(normalized_scene, normalized_mobile)
        await self._store_code(normalized_scene, normalized_mobile, code)
        try:
            result = await self._send_resolved(channel, template, normalized_mobile, normalized_scene, params)
        except Exception:
            await self.redis.delete(self.code_key(normalized_scene, normalized_mobile), self.cooldown_key(normalized_scene, normalized_mobile))
            raise
        if not result.success:
            await self.redis.delete(self.code_key(normalized_scene, normalized_mobile), self.cooldown_key(normalized_scene, normalized_mobile))
            raise CustomException(msg=f"短信发送失败: {result.message or result.code or '供应商返回失败'}", status_code=502)
        return {"expires_in": SMS_CODE_TTL, "resend_after": SMS_RESEND_INTERVAL}

    async def verify_code(self, *, mobile: str, scene: str, code: str) -> bool:
        normalized_mobile = normalize_mobile(mobile)
        normalized_scene = validate_scene(scene)
        if not str(code or "").isdigit() or len(str(code)) != 6:
            raise CustomException(msg="验证码错误", status_code=422)
        result = await self.redis.eval(
            _VERIFY_SCRIPT,
            1,
            self.code_key(normalized_scene, normalized_mobile),
            secret_digest(f"code:{code}"),
            SMS_MAX_VERIFY_FAILURES,
        )
        result = int(result)
        if result == 1:
            return True
        if result == -2:
            raise CustomException(msg="验证码错误次数过多，请重新获取", status_code=429)
        if result == -1:
            raise CustomException(msg="验证码错误", status_code=422)
        raise CustomException(msg="验证码不存在或已过期", status_code=422)


__all__ = ["SmsService"]
