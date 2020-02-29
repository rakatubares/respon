"""empty message

Revision ID: b13e23a07adb
Revises: 8fabbc576a89
Create Date: 2020-02-29 09:26:09.656710

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'b13e23a07adb'
down_revision = '8fabbc576a89'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('log',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('hash', sa.String(length=32), nullable=False),
    sa.Column('status', sa.String(length=32), nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_log_hash'), 'log', ['hash'], unique=False)
    op.create_index(op.f('ix_log_status'), 'log', ['status'], unique=False)
    op.drop_index('ix_login_hash', table_name='login')
    op.drop_index('ix_login_status', table_name='login')
    op.drop_table('login')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('login',
    sa.Column('id', mysql.INTEGER(display_width=11), autoincrement=True, nullable=False),
    sa.Column('status', mysql.VARCHAR(length=32), nullable=False),
    sa.Column('created_at', mysql.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.Column('hash', mysql.VARCHAR(length=32), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    mysql_default_charset='utf8',
    mysql_engine='InnoDB'
    )
    op.create_index('ix_login_status', 'login', ['status'], unique=False)
    op.create_index('ix_login_hash', 'login', ['hash'], unique=False)
    op.drop_index(op.f('ix_log_status'), table_name='log')
    op.drop_index(op.f('ix_log_hash'), table_name='log')
    op.drop_table('log')
    # ### end Alembic commands ###