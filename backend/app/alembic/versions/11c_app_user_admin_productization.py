"""Configure App User Admin dictionaries and Generator metadata.

The App User Admin page remains hand-authored.  This revision only makes the
shared dictionary data and the existing ``app_user`` Generator record match
the business semantics used by that page; it never regenerates source files.
"""

from datetime import UTC, datetime
from uuid import uuid4

import sqlalchemy as sa
from alembic import op

revision = "11c_app_user_admin"
down_revision = "11b_app_auth"
branch_labels = None
depends_on = None

_DICT_DEFINITIONS = (
    (
        "app_user_status",
        "用户端用户状态",
        "用户端用户业务状态",
        (
            (1, "正常", "0", "success", True, "ACTIVE"),
            (2, "禁用", "1", "danger", False, "DISABLED"),
            (3, "冻结", "2", "warning", False, "FROZEN"),
        ),
    ),
    (
        "app_user_kyc_status",
        "用户端实名状态",
        "用户端用户实名状态摘要",
        (
            (1, "未实名", "unverified", "info", True, "无有效实名记录"),
            (2, "待审核", "pending", "warning", False, "实名资料待审核"),
            (3, "已实名", "verified", "success", False, "实名资料已通过"),
            (4, "已驳回", "rejected", "danger", False, "实名资料审核未通过"),
        ),
    ),
)

_GENERATOR_COLUMNS = (
    (
        "username",
        {
            "column_comment": "登录账号",
            "column_type": "VARCHAR(64)",
            "column_length": "64",
            "column_default": "",
            "is_pk": False,
            "is_increment": False,
            "is_nullable": False,
            "is_unique": True,
            "python_type": "str",
            "python_field": "username",
            "is_insert": False,
            "is_edit": False,
            "is_list": True,
            "is_query": True,
            "query_type": "LIKE",
            "html_type": "input",
            "dict_type": "",
            "sort": 1,
        },
    ),
    (
        "password",
        {
            "column_comment": "密码哈希",
            "column_type": "VARCHAR(255)",
            "column_length": "255",
            "column_default": "",
            "is_pk": False,
            "is_increment": False,
            "is_nullable": False,
            "is_unique": False,
            "python_type": "str",
            "python_field": "password",
            "is_insert": False,
            "is_edit": False,
            "is_list": False,
            "is_query": False,
            "query_type": None,
            "html_type": "input",
            "dict_type": "",
            "sort": 2,
        },
    ),
    (
        "nickname",
        {
            "column_comment": "昵称",
            "column_type": "VARCHAR(128)",
            "column_length": "128",
            "column_default": "",
            "is_pk": False,
            "is_increment": False,
            "is_nullable": False,
            "is_unique": False,
            "python_type": "str",
            "python_field": "nickname",
            "is_insert": False,
            "is_edit": True,
            "is_list": True,
            "is_query": True,
            "query_type": "LIKE",
            "html_type": "input",
            "dict_type": "",
            "sort": 3,
        },
    ),
    (
        "avatar",
        {
            "column_comment": "头像URL地址",
            "column_type": "VARCHAR(512)",
            "column_length": "512",
            "column_default": "",
            "is_pk": False,
            "is_increment": False,
            "is_nullable": True,
            "is_unique": False,
            "python_type": "str",
            "python_field": "avatar",
            "is_insert": False,
            "is_edit": True,
            "is_list": False,
            "is_query": False,
            "query_type": None,
            "html_type": "imageUpload",
            "dict_type": "",
            "sort": 4,
        },
    ),
    (
        "mobile",
        {
            "column_comment": "唯一手机号",
            "column_type": "VARCHAR(32)",
            "column_length": "32",
            "column_default": "",
            "is_pk": False,
            "is_increment": False,
            "is_nullable": True,
            "is_unique": True,
            "python_type": "str",
            "python_field": "mobile",
            "is_insert": False,
            "is_edit": True,
            "is_list": True,
            "is_query": True,
            "query_type": "LIKE",
            "html_type": "input",
            "dict_type": "",
            "sort": 5,
        },
    ),
    (
        "status",
        {
            "column_comment": "状态(0正常 1禁用 2冻结)",
            "column_type": "INTEGER",
            "column_length": "",
            "column_default": "",
            "is_pk": False,
            "is_increment": False,
            "is_nullable": False,
            "is_unique": False,
            "python_type": "int",
            "python_field": "status",
            "is_insert": False,
            "is_edit": False,
            "is_list": True,
            "is_query": True,
            "query_type": "EQ",
            "html_type": "select",
            "dict_type": "app_user_status",
            "sort": 6,
        },
    ),
    (
        "referral_code",
        {
            "column_comment": "稳定唯一推荐码",
            "column_type": "VARCHAR(16)",
            "column_length": "16",
            "column_default": "",
            "is_pk": False,
            "is_increment": False,
            "is_nullable": False,
            "is_unique": True,
            "python_type": "str",
            "python_field": "referralCode",
            "is_insert": False,
            "is_edit": False,
            "is_list": True,
            "is_query": True,
            "query_type": "LIKE",
            "html_type": "input",
            "dict_type": "",
            "sort": 7,
        },
    ),
    (
        "referrer_id",
        {
            "column_comment": "直接推荐人ID",
            "column_type": "INTEGER",
            "column_length": "",
            "column_default": "",
            "is_pk": False,
            "is_increment": False,
            "is_nullable": True,
            "is_unique": False,
            "python_type": "int",
            "python_field": "referrerId",
            "is_insert": False,
            "is_edit": False,
            "is_list": False,
            "is_query": False,
            "query_type": None,
            "html_type": "input",
            "dict_type": "",
            "sort": 8,
        },
    ),
    (
        "referrer_bound_at",
        {
            "column_comment": "推荐关系绑定时间",
            "column_type": "DATETIME",
            "column_length": "",
            "column_default": "",
            "is_pk": False,
            "is_increment": False,
            "is_nullable": True,
            "is_unique": False,
            "python_type": "datetime",
            "python_field": "referrerBoundAt",
            "is_insert": False,
            "is_edit": False,
            "is_list": False,
            "is_query": False,
            "query_type": None,
            "html_type": "datetime",
            "dict_type": "",
            "sort": 9,
        },
    ),
    (
        "id",
        {
            "column_comment": "主键ID",
            "column_type": "INTEGER",
            "column_length": "",
            "column_default": "",
            "is_pk": True,
            "is_increment": True,
            "is_nullable": False,
            "is_unique": False,
            "python_type": "int",
            "python_field": "id",
            "is_insert": False,
            "is_edit": False,
            "is_list": False,
            "is_query": False,
            "query_type": None,
            "html_type": "input",
            "dict_type": "",
            "sort": 10,
        },
    ),
    (
        "uuid",
        {
            "column_comment": "UUID全局唯一标识",
            "column_type": "VARCHAR(64)",
            "column_length": "64",
            "column_default": "",
            "is_pk": False,
            "is_increment": False,
            "is_nullable": False,
            "is_unique": True,
            "python_type": "str",
            "python_field": "uuid",
            "is_insert": False,
            "is_edit": False,
            "is_list": False,
            "is_query": False,
            "query_type": None,
            "html_type": "input",
            "dict_type": "",
            "sort": 11,
        },
    ),
    (
        "is_deleted",
        {
            "column_comment": "是否已删除(0:未删除 1:已删除)",
            "column_type": "TINYINT",
            "column_length": "",
            "column_default": "",
            "is_pk": False,
            "is_increment": False,
            "is_nullable": False,
            "is_unique": False,
            "python_type": "bool",
            "python_field": "isDeleted",
            "is_insert": False,
            "is_edit": False,
            "is_list": False,
            "is_query": False,
            "query_type": None,
            "html_type": "input",
            "dict_type": "",
            "sort": 12,
        },
    ),
    (
        "created_time",
        {
            "column_comment": "创建时间",
            "column_type": "DATETIME",
            "column_length": "",
            "column_default": "",
            "is_pk": False,
            "is_increment": False,
            "is_nullable": False,
            "is_unique": False,
            "python_type": "datetime",
            "python_field": "createdTime",
            "is_insert": False,
            "is_edit": False,
            "is_list": True,
            "is_query": True,
            "query_type": "BETWEEN",
            "html_type": "datetime",
            "dict_type": "",
            "sort": 13,
        },
    ),
    (
        "updated_time",
        {
            "column_comment": "更新时间",
            "column_type": "DATETIME",
            "column_length": "",
            "column_default": "",
            "is_pk": False,
            "is_increment": False,
            "is_nullable": False,
            "is_unique": False,
            "python_type": "datetime",
            "python_field": "updatedTime",
            "is_insert": False,
            "is_edit": False,
            "is_list": False,
            "is_query": False,
            "query_type": None,
            "html_type": "datetime",
            "dict_type": "",
            "sort": 14,
        },
    ),
    (
        "deleted_time",
        {
            "column_comment": "删除时间",
            "column_type": "DATETIME",
            "column_length": "",
            "column_default": "",
            "is_pk": False,
            "is_increment": False,
            "is_nullable": True,
            "is_unique": False,
            "python_type": "datetime",
            "python_field": "deletedTime",
            "is_insert": False,
            "is_edit": False,
            "is_list": False,
            "is_query": False,
            "query_type": None,
            "html_type": "datetime",
            "dict_type": "",
            "sort": 15,
        },
    ),
)


def _dict_type_table() -> sa.TableClause:
    return sa.table(
        "sys_dict_type",
        sa.column("id", sa.Integer()),
        sa.column("dict_name", sa.String(length=100)),
        sa.column("dict_type", sa.String(length=255)),
        sa.column("status", sa.Integer()),
        sa.column("description", sa.Text()),
        sa.column("uuid", sa.String(length=64)),
        sa.column("is_deleted", sa.Boolean()),
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
        sa.column("uuid", sa.String(length=64)),
        sa.column("is_deleted", sa.Boolean()),
        sa.column("created_time", sa.DateTime(timezone=True)),
        sa.column("updated_time", sa.DateTime(timezone=True)),
        sa.column("deleted_time", sa.DateTime(timezone=True)),
    )


def _ensure_dictionaries(bind) -> None:
    table_names = set(sa.inspect(bind).get_table_names())
    if not {"sys_dict_type", "sys_dict_data"}.issubset(table_names):
        return

    dict_type = _dict_type_table()
    dict_data = _dict_data_table()
    now = datetime.now(UTC)

    for code, name, description, entries in _DICT_DEFINITIONS:
        type_id = bind.execute(sa.select(dict_type.c.id).where(dict_type.c.dict_type == code).order_by(dict_type.c.id.asc()).limit(1)).scalar_one_or_none()
        if type_id is None:
            bind.execute(
                dict_type.insert().values(
                    dict_name=name,
                    dict_type=code,
                    status=0,
                    description=description,
                    uuid=str(uuid4()),
                    is_deleted=False,
                    created_time=now,
                    updated_time=now,
                    deleted_time=None,
                )
            )
            # ``sa.table`` is intentionally used here so the migration can
            # run against the existing schema without importing ORM models.
            # It therefore has no implicit primary-key metadata, and some
            # dialects return an empty ``inserted_primary_key`` tuple.  Read
            # the generated id back by the stable dictionary code instead.
            type_id = bind.execute(sa.select(dict_type.c.id).where(dict_type.c.dict_type == code).order_by(dict_type.c.id.asc()).limit(1)).scalar_one()
        else:
            bind.execute(
                dict_type.update()
                .where(dict_type.c.id == type_id)
                .values(
                    dict_name=name,
                    status=0,
                    description=description,
                    is_deleted=False,
                    deleted_time=None,
                    updated_time=now,
                )
            )

        for dict_sort, label, value, list_class, is_default, entry_description in entries:
            entry_id = bind.execute(sa.select(dict_data.c.id).where(dict_data.c.dict_type == code, dict_data.c.dict_value == value).order_by(dict_data.c.id.asc()).limit(1)).scalar_one_or_none()
            values = {
                "dict_sort": dict_sort,
                "dict_label": label,
                "dict_value": value,
                "dict_type": code,
                "dict_type_id": type_id,
                "css_class": "",
                "list_class": list_class,
                "is_default": is_default,
                "status": 0,
                "description": entry_description,
                "is_deleted": False,
                "deleted_time": None,
                "updated_time": now,
            }
            if entry_id is None:
                bind.execute(
                    dict_data.insert().values(
                        **values,
                        uuid=str(uuid4()),
                        created_time=now,
                    )
                )
            else:
                bind.execute(dict_data.update().where(dict_data.c.id == entry_id).values(**values))


def _generator_table() -> sa.TableClause:
    return sa.table(
        "gen_table",
        sa.column("id", sa.Integer()),
        sa.column("table_name", sa.String(length=200)),
        sa.column("is_deleted", sa.Boolean()),
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


def _ensure_generator_metadata(bind) -> None:
    table_names = set(sa.inspect(bind).get_table_names())
    if not {"gen_table", "gen_table_column"}.issubset(table_names):
        return

    gen_table = _generator_table()
    table_id = bind.execute(sa.select(gen_table.c.id).where(gen_table.c.table_name == "app_user", gen_table.c.is_deleted.is_(False)).order_by(gen_table.c.id.asc()).limit(1)).scalar_one_or_none()
    if table_id is None:
        return

    gen_column = _generator_column_table()
    now = datetime.now(UTC)
    for column_name, config in _GENERATOR_COLUMNS:
        values = {
            "column_name": column_name,
            **config,
            "table_id": table_id,
            "status": 0,
            "is_deleted": False,
            "deleted_time": None,
            "updated_time": now,
        }
        column_id = bind.execute(
            sa.select(gen_column.c.id).where(gen_column.c.table_id == table_id, gen_column.c.column_name == column_name).order_by(gen_column.c.id.asc()).limit(1)
        ).scalar_one_or_none()
        if column_id is None:
            bind.execute(
                gen_column.insert().values(
                    **values,
                    uuid=str(uuid4()),
                    created_time=now,
                )
            )
        else:
            bind.execute(gen_column.update().where(gen_column.c.id == column_id).values(**values))


def upgrade() -> None:
    bind = op.get_bind()
    _ensure_dictionaries(bind)
    _ensure_generator_metadata(bind)


def downgrade() -> None:
    bind = op.get_bind()
    table_names = set(sa.inspect(bind).get_table_names())

    if {"sys_dict_type", "sys_dict_data"}.issubset(table_names):
        dict_type = _dict_type_table()
        dict_data = _dict_data_table()
        codes = [definition[0] for definition in _DICT_DEFINITIONS]
        bind.execute(dict_data.delete().where(dict_data.c.dict_type.in_(codes)))
        bind.execute(dict_type.delete().where(dict_type.c.dict_type.in_(codes)))

    # Generator metadata is shared, user-editable configuration.  Preserve it
    # on downgrade rather than deleting changes that may have been made after
    # this revision was applied.
