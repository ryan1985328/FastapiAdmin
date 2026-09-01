import re
from collections.abc import Mapping
from typing import Any

REDACTED_VALUE = "[REDACTED]"
_SENSITIVE_FIELD_NAMES = frozenset({"card_number", "cardnumber"})
_LONG_DIGIT_PATTERN = re.compile(r"(?<!\d)\d{12,19}(?!\d)")


def redact_sensitive_text(value: str) -> str:
    """Remove card-sized digit sequences from logs and error text."""

    return _LONG_DIGIT_PATTERN.sub(REDACTED_VALUE, value)


def redact_sensitive_payload(value: Any) -> Any:
    """Recursively redact known sensitive payload fields without changing shape."""

    if isinstance(value, Mapping):
        return {
            key: REDACTED_VALUE if str(key).lower() in _SENSITIVE_FIELD_NAMES else redact_sensitive_payload(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact_sensitive_payload(item) for item in value]
    if isinstance(value, tuple):
        return tuple(redact_sensitive_payload(item) for item in value)
    if isinstance(value, str):
        return redact_sensitive_text(value)
    return value


def redact_validation_errors(errors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Redact a card input even when Pydantic stores it under the ``input`` key."""

    redacted: list[dict[str, Any]] = []
    for error in errors:
        item = redact_sensitive_payload(error)
        location = error.get("loc", ())
        if isinstance(location, (list, tuple)) and any(
            str(part).lower() in _SENSITIVE_FIELD_NAMES for part in location
        ):
            item["input"] = REDACTED_VALUE
        redacted.append(item)
    return redacted


__all__ = [
    "REDACTED_VALUE",
    "redact_sensitive_payload",
    "redact_sensitive_text",
    "redact_validation_errors",
]
