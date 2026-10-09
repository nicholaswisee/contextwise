"""Versioned dense retrieval with owner-scoped collections and trace records."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import VECTOR

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "rag_collections",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("owner_id", sa.String(128), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("active_index_id", sa.String(36)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("owner_id", "name", name="uq_rag_collection_owner_name"),
    )
    op.create_index("ix_rag_collections_owner_id", "rag_collections", ["owner_id"])
    op.create_table(
        "rag_collection_documents",
        sa.Column(
            "collection_id",
            sa.String(36),
            sa.ForeignKey("rag_collections.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "document_id",
            sa.String(36),
            sa.ForeignKey("documents.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )
    op.create_table(
        "rag_indexes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "collection_id",
            sa.String(36),
            sa.ForeignKey("rag_collections.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("config", sa.JSON(), nullable=False),
        sa.Column("embedding_model", sa.String(128), nullable=False),
        sa.Column("membership", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("collection_id", "number", name="uq_rag_index_number"),
    )
    op.create_index("ix_rag_indexes_collection_id", "rag_indexes", ["collection_id"])
    op.create_table(
        "rag_chunks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "index_id",
            sa.String(36),
            sa.ForeignKey("rag_indexes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("document_id", sa.String(36), nullable=False),
        sa.Column("version_id", sa.String(36), nullable=False),
        sa.Column("segment_id", sa.String(36), nullable=False),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("text", sa.String(), nullable=False),
        sa.Column("page", sa.Integer()),
        sa.Column("section", sa.String(255)),
        sa.Column("source_start_offset", sa.Integer(), nullable=False),
        sa.Column("source_end_offset", sa.Integer(), nullable=False),
        sa.Column("segment_start_offset", sa.Integer(), nullable=False),
        sa.Column("segment_end_offset", sa.Integer(), nullable=False),
        sa.Column("embedding", VECTOR(256), nullable=False),
        sa.UniqueConstraint("index_id", "segment_id", "ordinal", name="uq_rag_chunk_identity"),
    )
    op.create_index("ix_rag_chunks_index_id", "rag_chunks", ["index_id"])
    op.create_index(
        "ix_rag_chunks_embedding_cosine",
        "rag_chunks",
        ["embedding"],
        postgresql_using="hnsw",
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )
    op.create_table(
        "rag_retrieval_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("owner_id", sa.String(128), nullable=False),
        sa.Column("collection_id", sa.String(36), nullable=False),
        sa.Column("index_id", sa.String(36)),
        sa.Column("index_number", sa.Integer()),
        sa.Column("query", sa.String(2000), nullable=False),
        sa.Column("config", sa.JSON(), nullable=False),
        sa.Column("candidates", sa.JSON(), nullable=False),
        sa.Column("selected_evidence_ids", sa.JSON(), nullable=False),
        sa.Column("answer", sa.String()),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column("estimated_cost_usd", sa.Float()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_rag_retrieval_runs_owner_id", "rag_retrieval_runs", ["owner_id"])


def downgrade() -> None:
    op.drop_table("rag_retrieval_runs")
    op.drop_table("rag_chunks")
    op.drop_table("rag_indexes")
    op.drop_table("rag_collection_documents")
    op.drop_table("rag_collections")
