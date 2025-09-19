"""Initial migration

Revision ID: 001
Revises:
Create Date: 2024-12-19 15:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create recipes table
    op.create_table(
        "recipes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("calories", sa.Float(), nullable=False),
        sa.Column("protein", sa.Float(), nullable=False),
        sa.Column("fat", sa.Float(), nullable=False),
        sa.Column("carbs", sa.Float(), nullable=False),
        sa.Column("ingredients", sa.Text(), nullable=False),
        sa.Column(
            "category",
            sa.Enum("BREAKFAST", "MAIN_DISH", "DESSERT", name="categoryenum"),
            nullable=False,
        ),
        sa.Column("instructions", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("recipes")
    op.execute("DROP TYPE IF EXISTS categoryenum")
