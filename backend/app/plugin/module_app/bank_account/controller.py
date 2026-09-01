from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import ResponseSchema, SuccessResponse
from app.core.dependencies import db_getter

from ..auth.dependencies import get_current_app_user
from ..user.model import AppUserModel
from .schema import (
    AppUserBankAccountCreateSchema,
    AppUserBankAccountOutSchema,
    AppUserBankAccountUpdateSchema,
)
from .service import AppUserBankAccountService

AppUserBankAccountRouter = APIRouter(prefix="/user/bank-accounts", tags=["App用户银行卡"])


@AppUserBankAccountRouter.get(
    "",
    summary="查询我的银行卡列表",
    response_model=ResponseSchema[list[AppUserBankAccountOutSchema]],
)
async def list_my_bank_accounts_controller(
    user: Annotated[AppUserModel, Depends(get_current_app_user)],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    result = await AppUserBankAccountService(db).list(user.id)
    return SuccessResponse(data=result, msg="查询我的银行卡成功")


@AppUserBankAccountRouter.get(
    "/{id}",
    summary="获取我的银行卡详情",
    response_model=ResponseSchema[AppUserBankAccountOutSchema],
)
async def get_my_bank_account_controller(
    user: Annotated[AppUserModel, Depends(get_current_app_user)],
    id: Annotated[int, Path(description="银行卡ID", ge=1)],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    result = await AppUserBankAccountService(db).detail(user.id, id)
    return SuccessResponse(data=result, msg="获取银行卡详情成功")


@AppUserBankAccountRouter.post(
    "",
    summary="新增我的银行卡",
    response_model=ResponseSchema[AppUserBankAccountOutSchema],
)
async def create_my_bank_account_controller(
    user: Annotated[AppUserModel, Depends(get_current_app_user)],
    data: Annotated[AppUserBankAccountCreateSchema, Body(description="银行卡信息")],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    result = await AppUserBankAccountService(db).create(user.id, data)
    return SuccessResponse(data=result, msg="新增银行卡成功")


@AppUserBankAccountRouter.put(
    "/{id}",
    summary="编辑我的银行卡",
    response_model=ResponseSchema[AppUserBankAccountOutSchema],
)
async def update_my_bank_account_controller(
    user: Annotated[AppUserModel, Depends(get_current_app_user)],
    id: Annotated[int, Path(description="银行卡ID", ge=1)],
    data: Annotated[AppUserBankAccountUpdateSchema, Body(description="银行卡信息")],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    result = await AppUserBankAccountService(db).update(user.id, id, data)
    return SuccessResponse(data=result, msg="编辑银行卡成功")


@AppUserBankAccountRouter.delete(
    "/{id}",
    summary="解绑我的银行卡",
    response_model=ResponseSchema[None],
)
async def delete_my_bank_account_controller(
    user: Annotated[AppUserModel, Depends(get_current_app_user)],
    id: Annotated[int, Path(description="银行卡ID", ge=1)],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    await AppUserBankAccountService(db).delete(user.id, id)
    return SuccessResponse(msg="解绑银行卡成功")


@AppUserBankAccountRouter.put(
    "/{id}/default",
    summary="设置我的默认银行卡",
    response_model=ResponseSchema[AppUserBankAccountOutSchema],
)
async def set_my_default_bank_account_controller(
    user: Annotated[AppUserModel, Depends(get_current_app_user)],
    id: Annotated[int, Path(description="银行卡ID", ge=1)],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    result = await AppUserBankAccountService(db).set_default(user.id, id)
    return SuccessResponse(data=result, msg="默认银行卡设置成功")


__all__ = ["AppUserBankAccountRouter"]
