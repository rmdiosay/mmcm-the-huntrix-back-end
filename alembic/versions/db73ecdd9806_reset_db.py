"""Reset DB

Revision ID: db73ecdd9806
Revises: f185dd74b4ec
Create Date: 2025-08-24 05:41:13.924914

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "db73ecdd9806"
down_revision: Union[str, Sequence[str], None] = "f185dd74b4ec"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Truncate tables in order to avoid foreign key issues
    op.execute("TRUNCATE TABLE lister_buyers CASCADE")
    op.execute("TRUNCATE TABLE lister_tenants CASCADE")
    op.execute("TRUNCATE TABLE buy_properties CASCADE")
    op.execute("TRUNCATE TABLE rent_properties CASCADE")
    op.execute("TRUNCATE TABLE users CASCADE")


def downgrade():
    # No-op: cannot undo truncate safely
    pass
