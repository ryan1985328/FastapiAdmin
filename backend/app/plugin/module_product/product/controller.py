import urllib.parse
from typing import Annotated

from fastapi import APIRouter, Body, Depends, File, Path, Query, Request, UploadFile, status
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import ResponseSchema, StreamResponse, SuccessResponse
from app.core.base_schema import AuthSchema, BatchSetAvailable, PageResultSchema, PaginationQueryParam
from app.core.dependencies import AuthPermission, db_getter
from app.core.router_class import OperationLogRoute
from app.utils.common_util import bytes2file_response

from .schema import ProductCreateSchema, ProductOutSchema, ProductQueryParam, ProductUpdateSchema
from .service import ProductService

ProductRouter = APIRouter(route_class=OperationLogRoute, prefix="/product", tags=["Product模块"])


@ProductRouter.get("/detail/{id}", summary="获取Product详情", response_model=ResponseSchema[ProductOutSchema])
async def get_obj_detail_controller(
    request: Request,
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_product:product:detail"]))],
    id: Annotated[int, Path(description="ProductID")],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    service = ProductService(auth, db)
    result_dict = await service.detail(id=id, request=request)
    return SuccessResponse(data=result_dict, msg="获取Product详情成功")


@ProductRouter.get("/list", summary="分页查询Product", response_model=ResponseSchema[PageResultSchema[ProductOutSchema]])
async def get_obj_list_controller(
    request: Request,
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_product:product:query"]))],
    page: Annotated[PaginationQueryParam, Depends()],
    search: Annotated[ProductQueryParam, Query()],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    service = ProductService(auth, db)
    result_dict = await service.page(
        page_no=page.page_no,
        page_size=page.page_size,
        search=search,
        order_by=page.order_by,
        request=request,
    )
    return SuccessResponse(data=result_dict, msg="查询Product列表成功")


@ProductRouter.post("/create", status_code=status.HTTP_201_CREATED, summary="创建Product", response_model=ResponseSchema[ProductOutSchema])
async def create_obj_controller(
    request: Request,
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_product:product:create"]))],
    data: Annotated[ProductCreateSchema, Body(description="创建参数")],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    service = ProductService(auth, db)
    result_dict = await service.create(data=data, request=request)
    return SuccessResponse(data=result_dict, msg="创建Product成功")


@ProductRouter.put("/update/{id}", summary="修改Product", response_model=ResponseSchema[ProductOutSchema])
async def update_obj_controller(
    request: Request,
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_product:product:update"]))],
    id: Annotated[int, Path(description="ProductID")],
    data: Annotated[ProductUpdateSchema, Body(description="修改参数")],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    service = ProductService(auth, db)
    result_dict = await service.update(id=id, data=data, request=request)
    return SuccessResponse(data=result_dict, msg="修改Product成功")


@ProductRouter.delete("/delete", summary="删除Product", response_model=ResponseSchema[None])
async def delete_obj_controller(
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_product:product:delete"]))],
    ids: Annotated[list[int], Body(description="ID列表")],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    service = ProductService(auth, db)
    await service.delete(ids=ids)
    return SuccessResponse(msg="删除Product成功")


@ProductRouter.patch("/status/batch", summary="批量修改Product状态", response_model=ResponseSchema[None])
async def batch_set_available_obj_controller(
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_product:product:patch"]))],
    data: Annotated[BatchSetAvailable, Body(description="状态设置")],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    service = ProductService(auth, db)
    await service.set_available(data=data)
    return SuccessResponse(msg="批量修改Product状态成功")


@ProductRouter.post("/export", summary="导出Product")
async def export_obj_list_controller(
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_product:product:export"]))],
    search: Annotated[ProductQueryParam, Query()],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> StreamingResponse:
    service = ProductService(auth, db)
    result_dict_list = await service.get_list(search=search)
    export_result = ProductService.batch_export(obj_list=[item.model_dump() for item in result_dict_list])

    return StreamResponse(
        data=bytes2file_response(export_result),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=product.xlsx"},
    )


@ProductRouter.post("/import", summary="导入Product", response_model=ResponseSchema[str])
async def import_obj_list_controller(
    file: Annotated[UploadFile, File(description="导入文件")],
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_product:product:import"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    service = ProductService(auth, db)
    batch_import_result = await service.batch_import(file=file, update_support=True)
    return SuccessResponse(data=batch_import_result, msg="导入Product成功")


@ProductRouter.post("/download/template", summary="获取Product导入模板", dependencies=[Depends(AuthPermission(["module_product:product:download"]))])
async def export_obj_template_controller() -> StreamingResponse:
    import_template_result = ProductService.import_template_download()

    return StreamResponse(
        data=bytes2file_response(import_template_result),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename={urllib.parse.quote('Product导入模板.xlsx')}",
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )
