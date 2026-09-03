"""Replace the dormant SMS CRUD menu with the fixed settings product surface.

The existing ``sms_channel`` and ``sms_template`` tables remain the internal
storage contract.  This revision only adds Tencent's SDK App ID column, seeds
fail-closed system parameters, and creates a new canonical Admin menu tree.
The rows retired by ``12f_sms_menu_baseline`` are intentionally left untouched.
"""

from datetime import UTC, datetime
from uuid import uuid4

import sqlalchemy as sa
from alembic import op

revision = "12g_sms_settings_productization"
down_revision = "12f_sms_menu_baseline"
branch_labels = None
depends_on = None

_MENU_TABLE = "sys_menu"
_SMS_PROVIDERS = ("aliyun", "tencent")
_SMS_SCENES = ("register_code", "login_code", "reset_password_code")


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


def _find_ids(bind, table: sa.TableClause, *conditions: sa.ColumnElement[bool]) -> list[int]:
    result = bind.execute(
        sa.select(table.c.id).where(*conditions, table.c.is_deleted.is_(False)).order_by(table.c.id.asc()),
    )
    return [int(row[0]) for row in result]


def _insert_menu(bind, table: sa.TableClause, *, values: dict) -> int:
    now = datetime.now(UTC)
    menu_uuid = str(uuid4())
    insert_values = dict(values)
    insert_values.update(
        hidden=False,
        keep_alive=True,
        always_show=False,
        title=values["name"],
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
        description=values.get("description", ""),
        is_deleted=False,
        uuid=menu_uuid,
        created_time=now,
        updated_time=now,
        deleted_time=None,
    )
    bind.execute(
        table.insert().values(**insert_values),
    )
    return int(bind.execute(sa.select(table.c.id).where(table.c.uuid == menu_uuid)).scalar_one())


def _ensure_menu(bind, table: sa.TableClause, *, identity: tuple[sa.ColumnElement[bool], ...], values: dict) -> int:
    ids = _find_ids(bind, table, *identity)
    if len(ids) > 1:
        raise RuntimeError(f"发现重复的 SMS canonical 菜单节点: {values.get('permission') or values.get('route_name')}")
    if not ids:
        return _insert_menu(bind, table, values=values)

    menu_id = ids[0]
    bind.execute(
        table.update()
        .where(table.c.id == menu_id)
        .values(
            **values,
            title=values["name"],
            status=0,
            scope="web",
            is_deleted=False,
            deleted_time=None,
            updated_time=datetime.now(UTC),
        ),
    )
    return menu_id


def _ensure_sms_menu(bind) -> None:
    if _MENU_TABLE not in sa.inspect(bind).get_table_names():
        return

    menu = _menu_table()
    system_ids = _find_ids(bind, menu, menu.c.type == 1, menu.c.route_name == "System", menu.c.route_path == "/system")
    if len(system_ids) != 1:
        raise RuntimeError("无法唯一定位系统管理根菜单，停止 SMS 菜单收敛")
    system_id = system_ids[0]

    sms_root_id = _ensure_menu(
        bind,
        menu,
        identity=(menu.c.type == 1, menu.c.route_name == "Sms", menu.c.route_path == "sms"),
        values={
            "parent_id": system_id,
            "name": "短信管理",
            "type": 1,
            "order": 12,
            "permission": None,
            "icon": "ri:message-3-line",
            "route_name": "Sms",
            "route_path": "sms",
            "component_path": None,
            "redirect": "sms/settings",
            "description": "短信配置与发送记录",
        },
    )

    settings_id = _ensure_menu(
        bind,
        menu,
        identity=(menu.c.type == 2, menu.c.route_name == "SmsSettings", menu.c.route_path == "settings"),
        values={
            "parent_id": sms_root_id,
            "name": "短信配置",
            "type": 2,
            "order": 1,
            "permission": "module_system:sms_settings:query",
            "icon": "ri:settings-3-line",
            "route_name": "SmsSettings",
            "route_path": "settings",
            "component_path": "module_system/sms/settings",
            "redirect": None,
            "description": "固定 Aliyun 与 Tencent Cloud 短信配置",
        },
    )
    for order, name, permission, description in (
        (1, "查询", "module_system:sms_settings:query", "读取短信配置"),
        (2, "保存", "module_system:sms_settings:update", "保存短信配置"),
        (3, "测试发送", "module_system:sms_settings:test_send", "发送一条配置测试短信"),
    ):
        _ensure_menu(
            bind,
            menu,
            identity=(menu.c.type == 3, menu.c.permission == permission),
            values={
                "parent_id": settings_id,
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
            },
        )

    log_id = _ensure_menu(
        bind,
        menu,
        identity=(menu.c.type == 2, menu.c.route_name == "SmsLog", menu.c.route_path == "log"),
        values={
            "parent_id": sms_root_id,
            "name": "发送记录",
            "type": 2,
            "order": 2,
            "permission": "module_system:sms_log:query",
            "icon": "ri:history-line",
            "route_name": "SmsLog",
            "route_path": "log",
            "component_path": "module_system/sms_log/index",
            "redirect": None,
            "description": "短信供应商发送结果与错误记录",
        },
    )
    for order, name, permission, description in (
        (1, "查询", "module_system:sms_log:query", "查询短信发送记录"),
        (2, "详情", "module_system:sms_log:detail", "查看短信发送记录详情"),
    ):
        _ensure_menu(
            bind,
            menu,
            identity=(menu.c.type == 3, menu.c.permission == permission),
            values={
                "parent_id": log_id,
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
            },
        )


def _ensure_sms_params(bind) -> None:
    if "sys_param" not in sa.inspect(bind).get_table_names():
        return
    params = sa.table(
        "sys_param",
        sa.column("id", sa.Integer()),
        sa.column("config_name", sa.String(length=64)),
        sa.column("config_key", sa.String(length=500)),
        sa.column("config_value", sa.Text()),
        sa.column("config_type", sa.Boolean()),
        sa.column("status", sa.Integer()),
        sa.column("description", sa.Text()),
        sa.column("is_deleted", sa.Boolean()),
        sa.column("uuid", sa.String(length=64)),
        sa.column("created_time", sa.DateTime(timezone=True)),
        sa.column("updated_time", sa.DateTime(timezone=True)),
        sa.column("deleted_time", sa.DateTime(timezone=True)),
    )
    for key, name, value, description in (
        (
            "sms_enabled",
            "短信服务启用",
            "off",
            "是否允许 App 认证流程调用真实短信供应商；开发固定验证码仍遵循环境保护规则",
        ),
        (
            "sms_active_provider",
            "短信当前供应商",
            "aliyun",
            "App 认证短信使用的内置供应商（aliyun 或 tencent）",
        ),
    ):
        ids = _find_ids(bind, params, params.c.config_key == key)
        if len(ids) > 1:
            raise RuntimeError(f"发现重复的 SMS 系统参数: {key}")
        if ids:
            continue
        now = datetime.now(UTC)
        bind.execute(
            params.insert().values(
                config_name=name,
                config_key=key,
                config_value=value,
                config_type=True,
                status=0,
                description=description,
                is_deleted=False,
                uuid=str(uuid4()),
                created_time=now,
                updated_time=now,
                deleted_time=None,
            ),
        )


def upgrade() -> None:
    bind = op.get_bind()
    table_names = set(sa.inspect(bind).get_table_names())
    if "sms_channel" in table_names:
        columns = {column["name"] for column in sa.inspect(bind).get_columns("sms_channel")}
        if "sms_sdk_app_id" not in columns:
            op.add_column(
                "sms_channel",
                sa.Column("sms_sdk_app_id", sa.String(length=64), nullable=True, comment="腾讯云短信 SDK App ID"),
            )
    _ensure_sms_params(bind)
    _ensure_sms_menu(bind)


def downgrade() -> None:
    # This is a forward product-surface reconciliation.  Do not delete provider
    # credentials, parameters, or menu rows during a downgrade.
    return None
