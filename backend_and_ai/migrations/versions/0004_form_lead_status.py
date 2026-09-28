"""form lead edubao status + phone index

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-28 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0004'
down_revision: Union[str, Sequence[str], None] = '0003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('form_leads', sa.Column('edubao_account_opened', sa.Boolean(), server_default='false', nullable=False))
    op.create_index(op.f('ix_form_leads_phone_number'), 'form_leads', ['phone_number'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_form_leads_phone_number'), table_name='form_leads')
    op.drop_column('form_leads', 'edubao_account_opened')
