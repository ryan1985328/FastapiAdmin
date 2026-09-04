"""Add normalized ordered media associations for Mini Mall products."""

import sqlalchemy as sa
from alembic import op

revision = "12i_mini_mall_product_media"
down_revision = "12h_mini_mall_vertical_slice"
branch_labels = None
depends_on = None

_TABLE = "product_image"


def upgrade() -> None:
    bind = op.get_bind()
    if _TABLE in sa.inspect(bind).get_table_names():
        return

    op.create_table(
        _TABLE,
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False, comment="主键ID"),
        sa.Column("uuid", sa.String(length=64), nullable=False, comment="UUID全局唯一标识"),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false(), comment="是否已删除"),
        sa.Column("created_time", sa.DateTime(timezone=True), nullable=False, comment="创建时间"),
        sa.Column("updated_time", sa.DateTime(timezone=True), nullable=False, comment="更新时间"),
        sa.Column("deleted_time", sa.DateTime(timezone=True), nullable=True, comment="删除时间"),
        sa.Column(
            "created_id",
            sa.Integer(),
            sa.ForeignKey("sys_user.id", ondelete="SET NULL", onupdate="CASCADE"),
            nullable=True,
            comment="创建人ID",
        ),
        sa.Column(
            "updated_id",
            sa.Integer(),
            sa.ForeignKey("sys_user.id", ondelete="SET NULL", onupdate="CASCADE"),
            nullable=True,
            comment="更新人ID",
        ),
        sa.Column(
            "deleted_id",
            sa.Integer(),
            sa.ForeignKey("sys_user.id", ondelete="SET NULL", onupdate="CASCADE"),
            nullable=True,
            comment="删除人ID",
        ),
        sa.Column(
            "product_id",
            sa.Integer(),
            sa.ForeignKey("product.id", ondelete="CASCADE", onupdate="CASCADE"),
            nullable=False,
            comment="商品ID",
        ),
        sa.Column(
            "storage_key",
            sa.String(length=512),
            nullable=False,
            comment="存储对象key",
        ),
        sa.Column(
            "source_id",
            sa.Integer(),
            sa.ForeignKey("storage_source.id", ondelete="SET NULL", onupdate="CASCADE"),
            nullable=True,
            comment="存储源ID",
        ),
        sa.Column("sort", sa.Integer(), nullable=False, server_default="0", comment="展示顺序"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("uuid"),
        comment="商品图片关联",
    )
    for name, columns in (
        ("ix_product_image_id", ["id"]),
        ("ix_product_image_uuid", ["uuid"]),
        ("ix_product_image_is_deleted", ["is_deleted"]),
        ("ix_product_image_created_time", ["created_time"]),
        ("ix_product_image_product_id", ["product_id"]),
        ("ix_product_image_source_id", ["source_id"]),
        ("ix_product_image_sort", ["sort"]),
        ("ix_product_image_product_sort_deleted", ["product_id", "sort", "is_deleted"]),
    ):
        op.create_index(name, _TABLE, columns, unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    if _TABLE in sa.inspect(bind).get_table_names():
        op.drop_table(_TABLE)
