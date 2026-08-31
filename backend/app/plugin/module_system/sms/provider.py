"""Provider abstraction and the first Alibaba Cloud SMS adapter."""

import json
from dataclasses import dataclass
from typing import Any, Protocol

from app.core.exceptions import CustomException

from .constants import SMS_PROVIDER_ALIYUN


@dataclass(frozen=True, slots=True)
class SmsProviderResult:
    """Provider-neutral send result persisted by :class:`SmsService`."""

    provider: str
    success: bool
    code: str | None = None
    message: str | None = None
    request_id: str | None = None


class SmsProvider(Protocol):
    async def send(
        self,
        *,
        mobile: str,
        sign_name: str,
        template_code: str,
        params: dict[str, Any],
    ) -> SmsProviderResult:
        """Send one message and return a normalized result."""


def _value(obj: object, *names: str) -> Any:
    for name in names:
        value = getattr(obj, name, None)
        if value is not None:
            return value
    if isinstance(obj, dict):
        for name in names:
            if name in obj and obj[name] is not None:
                return obj[name]
    return None


def _safe_error_message(exc: BaseException, secrets: tuple[str, ...] = ()) -> str:
    message = str(exc).strip() or type(exc).__name__
    for secret in secrets:
        if secret:
            message = message.replace(secret, "***")
    return message[:1000]


class AliyunSmsProvider:
    """Thin adapter around Alibaba Cloud's official Dysmsapi V2 SDK."""

    provider = SMS_PROVIDER_ALIYUN

    def __init__(self, access_key_id: str, access_key_secret: str, *, endpoint: str = "dysmsapi.aliyuncs.com") -> None:
        self.access_key_id = access_key_id.strip()
        self.access_key_secret = access_key_secret
        self.endpoint = endpoint

    async def send(
        self,
        *,
        mobile: str,
        sign_name: str,
        template_code: str,
        params: dict[str, Any],
    ) -> SmsProviderResult:
        if not self.access_key_id or not self.access_key_secret:
            return SmsProviderResult(
                provider=self.provider,
                success=False,
                code="CONFIG_MISSING",
                message="阿里云短信渠道未配置完整的 AccessKey",
            )

        try:
            from alibabacloud_dysmsapi20170525 import models as dysmsapi_20170525_models
            from alibabacloud_dysmsapi20170525.client import Client as Dysmsapi20170525Client
            from alibabacloud_tea_openapi import models as open_api_models
            from alibabacloud_tea_util import models as util_models

            config = open_api_models.Config(
                access_key_id=self.access_key_id,
                access_key_secret=self.access_key_secret,
                endpoint=self.endpoint,
            )
            client = Dysmsapi20170525Client(config)
            request = dysmsapi_20170525_models.SendSmsRequest(
                phone_numbers=mobile,
                sign_name=sign_name,
                template_code=template_code,
                template_param=json.dumps(params, ensure_ascii=False, separators=(",", ":")),
            )
            response = await client.send_sms_with_options_async(request, util_models.RuntimeOptions())
            body = _value(response, "body", "Body") or response
            code = _value(body, "code", "Code")
            message = _value(body, "message", "Message")
            request_id = _value(body, "request_id", "RequestId") or _value(response, "request_id", "RequestId")
            code_text = str(code) if code is not None else None
            return SmsProviderResult(
                provider=self.provider,
                success=code_text is not None and code_text.upper() == "OK",
                code=code_text,
                message=str(message) if message is not None else None,
                request_id=str(request_id) if request_id is not None else None,
            )
        except Exception as exc:
            return SmsProviderResult(
                provider=self.provider,
                success=False,
                code="PROVIDER_EXCEPTION",
                message=_safe_error_message(exc, (self.access_key_id, self.access_key_secret)),
            )


class MockSmsProvider:
    """Small injectable provider used by focused service tests."""

    def __init__(self, result: SmsProviderResult | None = None) -> None:
        self.calls: list[dict[str, Any]] = []
        self.result = result or SmsProviderResult(provider="mock", success=True, code="OK", message="ok")

    async def send(
        self,
        *,
        mobile: str,
        sign_name: str,
        template_code: str,
        params: dict[str, Any],
    ) -> SmsProviderResult:
        self.calls.append(
            {
                "mobile": mobile,
                "sign_name": sign_name,
                "template_code": template_code,
                "params": params.copy(),
            },
        )
        return self.result


def create_provider(provider: str, access_key_id: str, access_key_secret: str) -> SmsProvider:
    if provider == SMS_PROVIDER_ALIYUN:
        return AliyunSmsProvider(access_key_id, access_key_secret)
    raise CustomException(msg=f"暂不支持短信供应商: {provider}", status_code=422)


__all__ = [
    "AliyunSmsProvider",
    "MockSmsProvider",
    "SmsProvider",
    "SmsProviderResult",
    "create_provider",
]
