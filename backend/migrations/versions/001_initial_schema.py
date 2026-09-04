"""Initial schema — users, shows, seasons, episodes, artworks, publish_runs

Revision ID: 001
Revises:
Create Date: 2026-09-04
"""
from alembic import op
import sqlalchemy as sa

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Users
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("username", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.Enum("editor", "admin", name="userrole"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("username"),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_username", "users", ["username"])

    # Shows
    op.create_table(
        "shows",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("slug", sa.String(500), nullable=False),
        sa.Column("synopsis", sa.Text(), nullable=True),
        sa.Column("section", sa.String(50), nullable=True),
        sa.Column("categories", sa.Text(), nullable=True),
        sa.Column("status", sa.Enum("draft", "published", name="showstatus"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug", name="uq_show_slug"),
    )
    op.create_index("ix_shows_slug", "shows", ["slug"], unique=True)

    # Seasons
    op.create_table(
        "seasons",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("show_id", sa.Integer(), nullable=False),
        sa.Column("season_number", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["show_id"], ["shows.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_seasons_show_id", "seasons", ["show_id"])

    # Episodes
    op.create_table(
        "episodes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("season_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("synopsis", sa.Text(), nullable=True),
        sa.Column("episode_number", sa.Integer(), nullable=False),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("language", sa.String(10), nullable=False),
        sa.Column("content_group", sa.String(500), nullable=False),
        sa.Column("status", sa.Enum("draft", "published", name="episodestatus"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["season_id"], ["seasons.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("content_group", "language", name="uq_content_group_language"),
    )
    op.create_index("ix_episodes_season_id", "episodes", ["season_id"])
    op.create_index("ix_episodes_content_group", "episodes", ["content_group"])

    # Artworks
    op.create_table(
        "artworks",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("show_id", sa.Integer(), nullable=True),
        sa.Column("episode_id", sa.Integer(), nullable=True),
        sa.Column("artwork_type", sa.String(20), nullable=False),
        sa.Column("storage_key", sa.String(1000), nullable=False),
        sa.Column("original_filename", sa.String(500), nullable=True),
        sa.Column("mime_type", sa.String(100), nullable=True),
        sa.Column("file_size", sa.Integer(), nullable=True),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["show_id"], ["shows.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["episode_id"], ["episodes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_artworks_show_id", "artworks", ["show_id"])
    op.create_index("ix_artworks_episode_id", "artworks", ["episode_id"])

    # Publish runs
    op.create_table(
        "publish_runs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("initiated_by", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("status", sa.Enum("success", "failed", name="publishstatus"), nullable=False),
        sa.Column("shows_count", sa.Integer(), nullable=True),
        sa.Column("episodes_count", sa.Integer(), nullable=True),
        sa.Column("catalogue_version", sa.String(255), nullable=True),
        sa.Column("errors", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["initiated_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_publish_runs_initiated_by", "publish_runs", ["initiated_by"])


def downgrade() -> None:
    op.drop_table("publish_runs")
    op.drop_table("artworks")
    op.drop_table("episodes")
    op.drop_table("seasons")
    op.drop_table("shows")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS publishstatus")
    op.execute("DROP TYPE IF EXISTS episodestatus")
    op.execute("DROP TYPE IF EXISTS showstatus")
    op.execute("DROP TYPE IF EXISTS userrole")
