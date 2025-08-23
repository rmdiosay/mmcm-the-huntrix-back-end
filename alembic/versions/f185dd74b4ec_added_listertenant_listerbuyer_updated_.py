"""Added ListerTenant, ListerBuyer, updated User and properties

Revision ID: f185dd74b4ec
Revises: 156a8ad21b7b
Create Date: 2025-08-24 05:34:04.613089

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f185dd74b4ec"
down_revision: Union[str, Sequence[str], None] = "156a8ad21b7b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # 1. Add new columns to users if they don't exist
    with op.get_context().autocommit_block():
        op.execute("""
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS sale INTEGER DEFAULT 0 NOT NULL
        """)
        op.execute("""
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS rental INTEGER DEFAULT 0 NOT NULL
        """)

    # 2. Safely alter rent_properties columns
    with op.get_context().autocommit_block():
        op.execute("""
            ALTER TABLE rent_properties
            ALTER COLUMN price TYPE FLOAT
            USING price::double precision
        """)
        op.execute("""
            ALTER TABLE rent_properties
            ALTER COLUMN lease_term TYPE INTEGER
            USING lease_term::integer
        """)

    # 3. Create ListerTenant table if not exists
    op.execute("""
        CREATE TABLE IF NOT EXISTS lister_tenants (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            rent_id UUID NOT NULL REFERENCES rent_properties(id),
            lister_id UUID NOT NULL REFERENCES users(id),
            tenant_id UUID NOT NULL REFERENCES users(id),
            created_at TIMESTAMP DEFAULT now() NOT NULL
        )
    """)

    # 4. Create ListerBuyer table if not exists
    op.execute("""
        CREATE TABLE IF NOT EXISTS lister_buyers (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            buy_id UUID NOT NULL REFERENCES buy_properties(id),
            lister_id UUID NOT NULL REFERENCES users(id),
            buyer_id UUID NOT NULL REFERENCES users(id),
            created_at TIMESTAMP DEFAULT now() NOT NULL
        )
    """)


def downgrade():
    # 1. Drop ListerBuyer and ListerTenant tables if they exist
    op.execute("DROP TABLE IF EXISTS lister_buyers CASCADE")
    op.execute("DROP TABLE IF EXISTS lister_tenants CASCADE")

    # 2. Revert rent_properties columns
    with op.get_context().autocommit_block():
        op.execute("""
            ALTER TABLE rent_properties
            ALTER COLUMN lease_term TYPE VARCHAR
            USING lease_term::varchar
        """)
        op.execute("""
            ALTER TABLE rent_properties
            ALTER COLUMN price TYPE VARCHAR
            USING price::varchar
        """)

    # 3. Remove columns from users if they exist
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS rental")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS sale")