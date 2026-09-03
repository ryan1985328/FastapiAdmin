"""Remove the optional SMS Admin product surface from the Starter baseline.

SMS remains a reusable App/runtime capability, but the Admin channel, template,
and send-log pages are intentionally not part of the default Starter menu.
This is a forward-only menu reconciliation for databases that received the
runtime/Generator menu tree before the canonical seed was finalized.
"""

from datetime import UTC, datetime

import sqlalchemy as sa
from alembic import op

revision = "12f_sms_menu_baseline"
down_revision = "12e_user_menu_baseline"
branch_labels = None
depends_on = None

_MENU_TABLE = "sys_menu"
_ROLE_MENU_TABLE = "sys_role_menus"

_SMS_ROOT = {
    "name": "短信管理",
    "type": 1,
    "route_name": "Sms",
    "route_path": "sms",
}

_SMS_PAGES = (
    {
        "name": "短信渠道",
        "route_name": "SmsChannel",
        "route_path": "channel",
        "component_path": "module_system/sms_channel/index",
        "permission": "module_system:sms_channel:query",
    },
    {
        "name": "短信模板",
        "route_name": "SmsTemplate",
        "route_path": "template",
        "component_path": "module_system/sms_template/index",
        "permission": "module_system:sms_template:query",
    },
    {
        "name": "短信记录",
        "route_name": "SmsLog",
        "route_path": "log",
        "component_path": "module_system/sms_log/index",
        "permission": "module_system:sms_log:query",
    },
)

_SMS_ACTION_PERMISSIONS = (
    "module_system:sms_channel:query",
    "module_system:sms_channel:detail",
    "module_system:sms_channel:create",
    "module_system:sms_channel:update",
    "module_system:sms_channel:patch",
    "module_system:sms_channel:default",
    "module_system:sms_channel:test_send",
    "module_system:sms_template:query",
    "module_system:sms_template:detail",
    "module_system:sms_template:create",
    "module_system:sms_template:update",
    "module_system:sms_template:patch",
    "module_system:sms_log:query",
    "module_system:sms_log:detail",
)


def _menu_table() -> sa.TableClause:
    return sa.table(
        _MENU_TABLE,
        sa.column("id", sa.Integer()),
        sa.column("parent_id", sa.Integer()),
        sa.column("name", sa.String(length=64)),
        sa.column("type", sa.Integer()),
        sa.column("permission", sa.String(length=100)),
        sa.column("route_name", sa.String(length=100)),
        sa.column("route_path", sa.String(length=200)),
        sa.column("component_path", sa.String(length=200)),
        sa.column("status", sa.Integer()),
        sa.column("is_deleted", sa.Boolean()),
        sa.column("updated_time", sa.DateTime(timezone=True)),
        sa.column("deleted_time", sa.DateTime(timezone=True)),
    )


def _active_sms_menu_ids(bind, menu: sa.TableClause) -> list[int]:
    root_query = sa.select(menu.c.id).where(
        menu.c.type == _SMS_ROOT["type"],
        menu.c.name == _SMS_ROOT["name"],
        menu.c.route_name == _SMS_ROOT["route_name"],
        menu.c.route_path == _SMS_ROOT["route_path"],
        menu.c.is_deleted.is_(False),
    )
    root_ids = [int(row[0]) for row in bind.execute(root_query).all()]
    if len(root_ids) > 1:
        raise RuntimeError("发现多个活动的短信管理根菜单，停止 SMS 菜单收敛以避免误删")
    if not root_ids:
        orphan_query = sa.select(menu.c.id).where(
            menu.c.is_deleted.is_(False),
            sa.or_(
                menu.c.permission.in_(_SMS_ACTION_PERMISSIONS),
                menu.c.component_path.in_([page["component_path"] for page in _SMS_PAGES]),
            ),
        )
        orphan_ids = [int(row[0]) for row in bind.execute(orphan_query).all()]
        if orphan_ids:
            raise RuntimeError(f"发现没有短信管理根菜单的活动 SMS 节点 {orphan_ids}，停止收敛")
        return []

    page_conditions = [
        sa.and_(
            menu.c.name == page["name"],
            menu.c.route_name == page["route_name"],
            menu.c.route_path == page["route_path"],
            menu.c.component_path == page["component_path"],
            menu.c.permission == page["permission"],
        )
        for page in _SMS_PAGES
    ]
    page_query = sa.select(menu.c.id).where(
        menu.c.type == 2,
        menu.c.parent_id.in_(root_ids),
        sa.or_(*page_conditions),
        menu.c.is_deleted.is_(False),
    )
    page_ids = [int(row[0]) for row in bind.execute(page_query).all()]

    action_query = (
        sa.select(menu.c.id).where(
            menu.c.type == 3,
            menu.c.parent_id.in_(page_ids),
            menu.c.permission.in_(_SMS_ACTION_PERMISSIONS),
            menu.c.is_deleted.is_(False),
        )
        if page_ids
        else None
    )
    action_ids = [int(row[0]) for row in bind.execute(action_query).all()] if action_query is not None else []

    target_ids = set(root_ids) | set(page_ids) | set(action_ids)

    # Do not silently consume custom or unrelated children under the matched
    # SMS tree.  Fail closed if the live tree is not the audited shape.
    descendants: set[int] = set()
    frontier = set(root_ids)
    while frontier:
        child_query = sa.select(menu.c.id).where(
            menu.c.parent_id.in_(frontier),
            menu.c.is_deleted.is_(False),
        )
        children = {int(row[0]) for row in bind.execute(child_query).all()}
        children -= descendants
        if not children:
            break
        descendants.update(children)
        frontier = children

    unknown_children = descendants - (set(page_ids) | set(action_ids))
    if unknown_children:
        raise RuntimeError(f"短信菜单树包含未确认的活动子节点 {sorted(unknown_children)}，停止收敛以避免误删")

    sms_marker_query = sa.select(menu.c.id).where(
        menu.c.is_deleted.is_(False),
        sa.or_(
            menu.c.permission.in_(_SMS_ACTION_PERMISSIONS),
            menu.c.component_path.in_([page["component_path"] for page in _SMS_PAGES]),
            sa.and_(
                menu.c.type == _SMS_ROOT["type"],
                menu.c.name == _SMS_ROOT["name"],
                menu.c.route_name == _SMS_ROOT["route_name"],
                menu.c.route_path == _SMS_ROOT["route_path"],
            ),
        ),
    )
    marker_ids = {int(row[0]) for row in bind.execute(sms_marker_query).all()}
    unexpected_markers = marker_ids - target_ids
    if unexpected_markers:
        raise RuntimeError(f"发现未挂入目标树的活动 SMS 菜单节点 {sorted(unexpected_markers)}，停止收敛")

    return sorted(target_ids)


def upgrade() -> None:
    bind = op.get_bind()
    table_names = set(sa.inspect(bind).get_table_names())
    if _MENU_TABLE not in table_names:
        return

    menu = _menu_table()
    target_ids = _active_sms_menu_ids(bind, menu)
    if not target_ids:
        return

    if _ROLE_MENU_TABLE in table_names:
        role_menus = sa.table(
            _ROLE_MENU_TABLE,
            sa.column("role_id", sa.Integer()),
            sa.column("menu_id", sa.Integer()),
        )
        bind.execute(role_menus.delete().where(role_menus.c.menu_id.in_(target_ids)))

    now = datetime.now(UTC)
    bind.execute(menu.update().where(menu.c.id.in_(target_ids), menu.c.is_deleted.is_(False)).values(is_deleted=True, updated_time=now, deleted_time=now))


def downgrade() -> None:
    # This is a forward baseline reconciliation.  Re-enabling optional Admin
    # menus on downgrade could resurrect stale permissions and bypass the
    # canonical seed decision, so the data change is intentionally not undone.
    return None
