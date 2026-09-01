from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_crud import CRUDBase
from app.core.base_schema import AuthSchema
from app.plugin.module_app.address.model import AppUserAddressModel
from app.plugin.module_app.address.schema import AppUserAddressCreateSchema, AppUserAddressUpdateSchema


class AppUserAddressCRUD(CRUDBase[AppUserAddressModel, AppUserAddressCreateSchema, AppUserAddressUpdateSchema]):
    """Admin data access adapter; this phase exposes read-only Admin routes."""

    def __init__(self, auth: AuthSchema, db: AsyncSession) -> None:
        super().__init__(model=AppUserAddressModel, auth=auth, db=db)


__all__ = ["AppUserAddressCRUD"]
