"""Admin routes for SMS templates."""

from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import ResponseSchema, SuccessResponse
from app.core.base_schema import AuthSchema, BatchSetAvailable, PageResultSchema, PaginationQueryParam
from app.core.dependencies import AuthPermission, db_getter

from .schema import SmsTemplateCreateSchema, SmsTemplateOutSchema, SmsTemplateQueryParam, SmsTemplateUpdateSchema
from .service import SmsTemplateService

SmsTemplateRouter = APIRouter(prefix="/sms_template", tags=["短信模板模块"])


@SmsTemplateRouter.get("/detail/{id}", summary="获取短信模板详情", response_model=ResponseSchema[SmsTemplateOutSchema])
async def get_detail(
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_system:sms_template:detail"]))],
    id: Annotated[int, Path(ge=1, description="短信模板ID")],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    return SuccessResponse(data=await SmsTemplateService(auth, db).detail(id), msg="获取短信模板详情成功")


@SmsTemplateRouter.get("/list", summary="分页查询短信模板", response_model=ResponseSchema[PageResultSchema[SmsTemplateOutSchema]])
async def get_list(
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_system:sms_template:query"]))],
    page: Annotated[PaginationQueryParam, Depends()],
    search: Annotated[SmsTemplateQueryParam, Query()],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    result = await SmsTemplateService(auth, db).page(page.page_no, page.page_size, search, page.order_by)
    return SuccessResponse(data=result, msg="查询短信模板列表成功")


@SmsTemplateRouter.post("/create", status_code=201, summary="创建短信模板", response_model=ResponseSchema[SmsTemplateOutSchema])
async def create(
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_system:sms_template:create"]))],
    data: Annotated[SmsTemplateCreateSchema, Body(description="创建参数")],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    return SuccessResponse(data=await SmsTemplateService(auth, db).create(data), msg="创建短信模板成功", status_code=201)


@SmsTemplateRouter.put("/update/{id}", summary="修改短信模板", response_model=ResponseSchema[SmsTemplateOutSchema])
async def update(
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_system:sms_template:update"]))],
    id: Annotated[int, Path(ge=1, description="短信模板ID")],
    data: Annotated[SmsTemplateUpdateSchema, Body(description="修改参数")],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    return SuccessResponse(data=await SmsTemplateService(auth, db).update(id, data), msg="修改短信模板成功")


@SmsTemplateRouter.patch("/status/batch", summary="批量修改短信模板状态", response_model=ResponseSchema[None])
async def set_available(
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_system:sms_template:patch"]))],
    data: Annotated[BatchSetAvailable, Body(description="状态设置")],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    await SmsTemplateService(auth, db).set_available(data)
    return SuccessResponse(msg="修改短信模板状态成功")


__all__ = ["SmsTemplateRouter"]
