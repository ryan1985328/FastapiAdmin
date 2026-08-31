"""Small, opaque referral-code generator for App Users."""

import secrets

# Avoid visually ambiguous characters in manually entered/shared codes.
REFERRAL_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
REFERRAL_CODE_LENGTH = 10


def generate_referral_code() -> str:
    """Return a stable-looking, non-sequential referral code."""

    return "".join(secrets.choice(REFERRAL_CODE_ALPHABET) for _ in range(REFERRAL_CODE_LENGTH))


__all__ = ["REFERRAL_CODE_ALPHABET", "REFERRAL_CODE_LENGTH", "generate_referral_code"]
