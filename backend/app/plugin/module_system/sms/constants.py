"""Constants and non-persistent helpers for the starter SMS capability."""

import hashlib
import hmac
import re

from app.common.enums import EnvironmentEnum
from app.config.setting import settings
from app.core.exceptions import CustomException

SMS_PROVIDER_ALIYUN = "aliyun"
SMS_SCENES = frozenset({"register_code", "login_code", "reset_password_code"})
SMS_CODE_TTL = 300
SMS_RESEND_INTERVAL = 60
SMS_HOURLY_LIMIT = 5
SMS_MAX_VERIFY_FAILURES = 5
_FIXED_CODE_ENVIRONMENTS = {EnvironmentEnum.DEV.value, "test"}


def get_fixed_sms_code() -> str | None:
    """Return the configured fixed code only outside production.

    The environment guard is deliberately evaluated at use time so tests can
    exercise both branches without creating a second SMS implementation.
    """

    environment = getattr(settings.ENVIRONMENT, "value", settings.ENVIRONMENT)
    if str(environment).lower() not in _FIXED_CODE_ENVIRONMENTS:
        return None
    if not settings.APP_SMS_FIXED_CODE_ENABLED:
        return None
    code = str(settings.APP_SMS_FIXED_CODE).strip()
    if not re.fullmatch(r"\d{6}", code):
        raise CustomException(msg="固定短信验证码配置无效", status_code=500)
    return code


def normalize_mobile(value: str) -> str:
    """Normalize a mobile number without guessing a country code."""

    mobile = re.sub(r"[\s-]+", "", str(value or "").strip())
    if not re.fullmatch(r"\+?[1-9]\d{6,14}", mobile):
        raise CustomException(msg="手机号格式不正确", status_code=422)
    return mobile


def mask_mobile(value: str) -> str:
    """Mask a mobile number for list responses while retaining search utility."""

    mobile = str(value or "")
    if len(mobile) <= 7:
        return "*" * len(mobile)
    return f"{mobile[:3]}{'*' * (len(mobile) - 7)}{mobile[-4:]}"


def secret_digest(value: str) -> str:
    """Create a keyed digest suitable for Redis values and key derivation."""

    return hmac.new(settings.SECRET_KEY.encode("utf-8"), value.encode("utf-8"), hashlib.sha256).hexdigest()


def mobile_hash(mobile: str) -> str:
    return secret_digest(f"mobile:{mobile}")


def validate_scene(value: str) -> str:
    scene = str(value or "").strip()
    if scene not in SMS_SCENES:
        raise CustomException(msg="短信场景不受支持", status_code=422)
    return scene
