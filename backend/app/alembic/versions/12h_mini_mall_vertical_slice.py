"""Add the Mini Mall V1 order aggregate and reconcile its Admin menu."""

from datetime import UTC, datetime
from uuid import uuid4

import sqlalchemy as sa
from alembic import op

revision = "12h_mini_mall_vertical_slice"
down_revision = "12g_sms_settings_productization"
branch_labels = None
depends_on = None

_ORDER_TABLE = "product_order"
_ITEM_TABLE = "product_order_item"
_ORDER_QUERY_PERMISSION = "module_product:order:query"
_ORDER_DETAIL_PERMISSION = "module_product:order:detail"


def _menu_table() -> sa.TableClause:
    return sa.table(
        "sys_menu",
        sa.column("id", sa.Integer()),
        sa.column("parent_id", sa.Integer()),
        sa.column("name", sa.String(length=64)),
        sa.column("type", sa.Integer()),
        sa.column("order", sa.Integer()),
        sa.column("permission", sa.String(length=100)),
        sa.column("icon", sa.String(length=50)),
        sa.column("route_name", sa.String(length=100)),
        sa.column("route_path", sa.String(length=200)),
        sa.column("component_path", sa.String(length=200)),
        sa.column("redirect", sa.String(length=200)),
        sa.column("hidden", sa.Boolean()),
        sa.column("keep_alive", sa.Boolean()),
        sa.column("always_show", sa.Boolean()),
        sa.column("title", sa.String(length=50)),
        sa.column("params", sa.JSON()),
        sa.column("affix", sa.Boolean()),
        sa.column("link", sa.String(length=500)),
        sa.column("is_iframe", sa.Boolean()),
        sa.column("is_hide_tab", sa.Boolean()),
        sa.column("active_path", sa.String(length=200)),
        sa.column("show_badge", sa.Boolean()),
        sa.column("show_text_badge", sa.String(length=20)),
        sa.column("scope", sa.String(length=20)),
        sa.column("status", sa.Integer()),
        sa.column("description", sa.Text()),
        sa.column("is_deleted", sa.Boolean()),
        sa.column("uuid", sa.String(length=64)),
        sa.column("created_time", sa.DateTime(timezone=True)),
        sa.column("updated_time", sa.DateTime(timezone=True)),
        sa.column("deleted_time", sa.DateTime(timezone=True)),
    )


def _active_id(bind, table: sa.TableClause, *conditions: sa.ColumnElement[bool]) -> int | None:
    result = bind.execute(
        sa.select(table.c.id).where(*conditions, table.c.is_deleted.is_(False)).order_by(table.c.id.asc()).limit(1)
    ).scalar_one_or_none()
    return int(result) if result is not None else None


def _insert_menu(
    bind,
    table: sa.TableClause,
    *,
    parent_id: int,
    name: str,
    menu_type: int,
    order: int,
    permission: str | None = None,
    icon: str | None = None,
    route_name: str | None = None,
    route_path: str | None = None,
    component_path: str | None = None,
    description: str = "",
) -> int:
    now = datetime.now(UTC)
    menu_uuid = str(uuid4())
    bind.execute(
        table.insert().values(
            parent_id=parent_id,
            name=name,
            type=menu_type,
            order=order,
            permission=permission,
            icon=icon,
            route_name=route_name,
            route_path=route_path,
            component_path=component_path,
            redirect=None,
            hidden=False,
            keep_alive=True,
            always_show=False,
            title=name,
            params=None,
            affix=False,
            link=None,
            is_iframe=False,
            is_hide_tab=False,
            active_path=None,
            show_badge=False,
            show_text_badge=None,
            scope="web",
            status=0,
            description=description,
            is_deleted=False,
            uuid=menu_uuid,
            created_time=now,
            updated_time=now,
            deleted_time=None,
        )
    )
    return int(bind.execute(sa.select(table.c.id).where(table.c.uuid == menu_uuid)).scalar_one())


def _ensure_order_action(bind, table: sa.TableClause, *, page_id: int, name: str, order: int, permission: str, description: str) -> None:
    action_id = _active_id(bind, table, table.c.type == 3, table.c.permission == permission)
    values = {
        "parent_id": page_id,
        "name": name,
        "type": 3,
        "order": order,
        "permission": permission,
        "icon": None,
        "route_name": None,
        "route_path": None,
        "component_path": None,
        "redirect": None,
        "description": description,
    }
    if action_id is None:
        _insert_menu(bind, table, parent_id=page_id, name=name, menu_type=3, order=order, permission=permission, description=description)
        return
    bind.execute(
        table.update()
        .where(table.c.id == action_id)
        .values(
            **values,
            title=name,
            status=0,
            scope="web",
            is_deleted=False,
            deleted_time=None,
            updated_time=datetime.now(UTC),
        )
    )


def _reconcile_mall_menu(bind) -> None:
    if "sys_menu" not in sa.inspect(bind).get_table_names():
        return

    menu = _menu_table()
    root_id = _active_id(bind, menu, menu.c.type == 1, menu.c.route_path.in_(["/product", "product"]), menu.c.route_name.in_(["BusinessExample", "Mall"]))
    if root_id is None:
        return

    bind.execute(
        menu.update()
        .where(menu.c.id == root_id)
        .values(
            name="商城管理",
            title="商城管理",
            redirect="/product/product",
            description="商城商品与订单管理",
            status=0,
            scope="web",
            updated_time=datetime.now(UTC),
        )
    )

    product_id = _active_id(bind, menu, menu.c.parent_id == root_id, menu.c.type == 2, menu.c.route_name == "Product")
    if product_id is None:
        product_id = _active_id(bind, menu, menu.c.parent_id == root_id, menu.c.type == 2, menu.c.permission == "module_product:product:query")
    if product_id is None:
        return

    bind.execute(
        menu.update()
        .where(menu.c.id == product_id)
        .values(
            parent_id=root_id,
            name="商品管理",
            title="商品管理",
            type=2,
            route_name="Product",
            route_path="product",
            component_path="module_product/product/index",
            status=0,
            scope="web",
            is_deleted=False,
            deleted_time=None,
            description="商城商品管理",
            updated_time=datetime.now(UTC),
        )
    )

    order_id = _active_id(bind, menu, menu.c.parent_id == root_id, menu.c.type == 2, menu.c.permission == _ORDER_QUERY_PERMISSION)
    if order_id is None:
        order_id = _insert_menu(
            bind,
            menu,
            parent_id=root_id,
            name="订单管理",
            menu_type=2,
            order=2,
            permission=_ORDER_QUERY_PERMISSION,
            icon="ri:receipt-line",
            route_name="ProductOrder",
            route_path="order",
            component_path="module_product/order/index",
            description="商城订单只读查询",
        )
    else:
        bind.execute(
            menu.update()
            .where(menu.c.id == order_id)
            .values(
                parent_id=root_id,
                name="订单管理",
                title="订单管理",
                type=2,
                order=2,
                permission=_ORDER_QUERY_PERMISSION,
                icon="ri:receipt-line",
                route_name="ProductOrder",
                route_path="order",
                component_path="module_product/order/index",
                status=0,
                scope="web",
                is_deleted=False,
                deleted_time=None,
                description="商城订单只读查询",
                updated_time=datetime.now(UTC),
            )
        )

    _ensure_order_action(bind, menu, page_id=order_id, name="查询", order=1, permission=_ORDER_QUERY_PERMISSION, description="查询商城订单")
    _ensure_order_action(bind, menu, page_id=order_id, name="详情", order=2, permission=_ORDER_DETAIL_PERMISSION, description="查看商城订单详情")


def _create_order_tables(bind) -> None:
    table_names = set(sa.inspect(bind).get_table_names())
    if _ORDER_TABLE not in table_names:
        op.create_table(
            _ORDER_TABLE,
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False, comment="主键ID"),
            sa.Column("uuid", sa.String(length=64), nullable=False, comment="UUID全局唯一标识"),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false(), comment="是否已删除"),
            sa.Column("created_time", sa.DateTime(timezone=True), nullable=False, comment="创建时间"),
            sa.Column("updated_time", sa.DateTime(timezone=True), nullable=False, comment="更新时间"),
            sa.Column("deleted_time", sa.DateTime(timezone=True), nullable=True, comment="删除时间"),
            sa.Column("order_no", sa.String(length=40), nullable=False, comment="订单号"),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("app_user.id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False, comment="App用户ID"),
            sa.Column("total_amount", sa.Numeric(12, 2), nullable=False, comment="订单总金额"),
            sa.Column("status", sa.String(length=32), nullable=False, server_default="PENDING_PAYMENT", comment="订单状态"),
            sa.Column("paid_time", sa.DateTime(timezone=True), nullable=True, comment="支付时间"),
            sa.Column("cancelled_time", sa.DateTime(timezone=True), nullable=True, comment="取消时间"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("uuid"),
            sa.UniqueConstraint("order_no"),
            comment="商城订单",
        )
        for name, columns in (
            ("ix_product_order_id", ["id"]),
            ("ix_product_order_uuid", ["uuid"]),
            ("ix_product_order_is_deleted", ["is_deleted"]),
            ("ix_product_order_created_time", ["created_time"]),
            ("ix_product_order_order_no", ["order_no"]),
            ("ix_product_order_user_id", ["user_id"]),
            ("ix_product_order_status", ["status"]),
            ("ix_product_order_user_status_deleted", ["user_id", "status", "is_deleted"]),
            ("ix_product_order_user_created_deleted", ["user_id", "created_time", "is_deleted"]),
        ):
            op.create_index(name, _ORDER_TABLE, columns, unique=False)

    table_names = set(sa.inspect(bind).get_table_names())
    if _ITEM_TABLE not in table_names:
        op.create_table(
            _ITEM_TABLE,
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False, comment="主键ID"),
            sa.Column("uuid", sa.String(length=64), nullable=False, comment="UUID全局唯一标识"),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false(), comment="是否已删除"),
            sa.Column("created_time", sa.DateTime(timezone=True), nullable=False, comment="创建时间"),
            sa.Column("updated_time", sa.DateTime(timezone=True), nullable=False, comment="更新时间"),
            sa.Column("deleted_time", sa.DateTime(timezone=True), nullable=True, comment="删除时间"),
            sa.Column("order_id", sa.Integer(), sa.ForeignKey("product_order.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False, comment="订单ID"),
            sa.Column("product_id", sa.Integer(), sa.ForeignKey("product.id", ondelete="SET NULL", onupdate="CASCADE"), nullable=True, comment="商品ID"),
            sa.Column("product_name_snapshot", sa.String(length=128), nullable=False, comment="商品名称快照"),
            sa.Column("product_cover_snapshot", sa.String(length=512), nullable=True, comment="商品封面快照"),
            sa.Column("unit_price", sa.Numeric(12, 2), nullable=False, comment="成交单价快照"),
            sa.Column("quantity", sa.Integer(), nullable=False, comment="购买数量"),
            sa.Column("subtotal", sa.Numeric(12, 2), nullable=False, comment="商品小计"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("uuid"),
            comment="商城订单商品快照",
        )
        for name, columns in (
            ("ix_product_order_item_id", ["id"]),
            ("ix_product_order_item_uuid", ["uuid"]),
            ("ix_product_order_item_is_deleted", ["is_deleted"]),
            ("ix_product_order_item_created_time", ["created_time"]),
            ("ix_product_order_item_order_id", ["order_id"]),
            ("ix_product_order_item_product_id", ["product_id"]),
            ("ix_product_order_item_order_deleted", ["order_id", "is_deleted"]),
            ("ix_product_order_item_product_deleted", ["product_id", "is_deleted"]),
        ):
            op.create_index(name, _ITEM_TABLE, columns, unique=False)


def upgrade() -> None:
    bind = op.get_bind()
    _create_order_tables(bind)
    _reconcile_mall_menu(bind)


def downgrade() -> None:
    bind = op.get_bind()
    table_names = set(sa.inspect(bind).get_table_names())
    if _ITEM_TABLE in table_names:
        op.drop_table(_ITEM_TABLE)
    if _ORDER_TABLE in table_names:
        op.drop_table(_ORDER_TABLE)
