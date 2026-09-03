"""Application clock helpers.

The current V1.x database contract stores business timestamps in MySQL
``DATETIME`` columns as naive application-local wall-clock values.  This
module makes that contract explicit without depending on the host operating
system timezone or adding a fixed offset.
"""

from datetime import datetime
from functools import lru_cache
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.config.setting import settings


@lru_cache(maxsize=8)
def _get_timezone(timezone_name: str) -> ZoneInfo:
    try:
        return ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError as exc:
        raise RuntimeError(f"APPLICATION_TIMEZONE 无效: {timezone_name}") from exc


def application_now() -> datetime:
    """Return the configured application-local time as a naive datetime."""

    return datetime.now(_get_timezone(settings.APPLICATION_TIMEZONE)).replace(tzinfo=None)
