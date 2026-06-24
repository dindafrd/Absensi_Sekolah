"""baseline schema

Revision ID: c03252932fc2
Revises: 
Create Date: 2026-06-05 07:44:54.989154

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c03252932fc2'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_names = set(inspector.get_table_names())

    if 'users' not in table_names:
        op.create_table(
            'users',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('username', sa.String(length=80), nullable=False),
            sa.Column('password_hash', sa.String(length=255), nullable=False),
            sa.Column('full_name', sa.String(length=200), nullable=True),
            sa.Column('role', sa.String(length=20), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('last_login', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('username')
        )
        op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=False)

    if 'students' not in table_names:
        op.create_table(
            'students',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('student_id', sa.String(length=50), nullable=False),
            sa.Column('name', sa.String(length=200), nullable=False),
            sa.Column('class_name', sa.String(length=50), nullable=False),
            sa.Column('gender', sa.String(length=20), nullable=True),
            sa.Column('birth_place', sa.String(length=100), nullable=True),
            sa.Column('birth_date', sa.Date(), nullable=True),
            sa.Column('religion', sa.String(length=50), nullable=True),
            sa.Column('address', sa.Text(), nullable=True),
            sa.Column('num_photos', sa.Integer(), nullable=True),
            sa.Column('photos_path', sa.Text(), nullable=True),
            sa.Column('face_encodings', sa.LargeBinary(), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=True),
            sa.Column('added_date', sa.Date(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('student_id')
        )
        op.create_index(op.f('ix_students_class_name'), 'students', ['class_name'], unique=False)
        op.create_index(op.f('ix_students_student_id'), 'students', ['student_id'], unique=False)

    if 'settings' not in table_names:
        op.create_table(
            'settings',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('key', sa.String(length=100), nullable=False),
            sa.Column('value', sa.Text(), nullable=True),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('key')
        )
        op.create_index(op.f('ix_settings_key'), 'settings', ['key'], unique=False)

    if 'attendance' not in table_names:
        op.create_table(
            'attendance',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('student_id', sa.String(length=50), nullable=False),
            sa.Column('date', sa.Date(), nullable=False),
            sa.Column('time', sa.Time(), nullable=False),
            sa.Column('status', sa.String(length=20), nullable=True),
            sa.Column('session_type', sa.String(length=20), nullable=True),
            sa.Column('confidence', sa.Float(), nullable=True),
            sa.Column('marked_by', sa.String(length=20), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['student_id'], ['students.student_id'], ),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('student_id', 'date', 'session_type', name='uq_student_date_session')
        )
        op.create_index(op.f('ix_attendance_date'), 'attendance', ['date'], unique=False)
        op.create_index(op.f('ix_attendance_student_id'), 'attendance', ['student_id'], unique=False)
        op.create_index('idx_student_date', 'attendance', ['student_id', 'date'], unique=False)
        return

    inspector = sa.inspect(bind)
    unique_constraints = {c['name'] for c in inspector.get_unique_constraints('attendance')}
    if 'uq_student_date_session' not in unique_constraints:
        with op.batch_alter_table('attendance', schema=None) as batch_op:
            batch_op.create_unique_constraint('uq_student_date_session', ['student_id', 'date', 'session_type'])


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_names = set(inspector.get_table_names())

    if 'attendance' in table_names:
        op.drop_index('idx_student_date', table_name='attendance')
        op.drop_index(op.f('ix_attendance_student_id'), table_name='attendance')
        op.drop_index(op.f('ix_attendance_date'), table_name='attendance')
        op.drop_table('attendance')

    if 'settings' in table_names:
        op.drop_index(op.f('ix_settings_key'), table_name='settings')
        op.drop_table('settings')

    if 'students' in table_names:
        op.drop_index(op.f('ix_students_student_id'), table_name='students')
        op.drop_index(op.f('ix_students_class_name'), table_name='students')
        op.drop_table('students')

    if 'users' in table_names:
        op.drop_index(op.f('ix_users_username'), table_name='users')
        op.drop_table('users')
