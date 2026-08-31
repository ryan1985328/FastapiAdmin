
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Body, Depends, File, Path, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import ResponseSchema, SuccessResponse
from app.core.base_schema import AuthSchema, UploadResponseSchema
from app.core.dependencies import db_getter
from app.core.exceptions import CustomException

from ..auth.dependencies import get_current_app_user
from ..user.model import AppUserModel
from .schema import AppKycImageSide, AppKycOutSchema, AppKycSubmissionSchema
from .service import AppKycService, _cleanup_temp_file

AppKycRouter = APIRouter(prefix="/kyc", tags=["App用户实名认证"])


@AppKycRouter.get("/mine", summary="获取我的实名认证", response_model=ResponseSchema[AppKycOutSchema | None])
async def get_my_kyc_controller(
    user: Annotated[AppUserModel, Depends(get_current_app_user)],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    result = await AppKycService(db).get_current_out(user.id)
    return SuccessResponse(data=result, msg="获取我的实名认证成功")


@AppKycRouter.post("/upload", summary="上传实名认证图片", response_model=ResponseSchema[UploadResponseSchema])
async def upload_my_kyc_image_controller(
    user: Annotated[AppUserModel, Depends(get_current_app_user)],
    db: Annotated[AsyncSession, Depends(db_getter)],
    file: Annotated[UploadFile, File(description="身份证图片")],
) -> JSONResponse:
    result = await AppKycService(db).upload_image(user.id, file)
    return SuccessResponse(data=result, msg="身份证图片上传成功")


@AppKycRouter.post("/submit", summary="提交实名认证", response_model=ResponseSchema[AppKycOutSchema])
async def submit_my_kyc_controller(
    user: Annotated[AppUserModel, Depends(get_current_app_user)],
    data: Annotated[AppKycSubmissionSchema, Body(description="实名认证资料")],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    result = await AppKycService(db).submit(user, data)
    return SuccessResponse(data=result, msg="实名认证已提交，请等待审核")


@AppKycRouter.post("/resubmit", summary="重新提交实名认证", response_model=ResponseSchema[AppKycOutSchema])
async def resubmit_my_kyc_controller(
    user: Annotated[AppUserModel, Depends(get_current_app_user)],
    data: Annotated[AppKycSubmissionSchema, Body(description="重新提交实名认证资料")],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    result = await AppKycService(db).submit(user, data, resubmit=True)
    return SuccessResponse(data=result, msg="实名认证已重新提交，请等待审核")


@AppKycRouter.get("/file/{side}", summary="查看我的实名认证图片", response_model=None)
async def get_my_kyc_image_controller(
    user: Annotated[AppUserModel, Depends(get_current_app_user)],
    side: Annotated[AppKycImageSide, Path(description="图片面: front 或 back")],
    background_tasks: BackgroundTasks,
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> FileResponse:
    service = AppKycService(db)
    record = await service.get_current(user.id)
    if not record:
        raise CustomException(msg="尚未提交实名认证")
    local_path, file_name = await service.download_image(AuthSchema(), record, side)
    background_tasks.add_task(_cleanup_temp_file, local_path)
    return FileResponse(local_path, filename=file_name)


__all__ = ["AppKycRouter"]
