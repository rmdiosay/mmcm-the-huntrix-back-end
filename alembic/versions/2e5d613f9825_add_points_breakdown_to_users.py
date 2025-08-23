"""Add points breakdown to users

Revision ID: 2e5d613f9825
Revises: 
Create Date: 2025-08-24 03:15:13.758770

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '2e5d613f9825'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('users', sa.Column('property_sale', sa.Integer(), nullable=True))
    op.add_column('users', sa.Column('property_rental', sa.Integer(), nullable=True))
    op.add_column('users', sa.Column('direct_referrals', sa.Integer(), nullable=True))
    op.add_column('users', sa.Column('secondary_referrals', sa.Integer(), nullable=True))
    op.add_column('users', sa.Column('tertiary_referrals', sa.Integer(), nullable=True))
    op.add_column('users', sa.Column('positive_reviews', sa.Integer(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'property_sale')
    op.drop_column('users', 'property_rental')
    op.drop_column('users', 'direct_referrals')
    op.drop_column('users', 'secondary_referrals')
    op.drop_column('users', 'tertiary_referrals')
    op.drop_column('users', 'positive_reviews')
