"""Shared SMS capability primitives used by Admin and App integrations."""

from .constants import SMS_SCENES, mask_mobile, normalize_mobile
from .provider import SmsProvider, SmsProviderResult, create_provider
from .service import SmsService

__all__ = [
    "SMS_SCENES",
    "SmsProvider",
    "SmsProviderResult",
    "SmsService",
    "create_provider",
    "mask_mobile",
    "normalize_mobile",
]
