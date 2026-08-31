import urllib.parse
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Body, Depends, File, Path, Query, UploadFile, status
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.module_storage.file.service import StorageFileService
from app.common.response import ResponseSchema, StreamResponse, SuccessResponse
from app.core.base_schema import AuthSchema, BatchSetAvailable, PageResultSchema, PaginationQueryParam
from app.core.dependencies import AuthPermission, db_getter
from app.core.exceptions import CustomException
from app.core.router_class import OperationLogRoute
from app.utils.common_util import bytes2file_response

from .schema import AppUserKycCreateSchema, AppUserKycOutSchema, AppUserKycQueryParam, AppUserKycReviewSchema, AppUserKycUpdateSchema
from .service import AppUserKycService


def _cleanup_temp_file(path: str) -> None:
    import os

    try:
        os.unlink(path)
    except OSError:
        pass

AppUserKycRouter = APIRouter(route_class=OperationLogRoute, prefix="/kyc", tags=["用户实名认证模块"])


@AppUserKycRouter.get("/detail/{id}", summary="获取用户实名认证详情", response_model=ResponseSchema[AppUserKycOutSchema])
async def get_obj_detail_controller(
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_system:kyc:detail"]))],
    id: Annotated[int, Path(description="用户实名认证ID")],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    service = AppUserKycService(auth, db)
    result_dict = await service.detail(id=id)
    return SuccessResponse(data=result_dict, msg="获取用户实名认证详情成功")


@AppUserKycRouter.get("/list", summary="分页查询用户实名认证", response_model=ResponseSchema[PageResultSchema[AppUserKycOutSchema]])
async def get_obj_list_controller(
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_system:kyc:query"]))],
    page: Annotated[PaginationQueryParam, Depends()],
    search: Annotated[AppUserKycQueryParam, Query()],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    service = AppUserKycService(auth, db)
    result_dict = await service.page(
        page_no=page.page_no,
        page_size=page.page_size,
        search=search,
        order_by=page.order_by,
    )
    return SuccessResponse(data=result_dict, msg="查询用户实名认证列表成功")


@AppUserKycRouter.post("/create", status_code=status.HTTP_201_CREATED, summary="创建用户实名认证", response_model=ResponseSchema[AppUserKycOutSchema])
async def create_obj_controller(
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_system:kyc:create"]))],
    data: Annotated[AppUserKycCreateSchema, Body(description="创建参数")],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    service = AppUserKycService(auth, db)
    result_dict = await service.create(data=data)
    return SuccessResponse(data=result_dict, msg="创建用户实名认证成功")


@AppUserKycRouter.put("/update/{id}", summary="修改用户实名认证", response_model=ResponseSchema[AppUserKycOutSchema])
async def update_obj_controller(
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_system:kyc:update"]))],
    id: Annotated[int, Path(description="用户实名认证ID")],
    data: Annotated[AppUserKycUpdateSchema, Body(description="修改参数")],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    service = AppUserKycService(auth, db)
    result_dict = await service.update(id=id, data=data)
    return SuccessResponse(data=result_dict, msg="修改用户实名认证成功")


@AppUserKycRouter.post("/review/{id}", summary="审核用户实名认证", response_model=ResponseSchema[AppUserKycOutSchema])
async def review_obj_controller(
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_system:kyc:update"]))],
    id: Annotated[int, Path(description="用户实名认证ID")],
    data: Annotated[AppUserKycReviewSchema, Body(description="审核结果")],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    result_dict = await AppUserKycService(auth, db).review(id=id, data=data)
    return SuccessResponse(data=result_dict, msg="实名认证审核成功")


@AppUserKycRouter.delete("/delete", summary="删除用户实名认证", response_model=ResponseSchema[None])
async def delete_obj_controller(
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_system:kyc:delete"]))],
    ids: Annotated[list[int], Body(description="ID列表")],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    service = AppUserKycService(auth, db)
    await service.delete(ids=ids)
    return SuccessResponse(msg="删除用户实名认证成功")


@AppUserKycRouter.get("/file/{id}/{side}", summary="查看实名认证图片", response_model=None)
async def get_kyc_file_controller(
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_system:kyc:detail"]))],
    id: Annotated[int, Path(description="用户实名认证ID", ge=1)],
    side: Annotated[str, Path(pattern="^(front|back)$", description="图片面: front 或 back")],
    background_tasks: BackgroundTasks,
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> FileResponse:
    service = AppUserKycService(auth, db)
    record = await service.detail(id=id)
    path = record.id_card_front if side == "front" else record.id_card_back
    if not path:
        raise CustomException(msg="尚未上传该证件图片")
    local_path, file_name = await StorageFileService(auth, db).download(source_id=None, remote_path=path)
    background_tasks.add_task(_cleanup_temp_file, local_path)
    return FileResponse(local_path, filename=file_name)


@AppUserKycRouter.patch("/status/batch", summary="批量修改用户实名认证状态", response_model=ResponseSchema[None])
async def batch_set_available_obj_controller(
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_system:kyc:patch"]))],
    data: Annotated[BatchSetAvailable, Body(description="状态设置")],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    service = AppUserKycService(auth, db)
    await service.set_available(data=data)
    return SuccessResponse(msg="批量修改用户实名认证状态成功")


@AppUserKycRouter.post("/export", summary="导出用户实名认证")
async def export_obj_list_controller(
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_system:kyc:export"]))],
    search: Annotated[AppUserKycQueryParam, Query()],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> StreamingResponse:
    service = AppUserKycService(auth, db)
    result_dict_list = await service.get_list(search=search)
    export_result = AppUserKycService.batch_export(obj_list=[item.model_dump() for item in result_dict_list])

    return StreamResponse(
        data=bytes2file_response(export_result),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=app_user_kyc.xlsx"},
    )


@AppUserKycRouter.post("/import", summary="导入用户实名认证", response_model=ResponseSchema[str])
async def import_obj_list_controller(
    file: Annotated[UploadFile, File(description="导入文件")],
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_system:kyc:import"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    service = AppUserKycService(auth, db)
    batch_import_result = await service.batch_import(file=file, update_support=True)
    return SuccessResponse(data=batch_import_result, msg="导入用户实名认证成功")


@AppUserKycRouter.post("/download/template", summary="获取用户实名认证导入模板", dependencies=[Depends(AuthPermission(["module_system:kyc:download"]))])
async def export_obj_template_controller() -> StreamingResponse:
    import_template_result = AppUserKycService.import_template_download()

    return StreamResponse(
        data=bytes2file_response(import_template_result),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename={urllib.parse.quote('用户实名认证导入模板.xlsx')}",
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )
