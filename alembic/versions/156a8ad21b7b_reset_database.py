"""reset database

Revision ID: 156a8ad21b7b
Revises: 2e5d613f9825
Create Date: 2025-08-24 03:52:36.086045

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "156a8ad21b7b"
down_revision = '2e5d613f9825'  # or the last revision if any
branch_labels = None
depends_on = None


def upgrade():
    # Drop all tables
    op.execute("TRUNCATE TABLE users CASCADE;")
    op.execute("TRUNCATE TABLE rent_properties CASCADE;")
    op.execute("TRUNCATE TABLE buy_properties CASCADE;")
    op.execute("TRUNCATE TABLE reviews CASCADE;")

def downgrade():
    # Nothing to downgrade to, optional: recreate empty schema
    op.execute("DROP SCHEMA public CASCADE;")
    op.execute("CREATE SCHEMA public;")
