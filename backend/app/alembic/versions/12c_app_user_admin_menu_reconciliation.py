"""Reconcile the App User admin menu for legacy seeded installations.

Older development databases can still have the App User pages under the
``业务示例`` catalog.  The current seed uses a dedicated ``用户端`` catalog,
so this revision moves the existing pages and makes the 12A/12B pages
available without touching the Product menu or assigning new permissions to
non-superuser roles.
"""

from datetime import UTC, datetime
from uuid import uuid4

import sqlalchemy as sa
from alembic import op

revision = "12c_user_menu_reconcile"
down_revision = "12b_user_bank_account_foundation"
branch_labels = None
depends_on = None

_MENU_TABLE = "sys_menu"
_USER_PERMISSION = "module_system:app_user:query"
_KYC_PERMISSION = "module_system:kyc:query"
_ADDRESS_PERMISSION = "module_system:app_user_address:query"
_ADDRESS_DETAIL_PERMISSION = "module_system:app_user_address:detail"
_BANK_PERMISSION = "module_system:app_user_bank_account:query"
_BANK_DETAIL_PERMISSION = "module_system:app_user_bank_account:detail"
_BANK_STATUS_PERMISSION = "module_system:app_user_bank_account:patch"


def _menu_table() -> sa.TableClause:
    return sa.table(
        _MENU_TABLE,
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


def _active_menu_id(bind, menu: sa.TableClause, *conditions: sa.ColumnElement[bool]) -> int | None:
    result = bind.execute(
        sa.select(menu.c.id)
        .where(*conditions, menu.c.is_deleted.is_(False))
        .order_by(menu.c.id.asc())
        .limit(1)
    ).scalar_one_or_none()
    return int(result) if result is not None else None


def _insert_menu(
    bind,
    menu: sa.TableClause,
    *,
    parent_id: int | None,
    name: str,
    menu_type: int,
    order: int,
    permission: str | None = None,
    icon: str | None = None,
    route_name: str | None = None,
    route_path: str | None = None,
    component_path: str | None = None,
    redirect: str | None = None,
    description: str = "",
) -> int:
    now = datetime.now(UTC)
    menu_uuid = str(uuid4())
    bind.execute(
        menu.insert().values(
            parent_id=parent_id,
            name=name,
            type=menu_type,
            order=order,
            permission=permission,
            icon=icon,
            route_name=route_name,
            route_path=route_path,
            component_path=component_path,
            redirect=redirect,
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
    return int(bind.execute(sa.select(menu.c.id).where(menu.c.uuid == menu_uuid)).scalar_one())


def _ensure_catalog(bind, menu: sa.TableClause) -> int:
    catalog_id = _active_menu_id(
        bind,
        menu,
        menu.c.type == 1,
        menu.c.route_path.in_(["app-user", "/app-user"]),
    )
    if catalog_id is None:
        catalog_id = _active_menu_id(bind, menu, menu.c.type == 1, menu.c.name == "用户端")

    if catalog_id is None:
        catalog_id = _insert_menu(
            bind,
            menu,
            parent_id=None,
            name="用户端",
            menu_type=1,
            order=8,
            icon="ri:user-smile-line",
            route_name="AppUser",
            route_path="app-user",
            redirect="app-user",
            description="C端用户管理",
        )
    else:
        bind.execute(
            menu.update()
            .where(menu.c.id == catalog_id)
            .values(
                name="用户端",
                title="用户端",
                icon="ri:user-smile-line",
                route_name="AppUser",
                route_path="app-user",
                redirect="app-user",
                order=8,
                status=0,
                scope="web",
                description="C端用户管理",
            )
        )
    return catalog_id


def _move_existing_page(
    bind,
    menu: sa.TableClause,
    *,
    catalog_id: int,
    permission: str,
    name: str,
    order: int,
) -> None:
    page_id = _active_menu_id(bind, menu, menu.c.type == 2, menu.c.permission == permission)
    if page_id is None:
        return
    bind.execute(
        menu.update()
        .where(menu.c.id == page_id)
        .values(
            parent_id=catalog_id,
            name=name,
            title=name,
            order=order,
            status=0,
            scope="web",
        )
    )


def _ensure_page(
    bind,
    menu: sa.TableClause,
    *,
    catalog_id: int,
    permission: str,
    name: str,
    order: int,
    icon: str,
    route_name: str,
    route_path: str,
    component_path: str,
    description: str,
) -> int:
    page_id = _active_menu_id(bind, menu, menu.c.type == 2, menu.c.permission == permission)
    if page_id is None:
        return _insert_menu(
            bind,
            menu,
            parent_id=catalog_id,
            name=name,
            menu_type=2,
            order=order,
            permission=permission,
            icon=icon,
            route_name=route_name,
            route_path=route_path,
            component_path=component_path,
            description=description,
        )

    bind.execute(
        menu.update()
        .where(menu.c.id == page_id)
        .values(
            parent_id=catalog_id,
            name=name,
            title=name,
            order=order,
            icon=icon,
            route_name=route_name,
            route_path=route_path,
            component_path=component_path,
            status=0,
            scope="web",
            description=description,
        )
    )
    return page_id


def _ensure_action(
    bind,
    menu: sa.TableClause,
    *,
    page_id: int,
    permission: str,
    name: str,
    order: int,
    description: str,
) -> None:
    action_id = _active_menu_id(
        bind,
        menu,
        menu.c.parent_id == page_id,
        menu.c.type == 3,
        menu.c.permission == permission,
    )
    if action_id is None:
        _insert_menu(
            bind,
            menu,
            parent_id=page_id,
            name=name,
            menu_type=3,
            order=order,
            permission=permission,
            description=description,
        )
        return

    bind.execute(
        menu.update()
        .where(menu.c.id == action_id)
        .values(
            name=name,
            title=name,
            order=order,
            status=0,
            scope="web",
            description=description,
        )
    )


def _link_generator_metadata(bind, catalog_id: int) -> None:
    if "gen_table" not in sa.inspect(bind).get_table_names():
        return

    gen_table = sa.table(
        "gen_table",
        sa.column("table_name", sa.String(length=200)),
        sa.column("parent_menu_id", sa.Integer()),
        sa.column("is_deleted", sa.Boolean()),
    )
    bind.execute(
        gen_table.update()
        .where(
            gen_table.c.table_name.in_(["app_user_address", "app_user_bank_account"]),
            gen_table.c.is_deleted.is_(False),
        )
        .values(parent_menu_id=catalog_id)
    )


def upgrade() -> None:
    bind = op.get_bind()
    if _MENU_TABLE not in sa.inspect(bind).get_table_names():
        return

    menu = _menu_table()
    catalog_id = _ensure_catalog(bind, menu)

    # Keep the existing Product catalog intact; only move the App User pages
    # that were seeded under it by older versions.
    _move_existing_page(
        bind,
        menu,
        catalog_id=catalog_id,
        permission=_USER_PERMISSION,
        name="用户管理",
        order=1,
    )
    _move_existing_page(
        bind,
        menu,
        catalog_id=catalog_id,
        permission=_KYC_PERMISSION,
        name="用户实名认证",
        order=2,
    )

    address_id = _ensure_page(
        bind,
        menu,
        catalog_id=catalog_id,
        permission=_ADDRESS_PERMISSION,
        name="用户地址",
        order=3,
        icon="ri:map-pin-line",
        route_name="AppUserAddress",
        route_path="addresses",
        component_path="module_system/app_user_address/index",
        description="用户地址查询与详情",
    )
    _ensure_action(
        bind,
        menu,
        page_id=address_id,
        permission=_ADDRESS_PERMISSION,
        name="查询",
        order=1,
        description="查询用户地址",
    )
    _ensure_action(
        bind,
        menu,
        page_id=address_id,
        permission=_ADDRESS_DETAIL_PERMISSION,
        name="详情",
        order=2,
        description="查看用户地址详情",
    )

    bank_id = _ensure_page(
        bind,
        menu,
        catalog_id=catalog_id,
        permission=_BANK_PERMISSION,
        name="用户银行卡",
        order=4,
        icon="ri:bank-card-line",
        route_name="AppUserBankAccount",
        route_path="bank-accounts",
        component_path="module_system/app_user_bank_account/index",
        description="用户银行卡查询、详情与状态管理",
    )
    for order, name, permission, description in (
        (1, "查询", _BANK_PERMISSION, "查询用户银行卡"),
        (2, "详情", _BANK_DETAIL_PERMISSION, "查看用户银行卡详情"),
        (3, "状态变更", _BANK_STATUS_PERMISSION, "启用或禁用用户银行卡"),
    ):
        _ensure_action(
            bind,
            menu,
            page_id=bank_id,
            permission=permission,
            name=name,
            order=order,
            description=description,
        )

    # Generator expects parent_menu_id to point to a catalog, not a page.
    # 12A/12B could not resolve the catalog on legacy databases, so repair the
    # linkage after the canonical User catalog is available.
    _link_generator_metadata(bind, catalog_id)


def downgrade() -> None:
    # This is a reconciliation of shared menu data.  Leave existing menu and
    # permission rows intact on downgrade; deleting them could remove seed or
    # manually maintained permissions owned by 12A/12B or an administrator.
    pass
