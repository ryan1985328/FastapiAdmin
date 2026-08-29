# -*- coding: utf-8 -*-

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_crud import CRUDBase
from app.core.base_schema import AuthSchema
from app.plugin.module_app.user.model import AppUserModel

from .schema import AppUserUpdateSchema


class AppUserCRUD(CRUDBase[AppUserModel, AppUserUpdateSchema, AppUserUpdateSchema]):
    """Admin data access for the independent App user model."""

    def __init__(self, auth: AuthSchema, db: AsyncSession) -> None:
        super().__init__(model=AppUserModel, auth=auth, db=db)


__all__ = ["AppUserCRUD"]
