"""Add Business User referral fields and backfill existing App users.

This repository historically initialized tables with ``create_all`` and had
no migration lineage. The revision is therefore self-contained and can be
applied after the existing baseline tables have been created.
"""

import sqlalchemy as sa
from alembic import op

from app.plugin.module_app.user.referral import generate_referral_code

revision = "11a_business_user_foundation"
down_revision = None
branch_labels = None
depends_on = None

_TABLE = "app_user"
_REFERRAL_UNIQUE = "uq_app_user_referral_code"
_REFERRER_FK = "fk_app_user_referrer_id"
_REFERRER_INDEX = "ix_app_user_referrer_id"


def _has_unique_referral(bind) -> bool:
    inspector = sa.inspect(bind)
    for constraint in inspector.get_unique_constraints(_TABLE):
        if set(constraint.get("column_names") or []) == {"referral_code"}:
            return True
    return any(
        index.get("unique") and set(index.get("column_names") or []) == {"referral_code"}
        for index in inspector.get_indexes(_TABLE)
    )


def _has_referrer_fk(bind) -> bool:
    inspector = sa.inspect(bind)
    return any(
        set(foreign_key.get("constrained_columns") or []) == {"referrer_id"}
        and foreign_key.get("referred_table") == _TABLE
        for foreign_key in inspector.get_foreign_keys(_TABLE)
    )


def _has_index(bind, name: str) -> bool:
    return any(index.get("name") == name for index in sa.inspect(bind).get_indexes(_TABLE))


def _backfill_referral_codes(bind) -> None:
    table = sa.table(
        _TABLE,
        sa.column("id", sa.Integer()),
        sa.column("referral_code", sa.String(length=16)),
    )
    rows = bind.execute(sa.select(table.c.id, table.c.referral_code).order_by(table.c.id)).mappings().all()
    used: set[str] = set()

    for row in rows:
        raw_code = row["referral_code"]
        code = str(raw_code).strip().upper() if raw_code else ""
        if not code or code in used:
            while True:
                candidate = generate_referral_code()
                if candidate not in used:
                    code = candidate
                    break
        used.add(code)
        if raw_code != code:
            bind.execute(table.update().where(table.c.id == row["id"]).values(referral_code=code))


def upgrade() -> None:
    bind = op.get_bind()
    columns = {column["name"] for column in sa.inspect(bind).get_columns(_TABLE)}

    if "referral_code" not in columns:
        op.add_column(
            _TABLE,
            sa.Column("referral_code", sa.String(length=16), nullable=True, comment="稳定唯一推荐码"),
        )
    if "referrer_id" not in columns:
        op.add_column(
            _TABLE,
            sa.Column("referrer_id", sa.Integer(), nullable=True, comment="直接推荐人ID"),
        )
    if "referrer_bound_at" not in columns:
        op.add_column(
            _TABLE,
            sa.Column("referrer_bound_at", sa.DateTime(timezone=True), nullable=True, comment="推荐关系绑定时间"),
        )

    _backfill_referral_codes(bind)

    if bind.dialect.name == "sqlite":
        # SQLite cannot add a named FK/UNIQUE constraint with standalone
        # ALTER TABLE; batch recreation keeps the migration portable.
        with op.batch_alter_table(_TABLE, recreate="always") as batch_op:
            if not _has_unique_referral(bind):
                batch_op.create_unique_constraint(_REFERRAL_UNIQUE, ["referral_code"])
            if not _has_referrer_fk(bind):
                batch_op.create_foreign_key(
                    _REFERRER_FK,
                    _TABLE,
                    ["referrer_id"],
                    ["id"],
                    ondelete="SET NULL",
                    onupdate="CASCADE",
                )
            batch_op.alter_column(
                "referral_code",
                existing_type=sa.String(length=16),
                nullable=False,
            )
    else:
        if not _has_unique_referral(bind):
            op.create_unique_constraint(_REFERRAL_UNIQUE, _TABLE, ["referral_code"])
        if not _has_referrer_fk(bind):
            op.create_foreign_key(
                _REFERRER_FK,
                _TABLE,
                _TABLE,
                ["referrer_id"],
                ["id"],
                ondelete="SET NULL",
                onupdate="CASCADE",
            )
        op.alter_column(
            _TABLE,
            "referral_code",
            existing_type=sa.String(length=16),
            nullable=False,
        )

    if not _has_index(bind, _REFERRER_INDEX):
        op.create_index(_REFERRER_INDEX, _TABLE, ["referrer_id"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        with op.batch_alter_table(_TABLE, recreate="always") as batch_op:
            batch_op.drop_constraint(_REFERRER_FK, type_="foreignkey")
            batch_op.drop_constraint(_REFERRAL_UNIQUE, type_="unique")
            batch_op.drop_column("referrer_bound_at")
            batch_op.drop_column("referrer_id")
            batch_op.drop_column("referral_code")
    else:
        inspector = sa.inspect(bind)
        if any(index.get("name") == _REFERRER_INDEX for index in inspector.get_indexes(_TABLE)):
            op.drop_index(_REFERRER_INDEX, table_name=_TABLE)
        if _has_referrer_fk(bind):
            op.drop_constraint(_REFERRER_FK, _TABLE, type_="foreignkey")
        if _has_unique_referral(bind):
            op.drop_constraint(_REFERRAL_UNIQUE, _TABLE, type_="unique")
        for column_name in ("referrer_bound_at", "referrer_id", "referral_code"):
            if column_name in {column["name"] for column in sa.inspect(bind).get_columns(_TABLE)}:
                op.drop_column(_TABLE, column_name)
