"""Make App User mobile numbers unique for phone-based authentication."""

import sqlalchemy as sa
from alembic import op

revision = "11b_app_auth"
down_revision = "11a_business_user_menu"
branch_labels = None
depends_on = None

_TABLE = "app_user"
_UNIQUE = "uq_app_user_mobile"


def _has_unique_mobile(bind) -> bool:
    inspector = sa.inspect(bind)
    for constraint in inspector.get_unique_constraints(_TABLE):
        if set(constraint.get("column_names") or []) == {"mobile"}:
            return True
    return any(
        index.get("unique") and set(index.get("column_names") or []) == {"mobile"}
        for index in inspector.get_indexes(_TABLE)
    )


def _duplicate_mobiles(bind) -> list[str]:
    table = sa.table(_TABLE, sa.column("mobile", sa.String(length=32)))
    rows = bind.execute(
        sa.select(table.c.mobile)
        .where(table.c.mobile.is_not(None))
        .group_by(table.c.mobile)
        .having(sa.func.count() > 1)
    )
    return [str(row[0]) for row in rows]


def upgrade() -> None:
    bind = op.get_bind()
    if _TABLE not in sa.inspect(bind).get_table_names() or _has_unique_mobile(bind):
        return

    duplicates = _duplicate_mobiles(bind)
    if duplicates:
        raise RuntimeError(
            "无法启用手机号唯一约束，存在重复手机号，请先人工处理: " + ", ".join(duplicates[:10])
        )

    if bind.dialect.name == "sqlite":
        with op.batch_alter_table(_TABLE, recreate="always") as batch_op:
            batch_op.create_unique_constraint(_UNIQUE, ["mobile"])
    else:
        op.create_unique_constraint(_UNIQUE, _TABLE, ["mobile"])


def downgrade() -> None:
    bind = op.get_bind()
    if _TABLE not in sa.inspect(bind).get_table_names() or not _has_unique_mobile(bind):
        return
    if bind.dialect.name == "sqlite":
        with op.batch_alter_table(_TABLE, recreate="always") as batch_op:
            batch_op.drop_constraint(_UNIQUE, type_="unique")
    else:
        op.drop_constraint(_UNIQUE, _TABLE, type_="unique")
