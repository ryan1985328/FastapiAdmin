"""Persistence and validation for the fixed SMS settings page."""

import json
from dataclasses import dataclass
from typing import Final

from redis.asyncio.client import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.module_storage.core.encrypt import encrypt_password
from app.api.v1.module_system.params.model import ParamsModel
from app.api.v1.module_system.params.schema import ParamsOutSchema
from app.common.enums import RedisInitKeyConfig, SysParamKey
from app.core.base_schema import AuthSchema
from app.core.exceptions import CustomException
from app.core.redis_crud import RedisCURD

from ..sms_channel.model import SmsChannelModel
from ..sms_template.model import SmsTemplateModel
from .constants import SMS_PROVIDER_ALIYUN, SMS_PROVIDER_TENCENT, SMS_PROVIDERS, SMS_SCENES
from .settings_schema import (
    SmsProviderSettingsOutSchema,
    SmsProviderSettingsUpdateSchema,
    SmsSettingsOutSchema,
    SmsSettingsUpdateSchema,
    SmsTemplateSettingsOutSchema,
)

_PROVIDER_NAMES: Final[dict[str, str]] = {
    SMS_PROVIDER_ALIYUN: "阿里云",
    SMS_PROVIDER_TENCENT: "腾讯云",
}
_PROVIDER_KEYS: Final[tuple[str, str]] = (SMS_PROVIDER_ALIYUN, SMS_PROVIDER_TENCENT)
_SCENE_NAMES: Final[dict[str, str]] = {
    "register_code": "注册验证码",
    "login_code": "登录验证码",
    "reset_password_code": "重置密码验证码",
}
_CHANNEL_NAMES: Final[dict[str, str]] = {
    SMS_PROVIDER_ALIYUN: "Starter 阿里云短信",
    SMS_PROVIDER_TENCENT: "Starter 腾讯云短信",
}
_ENABLED_VALUES: Final[frozenset[str]] = frozenset({"1", "true", "on", "yes", "enabled"})
_DISABLED_VALUES: Final[frozenset[str]] = frozenset({"0", "false", "off", "no", "disabled"})
_SMS_PARAM_KEYS: Final[tuple[str, str]] = (SysParamKey.SMS_ENABLED.value, SysParamKey.SMS_ACTIVE_PROVIDER.value)


@dataclass(frozen=True, slots=True)
class SmsRuntimeConfig:
    sms_enabled: bool
    active_provider: str


def _param_value(rows: list[ParamsModel], key: str) -> str | None:
    matching = [row for row in rows if row.config_key == key and row.status == 0]
    if len(matching) > 1:
        raise CustomException(msg=f"短信系统参数重复: {key}", status_code=500)
    return matching[0].config_value if matching else None


async def read_sms_runtime_config(db: AsyncSession) -> SmsRuntimeConfig:
    """Read global/active-provider settings with safe defaults.

    Missing rows mean global SMS is off.  This keeps an installation fail-closed
    until the new settings migration or the settings page establishes a value.
    """

    result = await db.execute(
        select(ParamsModel).where(
            ParamsModel.config_key.in_(_SMS_PARAM_KEYS),
            ParamsModel.is_deleted.is_(False),
        ),
    )
    rows = list(result.scalars().all())
    enabled_raw = (_param_value(rows, SysParamKey.SMS_ENABLED.value) or "off").strip().lower()
    if enabled_raw in _ENABLED_VALUES:
        sms_enabled = True
    elif enabled_raw in _DISABLED_VALUES:
        sms_enabled = False
    else:
        raise CustomException(msg="短信全局启用配置无效，请使用 on 或 off", status_code=500)

    active_provider = (_param_value(rows, SysParamKey.SMS_ACTIVE_PROVIDER.value) or SMS_PROVIDER_ALIYUN).strip().lower()
    if active_provider not in SMS_PROVIDERS:
        raise CustomException(msg="短信当前供应商配置无效，请选择阿里云或腾讯云", status_code=500)
    return SmsRuntimeConfig(sms_enabled=sms_enabled, active_provider=active_provider)


class SmsSettingsService:
    """Manage one deterministic row per built-in provider and fixed scene."""

    def __init__(self, auth: AuthSchema, db: AsyncSession) -> None:
        self.auth = auth
        self.db = db

    async def _channels(self) -> dict[str, SmsChannelModel | None]:
        result = await self.db.execute(
            select(SmsChannelModel).where(
                SmsChannelModel.provider.in_(_PROVIDER_KEYS),
                SmsChannelModel.is_deleted.is_(False),
            ).order_by(SmsChannelModel.id.asc()),
        )
        rows = list(result.scalars().all())
        channels: dict[str, SmsChannelModel | None] = {}
        for provider in _PROVIDER_KEYS:
            matching = [row for row in rows if row.provider == provider]
            if len(matching) > 1:
                raise CustomException(msg=f"{_PROVIDER_NAMES[provider]}存在多个活动配置，已停止短信发送", status_code=500)
            channels[provider] = matching[0] if matching else None
        return channels

    async def _templates(self) -> dict[tuple[str, str], SmsTemplateModel | None]:
        result = await self.db.execute(
            select(SmsTemplateModel).where(
                SmsTemplateModel.provider.in_(_PROVIDER_KEYS),
                SmsTemplateModel.scene.in_(SMS_SCENES),
                SmsTemplateModel.is_deleted.is_(False),
            ).order_by(SmsTemplateModel.id.asc()),
        )
        rows = list(result.scalars().all())
        templates: dict[tuple[str, str], SmsTemplateModel | None] = {}
        for provider in _PROVIDER_KEYS:
            for scene in sorted(SMS_SCENES):
                matching = [row for row in rows if row.provider == provider and row.scene == scene]
                if len(matching) > 1:
                    raise CustomException(
                        msg=f"{_PROVIDER_NAMES[provider]}的{_SCENE_NAMES[scene]}存在多个配置，已停止短信发送",
                        status_code=500,
                    )
                templates[(provider, scene)] = matching[0] if matching else None
        return templates

    @staticmethod
    def _template_out(templates: dict[tuple[str, str], SmsTemplateModel | None], provider: str) -> SmsTemplateSettingsOutSchema:
        values = {
            scene: (templates[(provider, scene)].provider_template_code if templates[(provider, scene)] else "")
            for scene in _SCENE_NAMES
        }
        return SmsTemplateSettingsOutSchema(**values)

    @staticmethod
    def _provider_out(
        provider: str,
        channel: SmsChannelModel | None,
        templates: dict[tuple[str, str], SmsTemplateModel | None],
    ) -> SmsProviderSettingsOutSchema:
        return SmsProviderSettingsOutSchema(
            enabled=bool(channel and channel.status == 0),
            access_key_id=channel.access_key_id if channel else "",
            has_secret=bool(channel and channel.access_key_secret),
            sms_sdk_app_id=channel.sms_sdk_app_id if channel else None,
            sign_name=channel.sign_name if channel else "",
            templates=SmsSettingsService._template_out(templates, provider),
        )

    async def get(self) -> SmsSettingsOutSchema:
        runtime = await read_sms_runtime_config(self.db)
        channels = await self._channels()
        templates = await self._templates()
        return SmsSettingsOutSchema(
            sms_enabled=runtime.sms_enabled,
            active_provider=runtime.active_provider,
            aliyun=self._provider_out(SMS_PROVIDER_ALIYUN, channels[SMS_PROVIDER_ALIYUN], templates),
            tencent=self._provider_out(SMS_PROVIDER_TENCENT, channels[SMS_PROVIDER_TENCENT], templates),
        )

    @staticmethod
    def _user_id(auth: AuthSchema) -> int | None:
        return auth.user.id if auth.user and auth.user.id and auth.user.id > 0 else None

    @staticmethod
    def _effective_secret(config: SmsProviderSettingsUpdateSchema, channel: SmsChannelModel | None) -> str:
        if config.access_key_secret:
            return config.access_key_secret
        return channel.access_key_secret if channel else ""

    @classmethod
    def _validate_provider(
        cls,
        provider: str,
        config: SmsProviderSettingsUpdateSchema,
        channel: SmsChannelModel | None,
        *,
        required: bool,
    ) -> None:
        display = _PROVIDER_NAMES[provider]
        if required and not config.enabled:
            raise CustomException(msg=f"短信已开启，但当前供应商（{display}）未启用", status_code=422)
        if not config.enabled:
            return

        missing: list[str] = []
        if not config.access_key_id:
            missing.append("AccessKey ID/SecretId")
        if not cls._effective_secret(config, channel):
            missing.append("AccessKey Secret/SecretKey")
        if not config.sign_name:
            missing.append("短信签名")
        if provider == SMS_PROVIDER_TENCENT and not config.sms_sdk_app_id:
            missing.append("短信 SDK App ID")
        template_values = config.templates
        for scene in _SCENE_NAMES:
            if not getattr(template_values, scene):
                missing.append(_SCENE_NAMES[scene] + "模板")
        if missing:
            raise CustomException(msg=f"{display}配置不完整：缺少" + "、".join(missing), status_code=422)

    async def _params_by_key(self) -> dict[str, ParamsModel | None]:
        result = await self.db.execute(
            select(ParamsModel).where(
                ParamsModel.config_key.in_(_SMS_PARAM_KEYS),
                ParamsModel.is_deleted.is_(False),
            ).order_by(ParamsModel.id.asc()),
        )
        rows = list(result.scalars().all())
        values: dict[str, ParamsModel | None] = {}
        for key in _SMS_PARAM_KEYS:
            matching = [row for row in rows if row.config_key == key]
            if len(matching) > 1:
                raise CustomException(msg=f"短信系统参数重复: {key}", status_code=500)
            values[key] = matching[0] if matching else None
        return values

    async def _upsert_param(
        self,
        params: dict[str, ParamsModel | None],
        *,
        key: str,
        name: str,
        value: str,
        description: str,
    ) -> ParamsModel:
        obj = params[key]
        if obj is None:
            obj = ParamsModel(
                config_name=name,
                config_key=key,
                config_value=value,
                config_type=True,
                status=0,
                description=description,
            )
            self.db.add(obj)
        else:
            obj.config_name = name
            obj.config_value = value
            obj.config_type = True
            obj.status = 0
            obj.description = description
        return obj

    async def _sync_param_cache(self, redis: Redis, obj: ParamsModel) -> None:
        payload = ParamsOutSchema.model_validate(obj).model_dump(mode="json")
        key = f"{RedisInitKeyConfig.SYSTEM_CONFIG.key}:{obj.config_key}"
        if not await RedisCURD(redis).set(key=key, value=json.dumps(payload, ensure_ascii=False), expire=None):
            raise CustomException(msg="短信配置已保存，但同步系统配置缓存失败", status_code=503)

    async def update(self, data: SmsSettingsUpdateSchema, redis: Redis) -> SmsSettingsOutSchema:
        channels = await self._channels()
        required_provider = data.active_provider if data.sms_enabled else None
        provider_configs = {SMS_PROVIDER_ALIYUN: data.aliyun, SMS_PROVIDER_TENCENT: data.tencent}
        for provider, config in provider_configs.items():
            self._validate_provider(
                provider,
                config,
                channels[provider],
                required=provider == required_provider,
            )

        user_id = self._user_id(self.auth)
        for provider, config in provider_configs.items():
            channel = channels[provider]
            if channel is None:
                channel = SmsChannelModel(
                    name=_CHANNEL_NAMES[provider],
                    provider=provider,
                    access_key_id="",
                    access_key_secret="",
                    sms_sdk_app_id=None,
                    sign_name="",
                    status=1,
                    is_default=False,
                    created_id=user_id,
                    updated_id=user_id,
                )
                self.db.add(channel)
                channels[provider] = channel
            channel.name = _CHANNEL_NAMES[provider]
            channel.access_key_id = config.access_key_id
            if config.access_key_secret:
                channel.access_key_secret = encrypt_password(config.access_key_secret)
            channel.sms_sdk_app_id = config.sms_sdk_app_id
            channel.sign_name = config.sign_name
            channel.status = 0 if config.enabled else 1
            channel.is_default = provider == data.active_provider and config.enabled
            channel.updated_id = user_id

        for provider, config in provider_configs.items():
            for scene in _SCENE_NAMES:
                template_result = await self.db.execute(
                    select(SmsTemplateModel).where(
                        SmsTemplateModel.provider == provider,
                        SmsTemplateModel.scene == scene,
                        SmsTemplateModel.is_deleted.is_(False),
                    ).order_by(SmsTemplateModel.id.asc()),
                )
                matches = list(template_result.scalars().all())
                if len(matches) > 1:
                    raise CustomException(
                        msg=f"{_PROVIDER_NAMES[provider]}的{_SCENE_NAMES[scene]}存在多个配置，已停止保存",
                        status_code=500,
                    )
                template = matches[0] if matches else None
                if template is None:
                    template = SmsTemplateModel(
                        name=_SCENE_NAMES[scene],
                        scene=scene,
                        provider=provider,
                        provider_template_code="",
                        param_schema=["code"],
                        status=1,
                        created_id=user_id,
                        updated_id=user_id,
                    )
                    self.db.add(template)
                template.name = _SCENE_NAMES[scene]
                template.provider_template_code = getattr(config.templates, scene)
                template.param_schema = ["code"]
                template.status = 0
                template.updated_id = user_id

        params = await self._params_by_key()
        param_objects = [
            await self._upsert_param(
                params,
                key=SysParamKey.SMS_ENABLED.value,
                name="短信服务启用",
                value="on" if data.sms_enabled else "off",
                description="是否允许 App 认证流程调用真实短信供应商；开发固定验证码仍遵循环境保护规则",
            ),
            await self._upsert_param(
                params,
                key=SysParamKey.SMS_ACTIVE_PROVIDER.value,
                name="短信当前供应商",
                value=data.active_provider,
                description="App 认证短信使用的内置供应商（aliyun 或 tencent）",
            ),
        ]
        await self.db.flush()
        for obj in param_objects:
            await self._sync_param_cache(redis, obj)
        return await self.get()


__all__ = ["SmsRuntimeConfig", "SmsSettingsService", "read_sms_runtime_config"]
