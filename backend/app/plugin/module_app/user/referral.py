"""Small, opaque referral-code generator for App Users."""

import re
import secrets

# Avoid visually ambiguous characters in manually entered/shared codes.
REFERRAL_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
REFERRAL_CODE_LENGTH = 10
_REFERRAL_CODE_PATTERN = re.compile(r"^[A-Z0-9]{4,32}$")


def generate_referral_code() -> str:
    """Return a stable-looking, non-sequential referral code."""

    return "".join(secrets.choice(REFERRAL_CODE_ALPHABET) for _ in range(REFERRAL_CODE_LENGTH))


def normalize_referral_code(value: str) -> str:
    """Normalize the user-entered referral code used by every bind path."""

    code = str(value or "").strip().upper()
    if not _REFERRAL_CODE_PATTERN.fullmatch(code):
        raise ValueError("推荐码格式无效")
    return code


__all__ = [
    "REFERRAL_CODE_ALPHABET",
    "REFERRAL_CODE_LENGTH",
    "generate_referral_code",
    "normalize_referral_code",
]
