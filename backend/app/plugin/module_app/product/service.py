import mimetypes
import os
import tempfile
from pathlib import Path
from urllib.parse import urlparse

from fastapi import Request
from fastapi.responses import FileResponse, RedirectResponse, Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.background import BackgroundTask

from app.api.v1.module_storage.core.factory import StorageAdapterFactory
from app.api.v1.module_storage.file.service import StorageFileService
from app.common.enums import RET
from app.config.setting import settings
from app.core.base_schema import AuthSchema, PageResultSchema
from app.core.exceptions import CustomException
from app.plugin.module_product.product.constants import ProductStatus
from app.plugin.module_product.product.model import ProductModel

from .schema import AppProductDetailSchema, AppProductListItemSchema


def _delete_temp_file(path: str) -> None:
    try:
        os.unlink(path)
    except OSError:
        pass


class AppProductService:
    """Public read projection of the existing Product table."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    @staticmethod
    def _public_conditions():
        return [
            ProductModel.is_deleted.is_(False),
            ProductModel.status == ProductStatus.ON_SALE,
        ]

    @staticmethod
    def _cover_url(request: Request, product_id: int, image_url: str | None) -> str | None:
        if not image_url:
            return None
        parsed = urlparse(image_url)
        if parsed.scheme.lower() in {"http", "https", "data", "blob"}:
            return image_url
        base = str(request.base_url).rstrip("/")
        root_path = settings.ROOT_PATH.rstrip("/")
        if root_path and base.endswith(root_path):
            base = base[: -len(root_path)].rstrip("/")
        return f"{base}{root_path}/app/product/{product_id}/cover"

    @classmethod
    def _list_out(cls, request: Request, product: ProductModel) -> AppProductListItemSchema:
        return AppProductListItemSchema(
            id=product.id,
            name=product.name,
            cover_url=cls._cover_url(request, product.id, product.image_url),
            price=product.price,
            stock=product.stock,
            sold_out=product.stock <= 0,
        )

    @classmethod
    def _detail_out(cls, request: Request, product: ProductModel) -> AppProductDetailSchema:
        return AppProductDetailSchema(
            **cls._list_out(request, product).model_dump(),
            description=product.description,
        )

    async def page(
        self,
        request: Request,
        page_no: int,
        page_size: int,
        keyword: str | None = None,
    ) -> PageResultSchema[AppProductListItemSchema]:
        conditions = self._public_conditions()
        if keyword and keyword.strip():
            conditions.append(ProductModel.name.ilike(f"%{keyword.strip()}%"))
        total_result = await self.db.execute(select(func.count(ProductModel.id)).where(*conditions))
        total = int(total_result.scalar() or 0)
        result = await self.db.execute(
            select(ProductModel)
            .where(*conditions)
            .order_by(ProductModel.sort.asc(), ProductModel.id.desc())
            .offset((page_no - 1) * page_size)
            .limit(page_size)
        )
        return PageResultSchema(
            page_no=page_no,
            page_size=page_size,
            total=total,
            has_next=page_no * page_size < total,
            items=[self._list_out(request, product) for product in result.scalars().all()],
        )

    async def detail(self, request: Request, product_id: int) -> AppProductDetailSchema:
        result = await self.db.execute(
            select(ProductModel).where(ProductModel.id == product_id, *self._public_conditions())
        )
        product = result.scalar_one_or_none()
        if product is None:
            raise CustomException(msg="商品不存在或已下架", code=RET.NOT_FOUND.code, status_code=404)
        return self._detail_out(request, product)

    async def cover(self, product_id: int) -> Response:
        result = await self.db.execute(
            select(ProductModel).where(ProductModel.id == product_id, *self._public_conditions())
        )
        product = result.scalar_one_or_none()
        if product is None or not product.image_url:
            raise CustomException(msg="商品封面不存在", code=RET.NOT_FOUND.code, status_code=404)

        parsed = urlparse(product.image_url)
        if parsed.scheme.lower() in {"http", "https"}:
            return RedirectResponse(product.image_url)
        if parsed.scheme.lower() in {"data", "blob"}:
            raise CustomException(msg="商品封面不支持直接读取", code=RET.NOT_FOUND.code, status_code=404)

        remote_path = StorageFileService._validate_remote_path(product.image_url)
        auth = AuthSchema()
        config = await StorageFileService(auth, self.db)._get_source(None)
        adapter = StorageAdapterFactory.create(config)
        try:
            public_url = await adapter.get_url(remote_path)
            if public_url:
                return RedirectResponse(public_url)

            suffix = Path(remote_path).suffix
            fd, local_path = tempfile.mkstemp(suffix=suffix)
            os.close(fd)
            try:
                await adapter.download(remote_path, local_path)
            except Exception:
                _delete_temp_file(local_path)
                raise
        finally:
            await adapter.close()

        media_type = mimetypes.guess_type(remote_path)[0] or "application/octet-stream"
        return FileResponse(
            local_path,
            media_type=media_type,
            filename=Path(remote_path).name,
            background=BackgroundTask(_delete_temp_file, local_path),
        )


__all__ = ["AppProductService"]
