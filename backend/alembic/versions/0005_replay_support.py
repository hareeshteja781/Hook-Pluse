from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0005_replay_support"
down_revision = "0004_retry_schedule"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column("webhook_events", sa.Column("replay_of_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index("ix_webhook_events_replay_of_id", "webhook_events", ["replay_of_id"], unique=False)
    op.create_foreign_key("fk_webhook_events_replay_of_id", "webhook_events", "webhook_events", ["replay_of_id"], ["id"], ondelete="SET NULL")

def downgrade() -> None:
    op.drop_constraint("fk_webhook_events_replay_of_id", "webhook_events", type_="foreignkey")
    op.drop_index("ix_webhook_events_replay_of_id", table_name="webhook_events")
    op.drop_column("webhook_events", "replay_of_id")
