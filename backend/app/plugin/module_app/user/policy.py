"""Reusable Business User capability policies."""

from typing import Any

from app.core.exceptions import CustomException

from .constants import AppUserStatus


def _status_value(user_or_status: Any) -> int:
    if isinstance(user_or_status, (AppUserStatus, int)):
        return int(user_or_status)
    return int(getattr(user_or_status, "status"))


def is_asset_operation_allowed(user_or_status: Any) -> bool:
    """Return whether the user may perform future asset-domain operations.

    Asset operations are allowed only for ACTIVE users. FROZEN users remain
    valid for login and ordinary non-asset capabilities, but are denied here.
    DISABLED and unknown statuses are also denied by default.
    """

    return _status_value(user_or_status) == int(AppUserStatus.ACTIVE)


def assert_asset_operation_allowed(user_or_status: Any) -> None:
    """Raise the shared business-policy error for a disallowed asset action."""

    if not is_asset_operation_allowed(user_or_status):
        raise CustomException(msg="当前用户不允许进行资产类操作", status_code=403, code=10403)


class AppUserPolicy:
    """Namespace for future business modules that prefer a policy object."""

    is_asset_operation_allowed = staticmethod(is_asset_operation_allowed)
    assert_asset_operation_allowed = staticmethod(assert_asset_operation_allowed)


__all__ = [
    "AppUserPolicy",
    "assert_asset_operation_allowed",
    "is_asset_operation_allowed",
]
