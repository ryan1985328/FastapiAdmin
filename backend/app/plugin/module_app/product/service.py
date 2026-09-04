from __future__ import annotations

from fastapi import Request
from fastapi.responses import RedirectResponse, Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.module_storage.file.public_media import (
    PublicMediaService,
    is_browser_url,
    normalize_public_storage_key,
    public_media_path,
)
from app.common.enums import RET
from app.config.setting import settings
from app.core.base_schema import PageResultSchema
from app.core.exceptions import CustomException
from app.plugin.module_product.product.constants import ProductStatus
from app.plugin.module_product.product.model import ProductImageModel, ProductModel

from .schema import AppProductDetailSchema, AppProductImageSchema, AppProductListItemSchema


class AppProductService:
    """Public read projection of on-sale Products and their ordered media."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    @staticmethod
    def _public_conditions():
        return [
            ProductModel.is_deleted.is_(False),
            ProductModel.status == ProductStatus.ON_SALE,
        ]

    async def _resolve_reference(
        self,
        request: Request,
        value: str | None,
        source_id: int | None = None,
    ) -> str | None:
        if not value:
            return None
        if is_browser_url(value):
            return value
        if value.startswith(("data:", "blob:")):
            return None
        try:
            return await PublicMediaService(self.db).url_for(value, source_id=source_id, request=request)
        except Exception:
            # Invalid legacy values are hidden from the public projection;
            # they must never become an arbitrary file read.
            try:
                return public_media_path(value, source_id)
            except Exception:
                return None

    async def _images_for_products(
        self,
        request: Request,
        products: list[ProductModel],
    ) -> tuple[dict[int, list[AppProductImageSchema]], set[int]]:
        if not products:
            return {}, set()

        product_ids = [product.id for product in products]
        result = await self.db.execute(
            select(ProductImageModel)
            .where(
                ProductImageModel.product_id.in_(product_ids),
                ProductImageModel.is_deleted.is_(False),
            )
            .order_by(ProductImageModel.product_id.asc(), ProductImageModel.sort.asc(), ProductImageModel.id.asc())
        )
        grouped: dict[int, list[AppProductImageSchema]] = {product_id: [] for product_id in product_ids}
        associated_product_ids: set[int] = set()
        for image in result.scalars().all():
            associated_product_ids.add(image.product_id)
            url = await self._resolve_reference(request, image.storage_key, image.source_id)
            if url:
                grouped[image.product_id].append(AppProductImageSchema(url=url, sort=image.sort))

        for product in products:
            if grouped[product.id] or not product.image_url:
                continue
            url = await self._resolve_reference(request, product.image_url)
            if url:
                grouped[product.id].append(AppProductImageSchema(url=url, sort=0))
        return grouped, associated_product_ids

    @staticmethod
    def _legacy_cover_url(request: Request, product_id: int, image_url: str | None) -> str | None:
        if not image_url:
            return None
        if is_browser_url(image_url):
            return image_url
        if image_url.startswith(("data:", "blob:")):
            return None
        try:
            normalize_public_storage_key(image_url)
        except Exception:
            return None
        base = str(request.base_url).rstrip("/")
        root = settings.ROOT_PATH.rstrip("/")
        if root and base.endswith(root):
            base = base[: -len(root)].rstrip("/")
        return f"{base}{root}/app/product/{product_id}/cover"

    @staticmethod
    def _list_out(
        product: ProductModel,
        images: list[AppProductImageSchema],
    ) -> AppProductListItemSchema:
        return AppProductListItemSchema(
            id=product.id,
            name=product.name,
            cover_url=images[0].url if images else None,
            images=images,
            price=product.price,
            stock=product.stock,
            sold_out=product.stock <= 0,
        )

    async def _outputs(
        self,
        request: Request,
        products: list[ProductModel],
        *,
        detail: bool = False,
    ) -> list[AppProductListItemSchema | AppProductDetailSchema]:
        images, associated_product_ids = await self._images_for_products(request, products)
        outputs: list[AppProductListItemSchema | AppProductDetailSchema] = []
        for product in products:
            product_images = images.get(product.id, [])
            cover_url = product_images[0].url if product_images else None
            if product.id not in associated_product_ids:
                cover_url = self._legacy_cover_url(request, product.id, product.image_url)
            item = self._list_out(product, product_images)
            item.cover_url = cover_url
            if detail:
                outputs.append(AppProductDetailSchema(**item.model_dump(), description=product.description))
            else:
                outputs.append(item)
        return outputs

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
        products = list(result.scalars().all())
        outputs = await self._outputs(request, products)
        return PageResultSchema(
            page_no=page_no,
            page_size=page_size,
            total=total,
            has_next=page_no * page_size < total,
            items=outputs,
        )

    async def detail(self, request: Request, product_id: int) -> AppProductDetailSchema:
        result = await self.db.execute(
            select(ProductModel).where(ProductModel.id == product_id, *self._public_conditions())
        )
        product = result.scalar_one_or_none()
        if product is None:
            raise CustomException(msg="商品不存在或已下架", code=RET.NOT_FOUND.code, status_code=404)
        return (await self._outputs(request, [product], detail=True))[0]  # type: ignore[return-value]

    async def cover(self, product_id: int) -> Response:
        result = await self.db.execute(
            select(ProductModel).where(ProductModel.id == product_id, *self._public_conditions())
        )
        product = result.scalar_one_or_none()
        if product is None:
            raise CustomException(msg="商品封面不存在", code=RET.NOT_FOUND.code, status_code=404)

        image_result = await self.db.execute(
            select(ProductImageModel)
            .where(
                ProductImageModel.product_id == product_id,
                ProductImageModel.is_deleted.is_(False),
            )
            .order_by(ProductImageModel.sort.asc(), ProductImageModel.id.asc())
            .limit(1)
        )
        image = image_result.scalar_one_or_none()
        if image:
            return await PublicMediaService(self.db).response(image.storage_key, image.source_id)

        if not product.image_url:
            raise CustomException(msg="商品封面不存在", code=RET.NOT_FOUND.code, status_code=404)
        if is_browser_url(product.image_url):
            return RedirectResponse(product.image_url)
        if product.image_url.startswith(("data:", "blob:")):
            raise CustomException(msg="商品封面不存在", code=RET.NOT_FOUND.code, status_code=404)
        return await PublicMediaService(self.db).response(product.image_url)


__all__ = ["AppProductService"]
