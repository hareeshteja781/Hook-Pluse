from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0003_delivery_attempts"
down_revision = "0002_webhook_ingestion"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        "delivery_attempts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("http_status", sa.Integer(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("response_body", sa.Text(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["event_id"], ["webhook_events.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_id", "attempt_number", name="uq_delivery_attempt_event_attempt"),
    )
    op.create_index("ix_delivery_attempts_event_id", "delivery_attempts", ["event_id"], unique=False)

def downgrade() -> None:
    op.drop_index("ix_delivery_attempts_event_id", table_name="delivery_attempts")
    op.drop_table("delivery_attempts")
