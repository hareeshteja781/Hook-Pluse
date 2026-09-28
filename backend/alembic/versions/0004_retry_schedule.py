from alembic import op
import sqlalchemy as sa

revision = "0004_retry_schedule"
down_revision = "0003_delivery_attempts"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column("webhook_events", sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_webhook_events_next_retry_at", "webhook_events", ["next_retry_at"], unique=False)

def downgrade() -> None:
    op.drop_index("ix_webhook_events_next_retry_at", table_name="webhook_events")
    op.drop_column("webhook_events", "next_retry_at")
