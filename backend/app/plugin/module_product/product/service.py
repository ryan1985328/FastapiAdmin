
from typing import Any

from fastapi import Request, UploadFile
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.module_storage.file.public_media import PublicMediaService, is_browser_url, public_media_path
from app.core.base_schema import AuthSchema, BatchSetAvailable, PageResultSchema
from app.core.exceptions import CustomException
from app.core.logger import logger
from app.utils.common_util import search_to_dict
from app.utils.excel_util import ExcelUtil
from app.utils.time_util import application_now

from .constants import ProductStatus
from .crud import ProductCRUD
from .schema import (
    ProductCreateSchema,
    ProductImageInputSchema,
    ProductImageOutSchema,
    ProductOutSchema,
    ProductQueryParam,
    ProductUpdateSchema,
)
from .model import ProductImageModel


class ProductService:
    """Product模块服务层"""

    def __init__(self, auth: AuthSchema, db: AsyncSession) -> None:
        self.auth = auth
        self.db = db

    async def _resolve_reference(self, request: Request | None, value: str | None, source_id: int | None = None) -> str | None:
        if not value:
            return None
        if is_browser_url(value):
            return value
        if value.startswith(("data:", "blob:")):
            return None
        try:
            return await PublicMediaService(self.db).url_for(value, source_id=source_id, request=request)
        except Exception:
            # A missing source should not make an otherwise valid Admin row
            # unreadable. The URL will become live once the configured source
            # is available again, while still remaining a safe public route.
            try:
                return public_media_path(value, source_id)
            except ValueError:
                return None

    async def _media_for_products(
        self,
        products: list,
        request: Request | None = None,
    ) -> dict[int, list[ProductImageOutSchema]]:
        if not products:
            return {}
        product_ids = [product.id for product in products]
        result = await self.db.execute(
            select(ProductImageModel)
            .where(
                ProductImageModel.product_id.in_(product_ids),
                ProductImageModel.is_deleted.is_(False),
            )
            .order_by(ProductImageModel.product_id.asc(), ProductImageModel.sort.asc(), ProductImageModel.id.asc())
        )
        grouped: dict[int, list[ProductImageOutSchema]] = {product_id: [] for product_id in product_ids}
        for image in result.scalars().all():
            grouped[image.product_id].append(
                ProductImageOutSchema(
                    id=image.id,
                    storage_key=image.storage_key,
                    source_id=image.source_id,
                    sort=image.sort,
                    url=await self._resolve_reference(request, image.storage_key, image.source_id),
                )
            )

        for product in products:
            if grouped[product.id] or not product.image_url:
                continue
            grouped[product.id].append(
                ProductImageOutSchema(
                    id=None,
                    storage_key=None,
                    source_id=None,
                    sort=0,
                    url=await self._resolve_reference(request, product.image_url),
                    legacy=True,
                )
            )
        return grouped

    async def _to_out(self, obj, request: Request | None = None) -> ProductOutSchema:
        media = await self._media_for_products([obj], request=request)
        out = ProductOutSchema.model_validate(obj)
        out.images = media.get(obj.id, [])
        out.cover_url = out.images[0].url if out.images else None
        return out

    async def detail(self, id: int, request: Request | None = None) -> ProductOutSchema:
        obj = await ProductCRUD(self.auth, self.db).get(id=id)
        if not obj:
            raise CustomException(msg="该数据不存在")
        return await self._to_out(obj, request=request)

    async def get_list(
        self,
        search: ProductQueryParam | None = None,
        order_by: list[dict[str, str]] | None = None,
        request: Request | None = None,
    ) -> list[ProductOutSchema]:
        obj_list = await ProductCRUD(self.auth, self.db).get_list(search=search_to_dict(search), order_by=order_by)
        objects = list(obj_list)
        media = await self._media_for_products(objects, request=request)
        outputs: list[ProductOutSchema] = []
        for obj in objects:
            output = ProductOutSchema.model_validate(obj)
            output.images = media.get(obj.id, [])
            output.cover_url = output.images[0].url if output.images else None
            outputs.append(output)
        return outputs

    async def page(
        self,
        page_no: int,
        page_size: int,
        search: ProductQueryParam | None = None,
        order_by: list[dict[str, str]] | None = None,
        request: Request | None = None,
    ) -> PageResultSchema[ProductOutSchema]:
        offset = (page_no - 1) * page_size
        result = await ProductCRUD(self.auth, self.db).page(
            offset=offset,
            limit=page_size,
            order_by=order_by or [{"sort": "asc"}, {"id": "asc"}],
            search=search_to_dict(search, {}),
            out_schema=None,
        )
        objects = list(result.items)
        media = await self._media_for_products(objects, request=request)
        outputs: list[ProductOutSchema] = []
        for obj in objects:
            output = ProductOutSchema.model_validate(obj)
            output.images = media.get(obj.id, [])
            output.cover_url = output.images[0].url if output.images else None
            outputs.append(output)
        return PageResultSchema(
            page_no=result.page_no,
            page_size=result.page_size,
            total=result.total,
            has_next=result.has_next,
            items=outputs,
        )

    async def _sync_images(self, product_id: int, images: list[ProductImageInputSchema]) -> None:
        """Reconcile ordered associations without deleting storage objects."""

        result = await self.db.execute(
            select(ProductImageModel)
            .where(ProductImageModel.product_id == product_id)
            .order_by(ProductImageModel.sort.asc(), ProductImageModel.id.asc())
        )
        existing = list(result.scalars().all())
        by_id = {image.id: image for image in existing}
        by_key = {(image.source_id, image.storage_key): image for image in existing}
        foreign_ids = sorted({image.id for image in images if image.id and image.id not in by_id})
        if foreign_ids:
            raise CustomException(msg="商品图片关联不存在或不属于当前商品", status_code=409)
        kept_ids: set[int] = set()

        for position, image_data in enumerate(images):
            image = by_id.get(image_data.id) if image_data.id else None
            if image is None:
                image = by_key.get((image_data.source_id, image_data.storage_key))
            if image is None:
                image = ProductImageModel(
                    product_id=product_id,
                    storage_key=image_data.storage_key,
                    source_id=image_data.source_id,
                    sort=position,
                    created_id=self.auth.user.id or None,
                    updated_id=self.auth.user.id or None,
                )
                self.db.add(image)
            else:
                image.storage_key = image_data.storage_key
                image.source_id = image_data.source_id
                image.sort = position
                image.is_deleted = False
                image.deleted_time = None
                image.deleted_id = None
                image.updated_id = self.auth.user.id or None
            await self.db.flush()
            kept_ids.add(image.id)

        for image in existing:
            if image.id in kept_ids or image.is_deleted:
                continue
            image.is_deleted = True
            image.deleted_time = application_now()
            image.deleted_id = self.auth.user.id or None
            image.updated_id = self.auth.user.id or None
        await self.db.flush()

    async def create(self, data: ProductCreateSchema, request: Request | None = None) -> ProductOutSchema:
        obj = await ProductCRUD(self.auth, self.db).get(code=data.code)
        if obj:
            raise CustomException(msg="创建失败，编码已存在")
        payload = data.model_dump(exclude={"images"}, exclude_none=True)
        obj = await ProductCRUD(self.auth, self.db).create(data=payload)
        if data.images:
            await self._sync_images(obj.id, data.images)
            obj.image_url = None
            await self.db.flush()
        return await self._to_out(obj, request=request)

    async def update(self, id: int, data: ProductUpdateSchema, request: Request | None = None) -> ProductOutSchema:
        crud = ProductCRUD(self.auth, self.db)
        obj = await crud.get(id=id)
        if not obj:
            raise CustomException(msg="更新失败，该数据不存在")

        if data.code is not None:
            exist_obj = await crud.get(code=data.code)
            if exist_obj and exist_obj.id != id:
                raise CustomException(msg="更新失败，编码重复")

        payload = data.model_dump(exclude_unset=True, exclude={"images"})
        obj = await crud.update(id=id, data=payload)
        if data.images is not None:
            await self._sync_images(obj.id, data.images)
            if data.images:
                obj.image_url = None
                await self.db.flush()
        return await self._to_out(obj, request=request)

    async def delete(self, ids: list[int]) -> None:
        if not ids:
            raise CustomException(msg="删除失败，删除对象不能为空")
        objs = await ProductCRUD(self.auth, self.db).get_list(search={"id": ("in", ids)})
        obj_map = {o.id: o for o in objs}
        for id_ in ids:
            if id_ not in obj_map:
                raise CustomException(msg="删除失败，该数据不存在")

        # Product rows are historical references once an order has been
        # created.  A pending/paid order blocks even a soft delete; a
        # cancelled order does not.  The Product CRUD still owns the actual
        # soft-delete operation below.
        from app.plugin.module_product.order.model import ProductOrderItemModel, ProductOrderModel

        referenced = await self.db.execute(
            select(ProductOrderItemModel.id)
            .join(ProductOrderModel, ProductOrderModel.id == ProductOrderItemModel.order_id)
            .where(
                ProductOrderItemModel.product_id.in_(ids),
                ProductOrderItemModel.is_deleted.is_(False),
                ProductOrderModel.is_deleted.is_(False),
                ProductOrderModel.status != "CANCELLED",
            )
            .limit(1)
        )
        if referenced.scalar_one_or_none() is not None:
            raise CustomException(msg="商品已被未取消订单引用，无法删除", status_code=409)
        await ProductCRUD(self.auth, self.db).delete(ids=ids)
        await self.db.execute(
            update(ProductImageModel)
            .where(ProductImageModel.product_id.in_(ids), ProductImageModel.is_deleted.is_(False))
            .values(
                is_deleted=True,
                deleted_time=application_now(),
                deleted_id=self.auth.user.id or None,
                updated_id=self.auth.user.id or None,
            )
        )
        await self.db.flush()

    async def set_available(self, data: BatchSetAvailable) -> None:
        await ProductCRUD(self.auth, self.db).set(ids=data.ids, status=data.status)

    @staticmethod
    def batch_export(obj_list: list[dict[str, Any]]) -> bytes:
        mapping_dict = {
            'id': '主键ID',
            'created_time': '创建时间',
            'updated_time': '更新时间',
            'created_id': '创建人',
            'name': '名称',
            'code': '编码',
            'description': '描述',
            'image_url': '图片',
            'price': '价格',
            'stock': '库存',
            'status': '状态',
            'sort': '排序',
            'remark': '备注',
        }

        data = obj_list.copy()
        for item in data:
            item["status"] = "上架" if item.get("status") == ProductStatus.ON_SALE else "下架"
            creator_info = item.get("created_id")
            if isinstance(creator_info, dict):
                item["created_id"] = creator_info.get("name", "未知")
            else:
                item["created_id"] = "未知"

        return ExcelUtil.export_list2excel(list_data=data, mapping_dict=mapping_dict)

    async def batch_import(self, file: UploadFile, update_support: bool = False) -> str:
        header_dict = {
            '名称': 'name',
            '编码': 'code',
            '描述': 'description',
            '图片': 'image_url',
            '价格': 'price',
            '库存': 'stock',
            '状态': 'status',
            '排序': 'sort',
            '备注': 'remark',
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

            required_fields = ["name", "code"]
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
                    create_schema = ProductCreateSchema.model_validate(row)

                    exists_obj = await ProductCRUD(self.auth, self.db).get(code=create_schema.code)
                    if exists_obj:
                        if update_support:
                            await ProductCRUD(self.auth, self.db).update(id=getattr(exists_obj, 'id'), data=create_schema)
                            success_count += 1
                        else:
                            error_msgs.append(f"第{i}行: 编码 {create_schema.code} 已存在")
                        continue

                    await ProductCRUD(self.auth, self.db).create(data=create_schema)
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
            '名称',
            '编码',
            '描述',
            '图片',
            '价格',
            '库存',
            '状态',
            '排序',
            '备注',
        ]
        selector_header_list = []
        option_list = []


        return ExcelUtil.get_excel_template(
            header_list=header_list,
            selector_header_list=selector_header_list,
            option_list=option_list,
        )
