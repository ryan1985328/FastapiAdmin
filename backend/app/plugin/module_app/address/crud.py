from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_crud import CRUDBase
from app.core.base_schema import AuthSchema

from .model import AppUserAddressModel
from .schema import AppUserAddressCreateSchema, AppUserAddressUpdateSchema


class AppUserAddressCRUD(CRUDBase[AppUserAddressModel, AppUserAddressCreateSchema, AppUserAddressUpdateSchema]):
    """基础 CRUD 适配；地址归属和默认地址规则由 Service 统一负责。"""

    def __init__(self, auth: AuthSchema, db: AsyncSession) -> None:
        super().__init__(model=AppUserAddressModel, auth=auth, db=db)


__all__ = ["AppUserAddressCRUD"]
