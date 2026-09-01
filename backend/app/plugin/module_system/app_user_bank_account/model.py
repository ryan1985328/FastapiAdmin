"""Reuse the App-owned bank account model instead of declaring a second table."""

from app.plugin.module_app.bank_account.model import AppUserBankAccountModel

__all__ = ["AppUserBankAccountModel"]
