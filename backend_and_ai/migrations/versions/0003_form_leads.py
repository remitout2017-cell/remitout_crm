"""form leads

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-28 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0003'
down_revision: Union[str, Sequence[str], None] = '0002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('form_leads',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('full_name', sa.String(length=200), nullable=False),
        sa.Column('purpose', sa.String(length=30), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('phone_number', sa.String(length=30), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_form_leads')),
    )
    op.create_index(op.f('ix_form_leads_purpose'), 'form_leads', ['purpose'], unique=False)
    op.create_index(op.f('ix_form_leads_email'), 'form_leads', ['email'], unique=False)

    op.create_table('form_lead_documents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('form_lead_id', sa.Integer(), nullable=False),
        sa.Column('slot', sa.String(length=20), nullable=False),
        sa.Column('label', sa.String(length=100), nullable=False),
        sa.Column('original_file_name', sa.String(length=255), nullable=False),
        sa.Column('mimetype', sa.String(length=100), nullable=False),
        sa.Column('size', sa.BigInteger(), nullable=False),
        sa.Column('content', sa.LargeBinary(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['form_lead_id'], ['form_leads.id'], name=op.f('fk_form_lead_documents_form_lead_id_form_leads'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_form_lead_documents')),
    )
    op.create_index(op.f('ix_form_lead_documents_form_lead_id'), 'form_lead_documents', ['form_lead_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_form_lead_documents_form_lead_id'), table_name='form_lead_documents')
    op.drop_table('form_lead_documents')
    op.drop_index(op.f('ix_form_leads_email'), table_name='form_leads')
    op.drop_index(op.f('ix_form_leads_purpose'), table_name='form_leads')
    op.drop_table('form_leads')
