"""Merge the two Starter development migration branches.

The KYC workspace and App User menu work landed on parallel branches during
Starter development.  This revision intentionally performs no schema or data
mutation; it only gives future upgrades one canonical Alembic head.
"""

revision = "12d_merge_starter_heads"
down_revision = ("11d_kyc_admin_workspace", "12c_user_menu_reconcile")
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Converge the migration graph without changing application data."""
    return None


def downgrade() -> None:
    """Keep the merge revision reversible without mutating application data."""
    return None
