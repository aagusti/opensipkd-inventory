"""alter users date fields with time zone

Revision ID: 35f453a443
Revises: 
Create Date: 2015-02-06 15:59:42.859656

"""

# revision identifiers, used by Alembic.
revision = '35f453a443'
down_revision = None
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column('users', 'last_login_date',
        type_=sa.DateTime(timezone=True),
        existing_type=sa.DateTime(timezone=False))
    op.alter_column('users', 'registered_date',
        type_=sa.DateTime(timezone=True),
        existing_type=sa.DateTime(timezone=False))

def downgrade():
    pass
