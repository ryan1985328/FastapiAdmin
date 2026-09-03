"""Align User-domain menu and Generator metadata with the Starter seed.

The existing ``12c`` reconciliation made the User catalog available, but its
legacy update path did not force that catalog to the approved top-level
position.  This forward-only reconciliation makes existing installations
match the canonical clean-seed hierarchy without rewriting ``12c``.
"""

from datetime import UTC, datetime
from uuid import uuid4

import sqlalchemy as sa
from alembic import op

revision = "12e_user_menu_baseline"
down_revision = "12d_merge_starter_heads"
branch_labels = None
depends_on = None

_USER_TABLES = (
    "app_user",
    "app_user_kyc",
    "app_user_address",
    "app_user_bank_account",
)

_KYC_PERMISSION = "module_system:kyc:query"
_KYC_ACTIONS = (
    ("用户实名认证查询", 1, "module_system:kyc:query"),
    ("用户实名认证详情", 2, "module_system:kyc:detail"),
    ("用户实名认证新增", 3, "module_system:kyc:create"),
    ("用户实名认证修改", 4, "module_system:kyc:update"),
    ("用户实名认证删除", 5, "module_system:kyc:delete"),
    ("用户实名认证批量状态修改", 6, "module_system:kyc:patch"),
    ("用户实名认证导出", 7, "module_system:kyc:export"),
    ("用户实名认证导入", 8, "module_system:kyc:import"),
    ("用户实名认证下载导入模板", 9, "module_system:kyc:download"),
)


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


def _active_user_catalog_id(bind, menu: sa.TableClause) -> int | None:
    result = bind.execute(
        sa.select(menu.c.id)
        .where(
            menu.c.type == 1,
            menu.c.is_deleted.is_(False),
            sa.or_(
                menu.c.route_path.in_(["app-user", "/app-user"]),
                menu.c.name == "用户端",
            ),
        )
        .order_by(menu.c.id.asc())
        .limit(1)
    ).scalar_one_or_none()
    return int(result) if result is not None else None


def _active_menu_id(bind, menu: sa.TableClause, *conditions: sa.ColumnElement[bool]) -> int | None:
    result = bind.execute(sa.select(menu.c.id).where(*conditions, menu.c.is_deleted.is_(False)).order_by(menu.c.id.asc()).limit(1)).scalar_one_or_none()
    return int(result) if result is not None else None


def _insert_menu(
    bind,
    menu: sa.TableClause,
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
    return int(bind.execute(sa.select(menu.c.id).where(menu.c.uuid == menu_uuid)).scalar_one())


def _ensure_kyc_menu(bind, menu: sa.TableClause, catalog_id: int) -> None:
    page_id = _active_menu_id(bind, menu, menu.c.type == 2, menu.c.permission == _KYC_PERMISSION)
    if page_id is None:
        page_id = _insert_menu(
            bind,
            menu,
            parent_id=catalog_id,
            name="用户实名认证",
            menu_type=2,
            order=2,
            permission=_KYC_PERMISSION,
            icon="menu",
            route_name="Kyc",
            route_path="/module_system/kyc",
            component_path="module_system/kyc/index",
            description="用户实名认证功能菜单",
        )
    else:
        bind.execute(
            menu.update()
            .where(menu.c.id == page_id)
            .values(
                parent_id=catalog_id,
                name="用户实名认证",
                title="用户实名认证",
                order=2,
                permission=_KYC_PERMISSION,
                icon="menu",
                route_name="Kyc",
                route_path="/module_system/kyc",
                component_path="module_system/kyc/index",
                status=0,
                scope="web",
                description="用户实名认证功能菜单",
            )
        )

    for name, order, permission in _KYC_ACTIONS:
        action_id = _active_menu_id(bind, menu, menu.c.type == 3, menu.c.permission == permission)
        if action_id is None:
            _insert_menu(
                bind,
                menu,
                parent_id=page_id,
                name=name,
                menu_type=3,
                order=order,
                permission=permission,
                description="用户实名认证功能按钮",
            )
            continue
        bind.execute(
            menu.update()
            .where(menu.c.id == action_id)
            .values(
                parent_id=page_id,
                name=name,
                title=name,
                order=order,
                status=0,
                scope="web",
                description="用户实名认证功能按钮",
            )
        )


def _reconcile_user_catalog(bind) -> int | None:
    if "sys_menu" not in sa.inspect(bind).get_table_names():
        return None

    menu = _menu_table()
    catalog_id = _active_user_catalog_id(bind, menu)
    if catalog_id is None:
        return None

    # This is the only hierarchy change in the revision.  The catalog and its
    # existing children keep their stable rows, permissions, and mappings.
    bind.execute(menu.update().where(menu.c.id == catalog_id).values(parent_id=None, updated_time=datetime.now(UTC)))
    return catalog_id


def _reconcile_generator_metadata(bind, catalog_id: int | None) -> None:
    if catalog_id is None or "gen_table" not in sa.inspect(bind).get_table_names():
        return

    columns = {column["name"] for column in sa.inspect(bind).get_columns("gen_table")}
    if not {"table_name", "parent_menu_id", "is_deleted"}.issubset(columns):
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
            gen_table.c.table_name.in_(_USER_TABLES),
            gen_table.c.is_deleted.is_(False),
        )
        .values(parent_menu_id=catalog_id)
    )


def upgrade() -> None:
    bind = op.get_bind()
    catalog_id = _reconcile_user_catalog(bind)
    if catalog_id is not None:
        _ensure_kyc_menu(bind, _menu_table(), catalog_id)
    _reconcile_generator_metadata(bind, catalog_id)


def downgrade() -> None:
    # The canonical top-level relationship is shared menu data.  Do not move
    # it back to a legacy parent or undo user-edited Generator metadata.
    return None
