from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("model_invocations", sa.Column("conversation_id", sa.String(length=36)))
    op.add_column("model_invocations", sa.Column("assistant_message_id", sa.String(length=36)))
    op.add_column("model_invocations", sa.Column("context_snapshot", sa.JSON()))
    op.add_column("model_invocations", sa.Column("selected_message_ids", sa.JSON()))
    op.create_index(
        "ix_model_invocations_conversation_id", "model_invocations", ["conversation_id"]
    )
    op.create_index(
        "ix_model_invocations_assistant_message_id", "model_invocations", ["assistant_message_id"]
    )

    op.create_table(
        "conversations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("owner_id", sa.String(length=128), nullable=False),
        sa.Column("title", sa.String(length=256), nullable=True),
        sa.Column("head_message_id", sa.String(length=36), nullable=True),
        sa.Column("source_conversation_id", sa.String(length=36), nullable=True),
        sa.Column("source_message_id", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_conversations_owner_id", "conversations", ["owner_id"])

    op.create_table(
        "conversation_messages",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("conversation_id", sa.String(length=36), nullable=False),
        sa.Column("parent_id", sa.String(length=36), nullable=True),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("parts", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("model", sa.String(length=256), nullable=True),
        sa.Column("model_name", sa.String(length=256), nullable=True),
        sa.Column("provider", sa.String(length=128), nullable=True),
        sa.Column("prompt_name", sa.String(length=128), nullable=True),
        sa.Column("prompt_version", sa.Integer(), nullable=True),
        sa.Column("request_settings", sa.JSON(), nullable=True),
        sa.Column("invocation_id", sa.String(length=36), nullable=True),
        sa.Column("source_conversation_id", sa.String(length=36), nullable=True),
        sa.Column("source_message_id", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parent_id"], ["conversation_messages.id"]),
        sa.ForeignKeyConstraint(["invocation_id"], ["model_invocations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("conversation_id", "sequence", name="uq_conversation_message_sequence"),
    )
    op.create_index(
        "ix_conversation_messages_conversation_id", "conversation_messages", ["conversation_id"]
    )
    op.create_index(
        "ix_conversation_messages_parent",
        "conversation_messages",
        ["conversation_id", "parent_id"],
    )

    op.create_table(
        "conversation_requests",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("conversation_id", sa.String(length=36), nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("request_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("user_message_id", sa.String(length=36), nullable=False),
        sa.Column("assistant_message_id", sa.String(length=36), nullable=False),
        sa.Column("invocation_id", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("error_message", sa.String(length=256), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_message_id"], ["conversation_messages.id"]),
        sa.ForeignKeyConstraint(["assistant_message_id"], ["conversation_messages.id"]),
        sa.ForeignKeyConstraint(["invocation_id"], ["model_invocations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "conversation_id", "idempotency_key", name="uq_conversation_request_idempotency"
        ),
    )
    op.create_index(
        "ix_conversation_requests_conversation_id", "conversation_requests", ["conversation_id"]
    )
    op.create_index(
        "ix_conversation_requests_messages",
        "conversation_requests",
        ["user_message_id", "assistant_message_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_conversation_requests_messages", table_name="conversation_requests")
    op.drop_index("ix_conversation_requests_conversation_id", table_name="conversation_requests")
    op.drop_table("conversation_requests")
    op.drop_index("ix_conversation_messages_parent", table_name="conversation_messages")
    op.drop_index("ix_conversation_messages_conversation_id", table_name="conversation_messages")
    op.drop_table("conversation_messages")
    op.drop_index("ix_conversations_owner_id", table_name="conversations")
    op.drop_table("conversations")
    op.drop_index("ix_model_invocations_assistant_message_id", table_name="model_invocations")
    op.drop_index("ix_model_invocations_conversation_id", table_name="model_invocations")
    op.drop_column("model_invocations", "selected_message_ids")
    op.drop_column("model_invocations", "context_snapshot")
    op.drop_column("model_invocations", "assistant_message_id")
    op.drop_column("model_invocations", "conversation_id")
