from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import ResponseSchema, SuccessResponse
from app.core.dependencies import db_getter

from ..auth.dependencies import get_current_app_user
from ..user.model import AppUserModel
from .schema import AppUserAddressCreateSchema, AppUserAddressOutSchema, AppUserAddressUpdateSchema
from .service import AppUserAddressService

AppUserAddressRouter = APIRouter(prefix="/user/addresses", tags=["App用户地址"])


@AppUserAddressRouter.get("", summary="查询我的地址列表", response_model=ResponseSchema[list[AppUserAddressOutSchema]])
async def list_my_addresses_controller(
    user: Annotated[AppUserModel, Depends(get_current_app_user)],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    result = await AppUserAddressService(db).list(user.id)
    return SuccessResponse(data=result, msg="查询我的地址成功")


@AppUserAddressRouter.get("/{id}", summary="获取我的地址详情", response_model=ResponseSchema[AppUserAddressOutSchema])
async def get_my_address_controller(
    user: Annotated[AppUserModel, Depends(get_current_app_user)],
    id: Annotated[int, Path(description="地址ID", ge=1)],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    result = await AppUserAddressService(db).detail(user.id, id)
    return SuccessResponse(data=result, msg="获取地址详情成功")


@AppUserAddressRouter.post("", summary="新增我的地址", response_model=ResponseSchema[AppUserAddressOutSchema])
async def create_my_address_controller(
    user: Annotated[AppUserModel, Depends(get_current_app_user)],
    data: Annotated[AppUserAddressCreateSchema, Body(description="地址信息")],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    result = await AppUserAddressService(db).create(user.id, data)
    return SuccessResponse(data=result, msg="新增地址成功")


@AppUserAddressRouter.put("/{id}", summary="编辑我的地址", response_model=ResponseSchema[AppUserAddressOutSchema])
async def update_my_address_controller(
    user: Annotated[AppUserModel, Depends(get_current_app_user)],
    id: Annotated[int, Path(description="地址ID", ge=1)],
    data: Annotated[AppUserAddressUpdateSchema, Body(description="地址信息")],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    result = await AppUserAddressService(db).update(user.id, id, data)
    return SuccessResponse(data=result, msg="编辑地址成功")


@AppUserAddressRouter.delete("/{id}", summary="删除我的地址", response_model=ResponseSchema[None])
async def delete_my_address_controller(
    user: Annotated[AppUserModel, Depends(get_current_app_user)],
    id: Annotated[int, Path(description="地址ID", ge=1)],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    await AppUserAddressService(db).delete(user.id, id)
    return SuccessResponse(msg="删除地址成功")


@AppUserAddressRouter.put("/{id}/default", summary="设置我的默认地址", response_model=ResponseSchema[AppUserAddressOutSchema])
async def set_my_default_address_controller(
    user: Annotated[AppUserModel, Depends(get_current_app_user)],
    id: Annotated[int, Path(description="地址ID", ge=1)],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    result = await AppUserAddressService(db).set_default(user.id, id)
    return SuccessResponse(data=result, msg="默认地址设置成功")


__all__ = ["AppUserAddressRouter"]
