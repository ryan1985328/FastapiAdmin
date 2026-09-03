"""Shared SMS capability primitives used by Admin and App integrations."""

from .constants import SMS_PROVIDERS, SMS_SCENES, get_fixed_sms_code, mask_mobile, normalize_mobile
from .provider import SmsProvider, SmsProviderResult, create_provider
from .service import SmsService

__all__ = [
    "SMS_SCENES",
    "SMS_PROVIDERS",
    "SmsProvider",
    "SmsProviderResult",
    "SmsService",
    "create_provider",
    "get_fixed_sms_code",
    "mask_mobile",
    "normalize_mobile",
]
