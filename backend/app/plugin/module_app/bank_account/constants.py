from enum import IntEnum


class AppUserBankAccountStatus(IntEnum):
    """Bank account status; the values are intentionally 0=active, 1=disabled."""

    ACTIVE = 0
    DISABLED = 1


BANK_ACCOUNT_STATUS_DICT = "app_user_bank_account_status"


__all__ = ["AppUserBankAccountStatus", "BANK_ACCOUNT_STATUS_DICT"]
