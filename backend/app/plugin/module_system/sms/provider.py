"""Provider abstraction and the built-in Alibaba/Tencent SMS adapters."""

import asyncio
import json
from dataclasses import dataclass
from typing import Any, Protocol

from app.core.exceptions import CustomException

from .constants import SMS_PROVIDER_ALIYUN, SMS_PROVIDER_TENCENT


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


class TencentSmsProvider:
    """Thin adapter around Tencent Cloud's official SMS SDK."""

    provider = SMS_PROVIDER_TENCENT

    def __init__(self, secret_id: str, secret_key: str, sms_sdk_app_id: str, *, region: str = "ap-guangzhou") -> None:
        self.secret_id = secret_id.strip()
        self.secret_key = secret_key
        self.sms_sdk_app_id = sms_sdk_app_id.strip()
        self.region = region

    @staticmethod
    def _phone_number(mobile: str) -> str:
        """Tencent's API expects E.164; the Starter's default market is China."""

        return mobile if mobile.startswith("+") else f"+86{mobile}"

    async def send(
        self,
        *,
        mobile: str,
        sign_name: str,
        template_code: str,
        params: dict[str, Any],
    ) -> SmsProviderResult:
        if not self.secret_id or not self.secret_key or not self.sms_sdk_app_id:
            return SmsProviderResult(
                provider=self.provider,
                success=False,
                code="CONFIG_MISSING",
                message="腾讯云短信渠道未配置完整的 SecretId、SecretKey 或 SDK App ID",
            )

        try:
            from tencentcloud.common import credential
            from tencentcloud.sms.v20210111 import models, sms_client

            cred = credential.Credential(self.secret_id, self.secret_key)
            client = sms_client.SmsClient(cred, self.region)
            request = models.SendSmsRequest()
            request.SmsSdkAppId = self.sms_sdk_app_id
            request.SignName = sign_name
            request.TemplateId = template_code
            request.TemplateParamSet = [str(value) for value in params.values()]
            request.PhoneNumberSet = [self._phone_number(mobile)]

            response = await asyncio.to_thread(client.SendSms, request)
            status_set = _value(response, "SendStatusSet", "send_status_set") or []
            first_status = status_set[0] if status_set else None
            code = _value(first_status, "Code", "code")
            message = _value(first_status, "Message", "message")
            request_id = _value(response, "RequestId", "request_id")
            request_id = request_id or _value(first_status, "SerialNo", "serial_no")
            code_text = str(code) if code is not None else None
            return SmsProviderResult(
                provider=self.provider,
                success=code_text is not None and code_text.lower() == "ok",
                code=code_text,
                message=str(message) if message is not None else None,
                request_id=str(request_id) if request_id is not None else None,
            )
        except Exception as exc:
            return SmsProviderResult(
                provider=self.provider,
                success=False,
                code="PROVIDER_EXCEPTION",
                message=_safe_error_message(exc, (self.secret_id, self.secret_key)),
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


def create_provider(
    provider: str,
    access_key_id: str,
    access_key_secret: str,
    *,
    sms_sdk_app_id: str | None = None,
) -> SmsProvider:
    if provider == SMS_PROVIDER_ALIYUN:
        return AliyunSmsProvider(access_key_id, access_key_secret)
    if provider == SMS_PROVIDER_TENCENT:
        return TencentSmsProvider(access_key_id, access_key_secret, sms_sdk_app_id or "")
    raise CustomException(msg=f"暂不支持短信供应商: {provider}", status_code=422)


__all__ = [
    "AliyunSmsProvider",
    "MockSmsProvider",
    "SmsProvider",
    "SmsProviderResult",
    "TencentSmsProvider",
    "create_provider",
]
