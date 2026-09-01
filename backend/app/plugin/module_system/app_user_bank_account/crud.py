from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_crud import CRUDBase
from app.core.base_schema import AuthSchema
from app.plugin.module_app.bank_account.schema import (
    AppUserBankAccountCreateSchema,
    AppUserBankAccountUpdateSchema,
)

from .model import AppUserBankAccountModel


class AppUserBankAccountCRUD(
    CRUDBase[AppUserBankAccountModel, AppUserBankAccountCreateSchema, AppUserBankAccountUpdateSchema]
):
    """Generic CRUD adapter retained for Generator compatibility.

    Product routes intentionally use the specialized service and do not
    expose generic Admin create/edit/delete operations.
    """

    def __init__(self, auth: AuthSchema, db: AsyncSession) -> None:
        super().__init__(model=AppUserBankAccountModel, auth=auth, db=db)


__all__ = ["AppUserBankAccountCRUD"]
