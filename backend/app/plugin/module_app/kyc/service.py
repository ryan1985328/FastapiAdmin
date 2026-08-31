
import os
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.module_storage.file.service import StorageFileService
from app.core.base_schema import AuthSchema, UploadResponseSchema
from app.core.exceptions import CustomException
from app.plugin.module_system.kyc.model import AppUserKycModel
from app.utils.upload_util import UploadUtil

from ..user.model import AppUserModel
from .schema import AppKycImageSide, AppKycOutSchema, AppKycSubmissionSchema

KYC_PENDING = 0
KYC_APPROVED = 1
KYC_REJECTED = 2
KYC_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif"}


def _cleanup_temp_file(path: str) -> None:
    try:
        os.unlink(path)
    except OSError:
        pass


class AppKycService:
    """App 用户实名认证的单记录提交、上传与读取服务。"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_current(self, app_user_id: int) -> AppUserKycModel | None:
        result = await self.db.execute(
            select(AppUserKycModel)
            .where(
                AppUserKycModel.app_user_id == app_user_id,
                AppUserKycModel.is_deleted.is_(False),
            )
            .order_by(AppUserKycModel.id.asc())
        )
        records = result.scalars().all()
        if len(records) > 1:
            raise CustomException(msg="该用户存在多条实名认证记录，请联系管理员处理")
        return records[0] if records else None

    async def get_current_out(self, app_user_id: int) -> AppKycOutSchema | None:
        record = await self.get_current(app_user_id)
        return AppKycOutSchema.model_validate(record) if record else None

    @staticmethod
    def _validate_storage_reference(reference: str, app_user_id: int) -> str:
        try:
            normalized = StorageFileService._validate_remote_path(reference)
        except CustomException:
            raise
        except Exception as exc:
            raise CustomException(msg="图片文件引用无效") from exc

        prefix = f"kyc/{app_user_id}/"
        if not normalized.startswith(prefix):
            raise CustomException(msg="图片文件不属于当前用户")
        return normalized

    async def _validate_uploaded_references(self, data: AppKycSubmissionSchema, app_user_id: int) -> dict[str, str]:
        front = self._validate_storage_reference(data.id_card_front, app_user_id)
        back = self._validate_storage_reference(data.id_card_back, app_user_id)
        storage = StorageFileService(AuthSchema(), self.db)
        if not await storage.exists(source_id=None, remote_path=front):
            raise CustomException(msg="身份证正面图片不存在，请重新上传")
        if not await storage.exists(source_id=None, remote_path=back):
            raise CustomException(msg="身份证反面图片不存在，请重新上传")
        return {"id_card_front": front, "id_card_back": back}

    async def submit(
        self,
        app_user: AppUserModel,
        data: AppKycSubmissionSchema,
        *,
        resubmit: bool = False,
    ) -> AppKycOutSchema:
        references = await self._validate_uploaded_references(data, app_user.id)
        record = await self.get_current(app_user.id)

        if record and record.status == KYC_APPROVED:
            raise CustomException(msg="实名认证已通过，不能重复提交")
        if record and record.status == KYC_PENDING:
            raise CustomException(msg="实名认证正在审核中，请勿重复提交")
        if resubmit and (not record or record.status != KYC_REJECTED):
            raise CustomException(msg="当前没有可重新提交的驳回记录")

        payload = data.model_dump(exclude={"id_card_front", "id_card_back"})
        payload.update(references)
        if record is None:
            record = AppUserKycModel(
                app_user_id=app_user.id,
                status=KYC_PENDING,
                **payload,
            )
            self.db.add(record)
        else:
            for key, value in payload.items():
                setattr(record, key, value)
            record.status = KYC_PENDING
            record.review_remark = None
            record.reviewed_at = None

        await self.db.flush()
        await self.db.refresh(record)
        return AppKycOutSchema.model_validate(record)

    async def upload_image(self, app_user_id: int, file: UploadFile) -> UploadResponseSchema:
        if not file or not file.filename:
            raise CustomException(msg="请选择身份证图片")
        extension = UploadUtil.get_extension_from_filename(file.filename).lower()
        if extension not in KYC_IMAGE_EXTENSIONS:
            raise CustomException(msg="身份证图片仅支持 JPG、JPEG、PNG 或 GIF 格式")
        if not file.content_type or not file.content_type.startswith("image/"):
            raise CustomException(msg="身份证文件必须是图片")

        result = await StorageFileService(AuthSchema(), self.db).upload(
            source_id=None,
            file=file,
            remote_path=f"kyc/{app_user_id}/{uuid4().hex}",
        )
        return UploadResponseSchema.model_validate(result)

    async def download_image(
        self,
        auth: AuthSchema,
        record: AppUserKycModel,
        side: AppKycImageSide,
    ) -> tuple[str, str]:
        path = record.id_card_front if side == "front" else record.id_card_back
        if not path:
            raise CustomException(msg="该实名认证尚未上传此证件图片")
        return await StorageFileService(auth, self.db).download(source_id=None, remote_path=path)


__all__ = [
    "AppKycService",
    "KYC_APPROVED",
    "KYC_PENDING",
    "KYC_REJECTED",
    "_cleanup_temp_file",
]
