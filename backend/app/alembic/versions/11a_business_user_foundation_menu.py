"""Seed the Business User action permission for existing installations."""

from datetime import UTC, datetime
from uuid import uuid4

import sqlalchemy as sa
from alembic import op

revision = "11a_business_user_menu"
down_revision = "11a_business_user_foundation"
branch_labels = None
depends_on = None

_MENU_TABLE = "sys_menu"
_PARENT_PERMISSION = "module_system:app_user:query"
_BIND_PERMISSION = "module_system:app_user:bind_referrer"


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


def upgrade() -> None:
    bind = op.get_bind()
    if _MENU_TABLE not in sa.inspect(bind).get_table_names():
        return

    menu = _menu_table()
    parent_id = bind.execute(
        sa.select(menu.c.id).where(
            menu.c.type == 2,
            menu.c.permission == _PARENT_PERMISSION,
            menu.c.route_path == "users",
            menu.c.is_deleted.is_(False),
        ).limit(1)
    ).scalar_one_or_none()
    if parent_id is None:
        return

    bind.execute(
        menu.update()
        .where(menu.c.permission == "module_system:app_user:patch", menu.c.is_deleted.is_(False))
        .values(description="启用、禁用、冻结或解冻用户端用户")
    )

    exists = bind.execute(
        sa.select(menu.c.id).where(
            menu.c.permission == _BIND_PERMISSION,
            menu.c.is_deleted.is_(False),
        ).limit(1)
    ).scalar_one_or_none()
    if exists is not None:
        return

    now = datetime.now(UTC)
    bind.execute(
        menu.insert().values(
            parent_id=parent_id,
            name="绑定推荐人",
            type=3,
            order=6,
            permission=_BIND_PERMISSION,
            icon=None,
            route_name=None,
            route_path=None,
            component_path=None,
            redirect=None,
            hidden=False,
            keep_alive=True,
            always_show=False,
            title="绑定推荐人",
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
            description="为未绑定用户绑定直接推荐人",
            is_deleted=False,
            uuid=str(uuid4()),
            created_time=now,
            updated_time=now,
            deleted_time=None,
        )
    )


def downgrade() -> None:
    bind = op.get_bind()
    if _MENU_TABLE not in sa.inspect(bind).get_table_names():
        return
    menu = _menu_table()
    bind.execute(menu.delete().where(menu.c.permission == _BIND_PERMISSION))
