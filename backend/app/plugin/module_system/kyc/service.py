
from datetime import UTC, datetime
from typing import Any

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_schema import AuthSchema, BatchSetAvailable, PageResultSchema
from app.core.exceptions import CustomException
from app.core.logger import logger
from app.utils.common_util import search_to_dict
from app.utils.excel_util import ExcelUtil

from .crud import AppUserKycCRUD
from .schema import (
    AppUserKycCreateSchema,
    AppUserKycOutSchema,
    AppUserKycQueryParam,
    AppUserKycReviewSchema,
    AppUserKycUpdateSchema,
)


class AppUserKycService:
    """用户实名认证模块服务层"""

    def __init__(self, auth: AuthSchema, db: AsyncSession) -> None:
        self.auth = auth
        self.db = db

    async def detail(self, id: int) -> AppUserKycOutSchema:
        obj = await AppUserKycCRUD(self.auth, self.db).get(id=id)
        if not obj:
            raise CustomException(msg="该数据不存在")
        return AppUserKycOutSchema.model_validate(obj)

    async def get_list(
        self,
        search: AppUserKycQueryParam | None = None,
        order_by: list[dict[str, str]] | None = None,
    ) -> list[AppUserKycOutSchema]:
        obj_list = await AppUserKycCRUD(self.auth, self.db).get_list(search=search_to_dict(search), order_by=order_by)
        return [AppUserKycOutSchema.model_validate(obj) for obj in obj_list]

    async def page(
        self,
        page_no: int,
        page_size: int,
        search: AppUserKycQueryParam | None = None,
        order_by: list[dict[str, str]] | None = None,
    ) -> PageResultSchema[AppUserKycOutSchema]:
        offset = (page_no - 1) * page_size
        return await AppUserKycCRUD(self.auth, self.db).page(
            offset=offset,
            limit=page_size,
            order_by=order_by or [{"id": "asc"}],
            search=search_to_dict(search, {}),
            out_schema=AppUserKycOutSchema,
        )

    async def create(self, data: AppUserKycCreateSchema) -> AppUserKycOutSchema:
        obj = await AppUserKycCRUD(self.auth, self.db).create(data=data)
        return AppUserKycOutSchema.model_validate(obj)

    async def update(self, id: int, data: AppUserKycUpdateSchema) -> AppUserKycOutSchema:
        obj = await AppUserKycCRUD(self.auth, self.db).get(id=id)
        if not obj:
            raise CustomException(msg="更新失败，该数据不存在")


        obj = await AppUserKycCRUD(self.auth, self.db).update(id=id, data=data)
        return AppUserKycOutSchema.model_validate(obj)

    async def review(self, id: int, data: AppUserKycReviewSchema) -> AppUserKycOutSchema:
        obj = await AppUserKycCRUD(self.auth, self.db).get(id=id)
        if not obj:
            raise CustomException(msg="审核失败，该实名认证不存在")
        if obj.status != 0:
            raise CustomException(msg="该实名认证已审核，无需重复操作")
        review_remark = data.review_remark.strip() if data.review_remark else None
        if data.status == 2 and not review_remark:
            raise CustomException(msg="驳回实名认证时必须填写审核备注")

        obj.status = data.status
        obj.review_remark = review_remark if data.status == 2 else None
        obj.reviewed_at = datetime.now(UTC)
        await self.db.flush()
        await self.db.refresh(obj)
        return AppUserKycOutSchema.model_validate(obj)

    async def delete(self, ids: list[int]) -> None:
        if not ids:
            raise CustomException(msg="删除失败，删除对象不能为空")
        objs = await AppUserKycCRUD(self.auth, self.db).get_list(search={"id": ("in", ids)})
        obj_map = {o.id: o for o in objs}
        for id_ in ids:
            if id_ not in obj_map:
                raise CustomException(msg="删除失败，该数据不存在")
        await AppUserKycCRUD(self.auth, self.db).delete(ids=ids)

    async def set_available(self, data: BatchSetAvailable) -> None:
        await AppUserKycCRUD(self.auth, self.db).set(ids=data.ids, status=data.status)

    @staticmethod
    def batch_export(obj_list: list[dict[str, Any]]) -> bytes:
        mapping_dict = {
            'app_user_id': '用户端用户ID',
            'real_name': '真实姓名',
            'id_card_no': '证件号码',
            'id_card_front': '证件正面地址',
            'id_card_back': '证件反面地址',
            'status': '状态(0待审核 1通过 2拒绝)',
            'review_remark': '审核备注',
            'reviewed_at': '审核时间',
            'id': '主键ID',
            'created_time': '创建时间',
            'updated_time': '更新时间',
        }

        data = obj_list.copy()
        for item in data:
            item["status"] = "启用" if item.get("status") == 0 else "停用"
            creator_info = item.get("created_id")
            if isinstance(creator_info, dict):
                item["created_id"] = creator_info.get("name", "未知")
            else:
                item["created_id"] = "未知"

        return ExcelUtil.export_list2excel(list_data=data, mapping_dict=mapping_dict)

    async def batch_import(self, file: UploadFile, update_support: bool = False) -> str:
        header_dict = {
            '用户端用户ID': 'app_user_id',
            '真实姓名': 'real_name',
            '证件号码': 'id_card_no',
            '证件正面地址': 'id_card_front',
            '证件反面地址': 'id_card_back',
            '状态(0待审核 1通过 2拒绝)': 'status',
            '审核备注': 'review_remark',
            '审核时间': 'reviewed_at',
        }

        try:
            contents = await file.read()
            rows = ExcelUtil.read_excel_to_dicts(contents)
            await file.close()

            if not rows:
                raise CustomException(msg="导入文件为空")

            missing_headers = [h for h in header_dict if h not in rows[0]]
            if missing_headers:
                raise CustomException(msg=f"导入文件缺少必要的列: {', '.join(missing_headers)}")

            # 将中文字段名映射为英文字段
            mapped_rows = []
            for row in rows:
                mapped_rows.append({en: row.get(ch) for ch, en in header_dict.items()})

            required_fields = [
                "app_user_id",
                "id_card_no",
                "status",
            ]
            errors = []
            for field in required_fields:
                missing_indices = [i + 1 for i, r in enumerate(mapped_rows) if r.get(field) is None]
                if missing_indices:
                    field_name = next((k for k, v in header_dict.items() if v == field), field)
                    rows_str = "、".join(str(i) for i in missing_indices)
                    errors.append(f"{field_name}不能为空，第{rows_str}行")
            if errors:
                raise CustomException(msg=f"导入失败，以下行缺少必要字段：\n{'; '.join(errors)}")

            error_msgs = []
            success_count = 0

            for i, row in enumerate(mapped_rows, start=1):
                try:
                    create_schema = AppUserKycCreateSchema.model_validate(row)


                    await AppUserKycCRUD(self.auth, self.db).create(data=create_schema)
                    success_count += 1
                except Exception as e:
                    error_msgs.append(f"第{i}行: {e!s}")
                    continue

            result = f"成功导入 {success_count} 条数据"
            if error_msgs:
                result += "\n错误信息:\n" + "\n".join(error_msgs)
            return result

        except Exception as e:
            logger.error(f"批量导入失败: {e!s}")
            raise CustomException(msg=f"导入失败: {e!s}")

    @staticmethod
    def import_template_download() -> bytes:
        header_list = [
            '用户端用户ID',
            '真实姓名',
            '证件号码',
            '证件正面地址',
            '证件反面地址',
            '状态(0待审核 1通过 2拒绝)',
            '审核备注',
            '审核时间',
        ]
        selector_header_list = []
        option_list = []


        return ExcelUtil.get_excel_template(
            header_list=header_list,
            selector_header_list=selector_header_list,
            option_list=option_list,
        )
