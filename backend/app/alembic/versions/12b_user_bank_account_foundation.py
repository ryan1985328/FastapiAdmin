"""Create the reusable App User bank account foundation and Generator metadata."""

from datetime import UTC, datetime
from uuid import uuid4

import sqlalchemy as sa
from alembic import op

revision = "12b_user_bank_account_foundation"
down_revision = "12a_user_address_foundation"
branch_labels = None
depends_on = None

_TABLE = "app_user_bank_account"
_STATUS_DICT = "app_user_bank_account_status"
_MENU_PERMISSION = "module_system:app_user_bank_account:query"
_DETAIL_PERMISSION = "module_system:app_user_bank_account:detail"
_STATUS_PERMISSION = "module_system:app_user_bank_account:patch"
_USER_MENU_PERMISSION = "module_system:app_user:query"


def _column(
    *,
    comment: str,
    column_type: str,
    python_type: str,
    python_field: str,
    nullable: bool,
    sort: int,
    is_pk: bool = False,
    is_increment: bool = False,
    is_unique: bool = False,
    is_insert: bool = False,
    is_edit: bool = False,
    is_list: bool = False,
    is_query: bool = False,
    query_type: str | None = None,
    html_type: str = "input",
    dict_type: str = "",
    length: str = "",
    default: str = "",
) -> dict[str, object]:
    return {
        "column_comment": comment,
        "column_type": column_type,
        "column_length": length,
        "column_default": default,
        "is_pk": is_pk,
        "is_increment": is_increment,
        "is_nullable": nullable,
        "is_unique": is_unique,
        "python_type": python_type,
        "python_field": python_field,
        "is_insert": is_insert,
        "is_edit": is_edit,
        "is_list": is_list,
        "is_query": is_query,
        "query_type": query_type,
        "html_type": html_type,
        "dict_type": dict_type,
        "sort": sort,
    }


_GENERATOR_COLUMNS = (
    (
        "user_id",
        _column(
            comment="App用户ID（归属由当前登录用户决定）",
            column_type="INTEGER",
            python_type="int",
            python_field="user_id",
            nullable=False,
            sort=1,
        ),
    ),
    (
        "bank_name",
        _column(
            comment="银行名称",
            column_type="VARCHAR(128)",
            length="128",
            python_type="str",
            python_field="bank_name",
            nullable=False,
            is_insert=True,
            is_edit=True,
            is_list=True,
            is_query=True,
            query_type="LIKE",
            sort=2,
        ),
    ),
    (
        "bank_code",
        _column(
            comment="银行代码（可选，不作为普通列表/查询字段）",
            column_type="VARCHAR(64)",
            length="64",
            python_type="str",
            python_field="bank_code",
            nullable=True,
            is_insert=True,
            is_edit=True,
            sort=3,
        ),
    ),
    (
        "account_name",
        _column(
            comment="持卡人姓名",
            column_type="VARCHAR(128)",
            length="128",
            python_type="str",
            python_field="account_name",
            nullable=False,
            is_insert=True,
            is_edit=True,
            is_list=True,
            is_query=True,
            query_type="LIKE",
            sort=4,
        ),
    ),
    (
        "card_number",
        _column(
            comment="银行卡号密文（Generator 仅保留输入骨架，产品 Service 负责加密）",
            column_type="TEXT",
            python_type="str",
            python_field="card_number",
            nullable=False,
            is_insert=True,
            is_edit=True,
            is_list=False,
            is_query=False,
            sort=5,
        ),
    ),
    (
        "card_last4",
        _column(
            comment="银行卡号末四位（系统辅助字段）",
            column_type="VARCHAR(4)",
            length="4",
            python_type="str",
            python_field="card_last4",
            nullable=False,
            sort=6,
        ),
    ),
    (
        "branch_name",
        _column(
            comment="开户支行（可选）",
            column_type="VARCHAR(128)",
            length="128",
            python_type="str",
            python_field="branch_name",
            nullable=True,
            is_insert=True,
            is_edit=True,
            is_list=True,
            is_query=True,
            query_type="LIKE",
            sort=7,
        ),
    ),
    (
        "is_default",
        _column(
            comment="是否默认银行卡",
            column_type="TINYINT(1)",
            python_type="bool",
            python_field="is_default",
            nullable=False,
            is_insert=True,
            is_edit=True,
            is_list=True,
            is_query=True,
            query_type="EQ",
            html_type="select",
            dict_type="sys_yes_no",
            default="0",
            sort=8,
        ),
    ),
    (
        "status",
        _column(
            comment="状态(0正常 1禁用)",
            column_type="INTEGER",
            python_type="int",
            python_field="status",
            nullable=False,
            is_list=True,
            is_query=True,
            query_type="EQ",
            html_type="select",
            dict_type=_STATUS_DICT,
            default="0",
            sort=9,
        ),
    ),
    (
        "id",
        _column(
            comment="主键ID（技术字段）",
            column_type="INTEGER",
            python_type="int",
            python_field="id",
            nullable=False,
            is_pk=True,
            is_increment=True,
            sort=10,
        ),
    ),
    (
        "uuid",
        _column(
            comment="UUID全局唯一标识（技术字段）",
            column_type="VARCHAR(64)",
            length="64",
            python_type="str",
            python_field="uuid",
            nullable=False,
            is_unique=True,
            sort=11,
        ),
    ),
    (
        "is_deleted",
        _column(
            comment="是否已删除（技术字段）",
            column_type="TINYINT(1)",
            python_type="bool",
            python_field="is_deleted",
            nullable=False,
            sort=12,
        ),
    ),
    (
        "created_time",
        _column(
            comment="创建时间",
            column_type="DATETIME",
            python_type="datetime",
            python_field="created_time",
            nullable=False,
            is_list=True,
            is_query=True,
            query_type="BETWEEN",
            html_type="datetime",
            sort=13,
        ),
    ),
    (
        "updated_time",
        _column(
            comment="更新时间（技术字段）",
            column_type="DATETIME",
            python_type="datetime",
            python_field="updated_time",
            nullable=False,
            sort=14,
        ),
    ),
    (
        "deleted_time",
        _column(
            comment="删除时间（技术字段）",
            column_type="DATETIME",
            python_type="datetime",
            python_field="deleted_time",
            nullable=True,
            sort=15,
        ),
    ),
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


def _insert_menu(bind, menu: sa.TableClause, *, parent_id: int, name: str, permission: str, order: int, description: str) -> int:
    now = datetime.now(UTC)
    bind.execute(
        menu.insert().values(
            parent_id=parent_id,
            name=name,
            type=3,
            order=order,
            permission=permission,
            icon=None,
            route_name=None,
            route_path=None,
            component_path=None,
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
            uuid=str(uuid4()),
            created_time=now,
            updated_time=now,
            deleted_time=None,
        )
    )
    return int(
        bind.execute(
            sa.select(menu.c.id).where(menu.c.permission == permission, menu.c.is_deleted.is_(False)).order_by(menu.c.id.desc()).limit(1)
        ).scalar_one()
    )


def _ensure_menu(bind) -> int | None:
    if "sys_menu" not in sa.inspect(bind).get_table_names():
        return None

    menu = _menu_table()
    catalog_id = bind.execute(
        sa.select(menu.c.id)
        .where(
            menu.c.type == 1,
            menu.c.route_path.in_(["app-user", "/app-user"]),
            menu.c.is_deleted.is_(False),
        )
        .order_by(menu.c.id.asc())
        .limit(1)
    ).scalar_one_or_none()
    if catalog_id is None:
        return None

    bind.execute(
        menu.update()
        .where(
            menu.c.parent_id == catalog_id,
            menu.c.type == 2,
            menu.c.permission == _USER_MENU_PERMISSION,
            menu.c.route_path == "users",
            menu.c.is_deleted.is_(False),
        )
        .values(name="用户管理", title="用户管理")
    )

    bank_id = bind.execute(
        sa.select(menu.c.id)
        .where(menu.c.permission == _MENU_PERMISSION, menu.c.is_deleted.is_(False))
        .order_by(menu.c.id.asc())
        .limit(1)
    ).scalar_one_or_none()
    if bank_id is None:
        now = datetime.now(UTC)
        bind.execute(
            menu.insert().values(
                parent_id=catalog_id,
                name="用户银行卡",
                type=2,
                order=3,
                permission=_MENU_PERMISSION,
                icon="ri:bank-card-line",
                route_name="AppUserBankAccount",
                route_path="bank-accounts",
                component_path="module_system/app_user_bank_account/index",
                redirect=None,
                hidden=False,
                keep_alive=True,
                always_show=False,
                title="用户银行卡",
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
                description="用户银行卡查询、详情与状态管理",
                is_deleted=False,
                uuid=str(uuid4()),
                created_time=now,
                updated_time=now,
                deleted_time=None,
            )
        )
        bank_id = bind.execute(
            sa.select(menu.c.id).where(menu.c.permission == _MENU_PERMISSION, menu.c.is_deleted.is_(False)).order_by(menu.c.id.desc()).limit(1)
        ).scalar_one()

    child_data = (
        (1, "查询", _MENU_PERMISSION, "查询用户银行卡"),
        (2, "详情", _DETAIL_PERMISSION, "查看用户银行卡详情"),
        (3, "状态变更", _STATUS_PERMISSION, "启用或禁用用户银行卡"),
    )
    for order, name, permission, description in child_data:
        exists_id = bind.execute(
            sa.select(menu.c.id)
            .where(
                menu.c.parent_id == bank_id,
                menu.c.type == 3,
                menu.c.permission == permission,
                menu.c.is_deleted.is_(False),
            )
            .limit(1)
        ).scalar_one_or_none()
        if exists_id is None:
            _insert_menu(bind, menu, parent_id=int(bank_id), name=name, permission=permission, order=order, description=description)
    return int(bank_id)


def _dict_type_table() -> sa.TableClause:
    return sa.table(
        "sys_dict_type",
        sa.column("id", sa.Integer()),
        sa.column("dict_name", sa.String(length=100)),
        sa.column("dict_type", sa.String(length=255)),
        sa.column("status", sa.Integer()),
        sa.column("description", sa.Text()),
        sa.column("is_deleted", sa.Boolean()),
        sa.column("uuid", sa.String(length=64)),
        sa.column("created_time", sa.DateTime(timezone=True)),
        sa.column("updated_time", sa.DateTime(timezone=True)),
        sa.column("deleted_time", sa.DateTime(timezone=True)),
    )


def _dict_data_table() -> sa.TableClause:
    return sa.table(
        "sys_dict_data",
        sa.column("id", sa.Integer()),
        sa.column("dict_sort", sa.Integer()),
        sa.column("dict_label", sa.String(length=255)),
        sa.column("dict_value", sa.String(length=255)),
        sa.column("dict_type", sa.String(length=255)),
        sa.column("dict_type_id", sa.Integer()),
        sa.column("css_class", sa.String(length=255)),
        sa.column("list_class", sa.String(length=255)),
        sa.column("is_default", sa.Boolean()),
        sa.column("status", sa.Integer()),
        sa.column("description", sa.Text()),
        sa.column("is_deleted", sa.Boolean()),
        sa.column("uuid", sa.String(length=64)),
        sa.column("created_time", sa.DateTime(timezone=True)),
        sa.column("updated_time", sa.DateTime(timezone=True)),
        sa.column("deleted_time", sa.DateTime(timezone=True)),
    )


def _ensure_status_dict(bind) -> None:
    table_names = set(sa.inspect(bind).get_table_names())
    if not {"sys_dict_type", "sys_dict_data"}.issubset(table_names):
        return

    dict_type = _dict_type_table()
    dict_data = _dict_data_table()
    type_id = bind.execute(
        sa.select(dict_type.c.id)
        .where(dict_type.c.dict_type == _STATUS_DICT, dict_type.c.is_deleted.is_(False))
        .order_by(dict_type.c.id.asc())
        .limit(1)
    ).scalar_one_or_none()
    now = datetime.now(UTC)
    if type_id is None:
        bind.execute(
            dict_type.insert().values(
                dict_name="用户银行卡状态",
                dict_type=_STATUS_DICT,
                status=0,
                description="用户银行卡业务状态（0正常 1禁用）",
                is_deleted=False,
                uuid=str(uuid4()),
                created_time=now,
                updated_time=now,
                deleted_time=None,
            )
        )
        type_id = bind.execute(
            sa.select(dict_type.c.id).where(dict_type.c.dict_type == _STATUS_DICT, dict_type.c.is_deleted.is_(False)).order_by(dict_type.c.id.desc()).limit(1)
        ).scalar_one()

    for sort, label, value, list_class, description in (
        (1, "正常", "0", "success", "银行卡可正常使用"),
        (2, "禁用", "1", "danger", "银行卡已被管理员禁用"),
    ):
        exists_id = bind.execute(
            sa.select(dict_data.c.id)
            .where(
                dict_data.c.dict_type == _STATUS_DICT,
                dict_data.c.dict_value == value,
                dict_data.c.is_deleted.is_(False),
            )
            .limit(1)
        ).scalar_one_or_none()
        if exists_id is not None:
            continue
        bind.execute(
            dict_data.insert().values(
                dict_sort=sort,
                dict_label=label,
                dict_value=value,
                dict_type=_STATUS_DICT,
                dict_type_id=type_id,
                css_class="",
                list_class=list_class,
                is_default=value == "0",
                status=0,
                description=description,
                is_deleted=False,
                uuid=str(uuid4()),
                created_time=now,
                updated_time=now,
                deleted_time=None,
            )
        )


def _generator_table() -> sa.TableClause:
    return sa.table(
        "gen_table",
        sa.column("id", sa.Integer()),
        sa.column("table_name", sa.String(length=200)),
        sa.column("table_comment", sa.String(length=500)),
        sa.column("class_name", sa.String(length=100)),
        sa.column("package_name", sa.String(length=100)),
        sa.column("module_name", sa.String(length=30)),
        sa.column("business_name", sa.String(length=30)),
        sa.column("function_name", sa.String(length=100)),
        sa.column("sub_table_name", sa.String(length=64)),
        sa.column("sub_table_fk_name", sa.String(length=64)),
        sa.column("parent_menu_id", sa.Integer()),
        sa.column("status", sa.Integer()),
        sa.column("description", sa.Text()),
        sa.column("uuid", sa.String(length=64)),
        sa.column("is_deleted", sa.Boolean()),
        sa.column("created_time", sa.DateTime(timezone=True)),
        sa.column("updated_time", sa.DateTime(timezone=True)),
        sa.column("deleted_time", sa.DateTime(timezone=True)),
    )


def _generator_column_table() -> sa.TableClause:
    return sa.table(
        "gen_table_column",
        sa.column("id", sa.Integer()),
        sa.column("column_name", sa.String(length=200)),
        sa.column("column_comment", sa.String(length=500)),
        sa.column("column_type", sa.String(length=100)),
        sa.column("column_length", sa.String(length=50)),
        sa.column("column_default", sa.String(length=200)),
        sa.column("is_pk", sa.Boolean()),
        sa.column("is_increment", sa.Boolean()),
        sa.column("is_nullable", sa.Boolean()),
        sa.column("is_unique", sa.Boolean()),
        sa.column("python_type", sa.String(length=100)),
        sa.column("python_field", sa.String(length=200)),
        sa.column("is_insert", sa.Boolean()),
        sa.column("is_edit", sa.Boolean()),
        sa.column("is_list", sa.Boolean()),
        sa.column("is_query", sa.Boolean()),
        sa.column("query_type", sa.String(length=50)),
        sa.column("html_type", sa.String(length=100)),
        sa.column("dict_type", sa.String(length=200)),
        sa.column("sort", sa.Integer()),
        sa.column("table_id", sa.Integer()),
        sa.column("status", sa.Integer()),
        sa.column("description", sa.Text()),
        sa.column("uuid", sa.String(length=64)),
        sa.column("is_deleted", sa.Boolean()),
        sa.column("created_time", sa.DateTime(timezone=True)),
        sa.column("updated_time", sa.DateTime(timezone=True)),
        sa.column("deleted_time", sa.DateTime(timezone=True)),
    )


def _ensure_generator_metadata(bind, parent_menu_id: int | None) -> None:
    table_names = set(sa.inspect(bind).get_table_names())
    if not {"gen_table", "gen_table_column"}.issubset(table_names):
        return

    gen_table = _generator_table()
    table_id = bind.execute(
        sa.select(gen_table.c.id)
        .where(gen_table.c.table_name == _TABLE, gen_table.c.is_deleted.is_(False))
        .order_by(gen_table.c.id.asc())
        .limit(1)
    ).scalar_one_or_none()
    now = datetime.now(UTC)
    table_values = {
        "table_name": _TABLE,
        "table_comment": "用户银行卡",
        "class_name": "AppUserBankAccount",
        "package_name": "module_system",
        "module_name": "app_user_bank_account",
        "business_name": "app_user_bank_account",
        "function_name": "用户银行卡",
        "sub_table_name": None,
        "sub_table_fk_name": None,
        "parent_menu_id": parent_menu_id,
        "status": 0,
        "description": "用户银行卡基础能力；Admin 页面按业务语义手工产品化，card_number 不得使用 Generator 默认 CRUD",
        "is_deleted": False,
        "deleted_time": None,
        "updated_time": now,
    }
    if table_id is None:
        bind.execute(gen_table.insert().values(**table_values, uuid=str(uuid4()), created_time=now))
        table_id = bind.execute(
            sa.select(gen_table.c.id).where(gen_table.c.table_name == _TABLE, gen_table.c.is_deleted.is_(False)).order_by(gen_table.c.id.asc()).limit(1)
        ).scalar_one()
    else:
        bind.execute(gen_table.update().where(gen_table.c.id == table_id).values(**table_values))

    gen_column = _generator_column_table()
    for column_name, config in _GENERATOR_COLUMNS:
        values = {
            "column_name": column_name,
            **config,
            "table_id": table_id,
            "status": 0,
            "description": None,
            "is_deleted": False,
            "deleted_time": None,
            "updated_time": now,
        }
        column_id = bind.execute(
            sa.select(gen_column.c.id)
            .where(gen_column.c.table_id == table_id, gen_column.c.column_name == column_name)
            .order_by(gen_column.c.id.asc())
            .limit(1)
        ).scalar_one_or_none()
        if column_id is None:
            bind.execute(gen_column.insert().values(**values, uuid=str(uuid4()), created_time=now))
        else:
            bind.execute(gen_column.update().where(gen_column.c.id == column_id).values(**values))


def upgrade() -> None:
    bind = op.get_bind()
    table_names = set(sa.inspect(bind).get_table_names())
    if _TABLE not in table_names:
        op.create_table(
            _TABLE,
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False, comment="主键ID"),
            sa.Column("uuid", sa.String(length=64), nullable=False, comment="UUID全局唯一标识"),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false(), comment="是否已删除"),
            sa.Column("created_time", sa.DateTime(timezone=True), nullable=False, comment="创建时间"),
            sa.Column("updated_time", sa.DateTime(timezone=True), nullable=False, comment="更新时间"),
            sa.Column("deleted_time", sa.DateTime(timezone=True), nullable=True, comment="删除时间"),
            sa.Column(
                "user_id",
                sa.Integer(),
                sa.ForeignKey("app_user.id", ondelete="CASCADE", onupdate="CASCADE"),
                nullable=False,
                comment="App用户ID",
            ),
            sa.Column("bank_name", sa.String(length=128), nullable=False, comment="银行名称"),
            sa.Column("bank_code", sa.String(length=64), nullable=True, comment="银行代码"),
            sa.Column("account_name", sa.String(length=128), nullable=False, comment="持卡人姓名"),
            sa.Column("card_number", sa.Text(), nullable=False, comment="银行卡号密文"),
            sa.Column("card_last4", sa.String(length=4), nullable=False, comment="银行卡号末四位"),
            sa.Column("branch_name", sa.String(length=128), nullable=True, comment="开户支行"),
            sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.false(), comment="是否默认银行卡"),
            sa.Column("status", sa.Integer(), nullable=False, server_default="0", comment="状态(0正常 1禁用)"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("uuid"),
            comment="用户银行卡",
        )
        op.create_index("ix_app_user_bank_account_id", _TABLE, ["id"], unique=False)
        op.create_index("ix_app_user_bank_account_uuid", _TABLE, ["uuid"], unique=False)
        op.create_index("ix_app_user_bank_account_is_deleted", _TABLE, ["is_deleted"], unique=False)
        op.create_index("ix_app_user_bank_account_created_time", _TABLE, ["created_time"], unique=False)
        op.create_index("ix_app_user_bank_account_user_id", _TABLE, ["user_id"], unique=False)
        op.create_index("ix_app_user_bank_account_card_last4", _TABLE, ["card_last4"], unique=False)
        op.create_index(
            "ix_app_user_bank_account_user_default_deleted",
            _TABLE,
            ["user_id", "is_default", "is_deleted"],
            unique=False,
        )
        op.create_index(
            "ix_app_user_bank_account_user_status_deleted",
            _TABLE,
            ["user_id", "status", "is_deleted"],
            unique=False,
        )
        op.create_index(
            "ix_app_user_bank_account_user_created_deleted",
            _TABLE,
            ["user_id", "created_time", "is_deleted"],
            unique=False,
        )

    _ensure_status_dict(bind)
    bank_menu_id = _ensure_menu(bind)
    _ensure_generator_metadata(bind, bank_menu_id)


def downgrade() -> None:
    bind = op.get_bind()
    table_names = set(sa.inspect(bind).get_table_names())

    if {"gen_table", "gen_table_column"}.issubset(table_names):
        gen_table = _generator_table()
        gen_column = _generator_column_table()
        table_ids = sa.select(gen_table.c.id).where(gen_table.c.table_name == _TABLE)
        bind.execute(gen_column.delete().where(gen_column.c.table_id.in_(table_ids)))
        bind.execute(gen_table.delete().where(gen_table.c.table_name == _TABLE))

    if "sys_menu" in table_names:
        menu = _menu_table()
        bind.execute(
            menu.delete().where(
                menu.c.permission.in_([_MENU_PERMISSION, _DETAIL_PERMISSION, _STATUS_PERMISSION])
            )
        )

    if {"sys_dict_data", "sys_dict_type"}.issubset(table_names):
        dict_data = _dict_data_table()
        dict_type = _dict_type_table()
        bind.execute(dict_data.delete().where(dict_data.c.dict_type == _STATUS_DICT))
        bind.execute(dict_type.delete().where(dict_type.c.dict_type == _STATUS_DICT))

    if _TABLE in table_names:
        op.drop_table(_TABLE)
