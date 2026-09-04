from decimal import ROUND_HALF_UP, Decimal
from uuid import uuid4

from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.base_schema import PageResultSchema
from app.core.exceptions import CustomException
from app.plugin.module_app.user.model import AppUserModel
from app.plugin.module_product.product.constants import ProductStatus
from app.plugin.module_product.product.model import ProductModel
from app.utils.time_util import application_now

from .constants import ProductOrderStatus
from .model import ProductOrderItemModel, ProductOrderModel
from .schema import (
    AppOrderCreateSchema,
    AppOrderItemSchema,
    AppOrderSchema,
    ProductOrderAdminDetailSchema,
    ProductOrderAdminItemDetailSchema,
    ProductOrderAdminItemSchema,
    ProductOrderQueryParam,
)

_MONEY_QUANTUM = Decimal("0.01")


def _money(value: Decimal) -> Decimal:
    return Decimal(value).quantize(_MONEY_QUANTUM, rounding=ROUND_HALF_UP)


class ProductOrderService:
    """Shared order application service for App actions and Admin reads."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    @staticmethod
    def _new_order_no() -> str:
        return f"MM{uuid4().hex}"

    @staticmethod
    def _app_item(item: ProductOrderItemModel) -> AppOrderItemSchema:
        return AppOrderItemSchema(
            id=item.id,
            product_id=item.product_id,
            product_name=item.product_name_snapshot,
            product_cover=item.product_cover_snapshot,
            unit_price=item.unit_price,
            quantity=item.quantity,
            subtotal=item.subtotal,
        )

    @classmethod
    def _app_out(cls, order: ProductOrderModel) -> AppOrderSchema:
        return AppOrderSchema(
            id=order.id,
            order_no=order.order_no,
            total_amount=order.total_amount,
            status=ProductOrderStatus(order.status),
            created_time=order.created_time,
            updated_time=order.updated_time,
            paid_time=order.paid_time,
            cancelled_time=order.cancelled_time,
            items=[cls._app_item(item) for item in order.items if not item.is_deleted],
        )

    @staticmethod
    def _admin_item_detail(item: ProductOrderItemModel) -> ProductOrderAdminItemDetailSchema:
        return ProductOrderAdminItemDetailSchema(
            id=item.id,
            product_id=item.product_id,
            product_name=item.product_name_snapshot,
            product_cover=item.product_cover_snapshot,
            unit_price=item.unit_price,
            quantity=item.quantity,
            subtotal=item.subtotal,
        )

    @classmethod
    def _admin_list_out(cls, order: ProductOrderModel, user: AppUserModel) -> ProductOrderAdminItemSchema:
        item = next((item for item in order.items if not item.is_deleted), None)
        return ProductOrderAdminItemSchema(
            id=order.id,
            uuid=order.uuid,
            created_time=order.created_time,
            updated_time=order.updated_time,
            is_deleted=order.is_deleted,
            deleted_time=order.deleted_time,
            order_no=order.order_no,
            user_id=order.user_id,
            username=user.username,
            nickname=user.nickname,
            mobile=user.mobile,
            product_id=item.product_id if item else None,
            product_name=item.product_name_snapshot if item else None,
            quantity=item.quantity if item else None,
            total_amount=order.total_amount,
            status=ProductOrderStatus(order.status),
            paid_time=order.paid_time,
            cancelled_time=order.cancelled_time,
        )

    @classmethod
    def _admin_detail_out(cls, order: ProductOrderModel, user: AppUserModel) -> ProductOrderAdminDetailSchema:
        return ProductOrderAdminDetailSchema(
            id=order.id,
            uuid=order.uuid,
            created_time=order.created_time,
            updated_time=order.updated_time,
            is_deleted=order.is_deleted,
            deleted_time=order.deleted_time,
            user_id=order.user_id,
            username=user.username,
            nickname=user.nickname,
            mobile=user.mobile,
            order_no=order.order_no,
            total_amount=order.total_amount,
            status=ProductOrderStatus(order.status),
            paid_time=order.paid_time,
            cancelled_time=order.cancelled_time,
            items=[cls._admin_item_detail(item) for item in order.items if not item.is_deleted],
        )

    async def create(self, user_id: int, data: AppOrderCreateSchema) -> AppOrderSchema:
        product_result = await self.db.execute(
            select(ProductModel).where(
                ProductModel.id == data.product_id,
                ProductModel.is_deleted.is_(False),
                ProductModel.status == ProductStatus.ON_SALE,
            )
        )
        product = product_result.scalar_one_or_none()
        if product is None:
            raise CustomException(msg="商品不存在或已下架", status_code=409)

        unit_price = _money(product.price)
        subtotal = _money(unit_price * data.quantity)
        order = ProductOrderModel(
            order_no=self._new_order_no(),
            user_id=user_id,
            total_amount=subtotal,
            status=ProductOrderStatus.PENDING_PAYMENT.value,
            items=[
                ProductOrderItemModel(
                    product_id=product.id,
                    product_name_snapshot=product.name,
                    product_cover_snapshot=product.image_url,
                    unit_price=unit_price,
                    quantity=data.quantity,
                    subtotal=subtotal,
                )
            ],
        )
        self.db.add(order)
        await self.db.flush()
        return self._app_out(order)

    async def _get_owned(self, user_id: int, order_id: int, *, lock: bool = False) -> ProductOrderModel:
        query = (
            select(ProductOrderModel)
            .where(
                ProductOrderModel.id == order_id,
                ProductOrderModel.user_id == user_id,
                ProductOrderModel.is_deleted.is_(False),
            )
            .options(selectinload(ProductOrderModel.items))
        )
        if lock:
            query = query.with_for_update()
        result = await self.db.execute(query)
        order = result.scalars().first()
        if order is None:
            raise CustomException(msg="订单不存在", status_code=404)
        return order

    async def list_owned(self, user_id: int, page_no: int, page_size: int) -> PageResultSchema[AppOrderSchema]:
        conditions = [ProductOrderModel.user_id == user_id, ProductOrderModel.is_deleted.is_(False)]
        total_result = await self.db.execute(select(func.count(ProductOrderModel.id)).where(*conditions))
        total = int(total_result.scalar() or 0)
        result = await self.db.execute(
            select(ProductOrderModel)
            .where(*conditions)
            .options(selectinload(ProductOrderModel.items))
            .order_by(ProductOrderModel.created_time.desc(), ProductOrderModel.id.desc())
            .offset((page_no - 1) * page_size)
            .limit(page_size)
        )
        return PageResultSchema(
            page_no=page_no,
            page_size=page_size,
            total=total,
            has_next=page_no * page_size < total,
            items=[self._app_out(order) for order in result.scalars().all()],
        )

    async def detail_owned(self, user_id: int, order_id: int) -> AppOrderSchema:
        return self._app_out(await self._get_owned(user_id, order_id))

    async def pay(self, user_id: int, order_id: int) -> AppOrderSchema:
        order = await self._get_owned(user_id, order_id, lock=True)
        if order.status == ProductOrderStatus.PAID.value:
            return self._app_out(order)
        if order.status == ProductOrderStatus.CANCELLED.value:
            raise CustomException(msg="已取消订单不能支付", status_code=409)

        item = next((item for item in order.items if not item.is_deleted), None)
        if item is None or item.product_id is None:
            raise CustomException(msg="订单商品已不可用，无法支付", status_code=409)

        # The conditional UPDATE is the inventory reservation boundary: it
        # atomically checks sale status, deletion state, and stock without
        # maintaining a second Redis inventory ledger.
        stock_result = await self.db.execute(
            update(ProductModel)
            .where(
                ProductModel.id == item.product_id,
                ProductModel.is_deleted.is_(False),
                ProductModel.status == ProductStatus.ON_SALE,
                ProductModel.stock >= item.quantity,
            )
            .values(stock=ProductModel.stock - item.quantity)
        )
        if stock_result.rowcount != 1:
            raise CustomException(msg="库存不足或商品已下架", status_code=409)

        order.status = ProductOrderStatus.PAID.value
        order.paid_time = application_now()
        await self.db.flush()
        return self._app_out(order)

    async def cancel(self, user_id: int, order_id: int) -> AppOrderSchema:
        order = await self._get_owned(user_id, order_id, lock=True)
        if order.status == ProductOrderStatus.CANCELLED.value:
            return self._app_out(order)
        if order.status == ProductOrderStatus.PAID.value:
            raise CustomException(msg="已支付订单不能取消", status_code=409)

        order.status = ProductOrderStatus.CANCELLED.value
        order.cancelled_time = application_now()
        await self.db.flush()
        return self._app_out(order)

    async def admin_page(
        self,
        search: ProductOrderQueryParam | None,
        page_no: int,
        page_size: int,
    ) -> PageResultSchema[ProductOrderAdminItemSchema]:
        conditions = [ProductOrderModel.is_deleted.is_(False), AppUserModel.is_deleted.is_(False)]
        if search:
            if search.status is not None:
                conditions.append(ProductOrderModel.status == search.status.value)
            if search.user_id is not None:
                conditions.append(ProductOrderModel.user_id == search.user_id)
            if search.created_time and len(search.created_time) == 2:
                conditions.append(ProductOrderModel.created_time.between(*search.created_time))
            if search.updated_time and len(search.updated_time) == 2:
                conditions.append(ProductOrderModel.updated_time.between(*search.updated_time))
            if search.keyword:
                keyword = f"%{search.keyword.strip()}%"
                conditions.append(
                    or_(
                        ProductOrderModel.order_no.ilike(keyword),
                        AppUserModel.username.ilike(keyword),
                        AppUserModel.nickname.ilike(keyword),
                        AppUserModel.mobile.ilike(keyword),
                        ProductOrderItemModel.product_name_snapshot.ilike(keyword),
                    )
                )

        from_clause = (
            ProductOrderModel.__table__
            .join(AppUserModel, ProductOrderModel.user_id == AppUserModel.id)
            .outerjoin(
                ProductOrderItemModel,
                (ProductOrderItemModel.order_id == ProductOrderModel.id)
                & ProductOrderItemModel.is_deleted.is_(False),
            )
        )
        total_result = await self.db.execute(
            select(func.count(ProductOrderModel.id.distinct())).select_from(from_clause).where(*conditions)
        )
        total = int(total_result.scalar() or 0)
        result = await self.db.execute(
            select(ProductOrderModel, AppUserModel)
            .select_from(from_clause)
            .where(*conditions)
            .options(selectinload(ProductOrderModel.items))
            .distinct()
            .order_by(ProductOrderModel.created_time.desc(), ProductOrderModel.id.desc())
            .offset((page_no - 1) * page_size)
            .limit(page_size)
        )
        items = [self._admin_list_out(order, user) for order, user in result.unique().all()]
        return PageResultSchema(
            page_no=page_no,
            page_size=page_size,
            total=total,
            has_next=page_no * page_size < total,
            items=items,
        )

    async def admin_detail(self, order_id: int) -> ProductOrderAdminDetailSchema:
        result = await self.db.execute(
            select(ProductOrderModel, AppUserModel)
            .join(AppUserModel, ProductOrderModel.user_id == AppUserModel.id)
            .where(ProductOrderModel.id == order_id, ProductOrderModel.is_deleted.is_(False))
            .options(selectinload(ProductOrderModel.items))
        )
        row = result.unique().first()
        if row is None:
            raise CustomException(msg="订单不存在", status_code=404)
        order, user = row
        return self._admin_detail_out(order, user)


__all__ = ["ProductOrderService"]
