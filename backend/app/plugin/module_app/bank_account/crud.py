from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_crud import CRUDBase
from app.core.base_schema import AuthSchema

from .model import AppUserBankAccountModel
from .schema import AppUserBankAccountCreateSchema, AppUserBankAccountUpdateSchema


class AppUserBankAccountCRUD(
    CRUDBase[AppUserBankAccountModel, AppUserBankAccountCreateSchema, AppUserBankAccountUpdateSchema]
):
    """Data access adapter; ownership and sensitive projections stay in Service."""

    def __init__(self, auth: AuthSchema, db: AsyncSession) -> None:
        super().__init__(model=AppUserBankAccountModel, auth=auth, db=db)


__all__ = ["AppUserBankAccountCRUD"]
