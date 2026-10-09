"""Collection scoped index publication, cosine retrieval, and durable run records."""

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from contextwise.infrastructure.models import (
    Document,
    DocumentSegment,
    DocumentVersion,
    RagChunk,
    RagCollection,
    RagCollectionDocument,
    RagIndex,
    RagRetrievalRun,
)


class RagConflictError(Exception):
    pass


class RagRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self.session_factory = session_factory

    async def create_collection(self, owner_id: str, name: str) -> RagCollection:
        row = RagCollection(
            id=str(uuid4()),
            owner_id=owner_id,
            name=name,
            active_index_id=None,
            created_at=datetime.now(UTC),
        )
        async with self.session_factory.begin() as session:
            session.add(row)
        return row

    async def list_collections(self, owner_id: str) -> tuple[RagCollection, ...]:
        async with self.session_factory() as session:
            return tuple(
                await session.scalars(
                    select(RagCollection)
                    .where(RagCollection.owner_id == owner_id)
                    .order_by(RagCollection.created_at)
                )
            )

    async def get_collection(self, owner_id: str, collection_id: str) -> RagCollection | None:
        async with self.session_factory() as session:
            result: RagCollection | None = await session.scalar(
                select(RagCollection).where(
                    RagCollection.id == collection_id, RagCollection.owner_id == owner_id
                )
            )
            return result

    async def add_document(self, owner_id: str, collection_id: str, document_id: str) -> bool:
        async with self.session_factory.begin() as session:
            collection = await session.scalar(
                select(RagCollection)
                .where(RagCollection.id == collection_id, RagCollection.owner_id == owner_id)
                .with_for_update()
            )
            document = await session.scalar(
                select(Document).where(Document.id == document_id, Document.owner_id == owner_id)
            )
            if collection is None or document is None:
                return False
            association = await session.get(RagCollectionDocument, (collection_id, document_id))
            if association is None:
                session.add(
                    RagCollectionDocument(collection_id=collection_id, document_id=document_id)
                )
                collection.active_index_id = None
            return True

    async def snapshot(
        self, owner_id: str, collection_id: str
    ) -> (
        tuple[RagCollection, list[tuple[Document, DocumentVersion, tuple[DocumentSegment, ...]]]]
        | None
    ):
        async with self.session_factory() as session:
            collection = await session.scalar(
                select(RagCollection).where(
                    RagCollection.id == collection_id, RagCollection.owner_id == owner_id
                )
            )
            if collection is None:
                return None
            documents = tuple(
                await session.scalars(
                    select(Document)
                    .join(RagCollectionDocument, RagCollectionDocument.document_id == Document.id)
                    .where(
                        RagCollectionDocument.collection_id == collection_id,
                        Document.owner_id == owner_id,
                    )
                    .order_by(Document.id)
                )
            )
            result: list[tuple[Document, DocumentVersion, tuple[DocumentSegment, ...]]] = []
            for document in documents:
                version = await session.scalar(
                    select(DocumentVersion)
                    .where(DocumentVersion.document_id == document.id)
                    .order_by(DocumentVersion.number.desc())
                    .limit(1)
                )
                if version is None or version.status != "completed":
                    raise RagConflictError("document_not_ready")
                segments = tuple(
                    await session.scalars(
                        select(DocumentSegment)
                        .where(DocumentSegment.version_id == version.id)
                        .order_by(DocumentSegment.ordinal)
                    )
                )
                result.append((document, version, segments))
            return collection, result

    async def publish(
        self,
        owner_id: str,
        collection_id: str,
        config: dict[str, object],
        embedding_model: str,
        membership: dict[str, str],
        chunks: list[RagChunk],
    ) -> RagIndex:
        async with self.session_factory.begin() as session:
            collection = await session.scalar(
                select(RagCollection)
                .where(RagCollection.id == collection_id, RagCollection.owner_id == owner_id)
                .with_for_update()
            )
            if collection is None:
                raise RagConflictError("collection_not_found")
            current_ids = set(
                await session.scalars(
                    select(RagCollectionDocument.document_id).where(
                        RagCollectionDocument.collection_id == collection_id
                    )
                )
            )
            if current_ids != set(membership):
                raise RagConflictError("collection_changed")
            number = await session.scalar(
                select(func.coalesce(func.max(RagIndex.number), 0)).where(
                    RagIndex.collection_id == collection_id
                )
            )
            index = RagIndex(
                id=str(uuid4()),
                collection_id=collection_id,
                number=int(number or 0) + 1,
                config=config,
                embedding_model=embedding_model,
                membership=membership,
                created_at=datetime.now(UTC),
            )
            session.add(index)
            await session.flush()
            for chunk in chunks:
                chunk.index_id = index.id
            session.add_all(chunks)
            collection.active_index_id = index.id
            return index

    async def search(
        self,
        owner_id: str,
        collection_id: str,
        index_id: str,
        vector: list[float],
        top_k: int,
        min_score: float,
    ) -> tuple[RagIndex | None, list[tuple[RagChunk, float]]]:
        async with self.session_factory() as session:
            collection = await session.scalar(
                select(RagCollection).where(
                    RagCollection.id == collection_id, RagCollection.owner_id == owner_id
                )
            )
            if collection is None:
                raise RagConflictError("collection_not_found")
            index = await session.get(RagIndex, index_id)
            if index is None or index.collection_id != collection_id:
                return None, []
            distance = RagChunk.embedding.cosine_distance(vector)
            rows = await session.execute(
                select(RagChunk, distance.label("distance"))
                .where(RagChunk.index_id == index.id, distance <= 1 - min_score)
                .order_by(distance, RagChunk.id)
                .limit(top_k)
            )
            return index, [(chunk, float(1 - value)) for chunk, value in rows]

    async def save_run(self, run: RagRetrievalRun) -> None:
        async with self.session_factory.begin() as session:
            session.add(run)

    async def get_run(self, owner_id: str, run_id: str) -> RagRetrievalRun | None:
        async with self.session_factory() as session:
            result: RagRetrievalRun | None = await session.scalar(
                select(RagRetrievalRun).where(
                    RagRetrievalRun.id == run_id, RagRetrievalRun.owner_id == owner_id
                )
            )
            return result

    async def get_evidence(self, owner_id: str, chunk_id: str) -> tuple[RagChunk, Document] | None:
        async with self.session_factory() as session:
            row = await session.execute(
                select(RagChunk, Document)
                .join(RagIndex, RagIndex.id == RagChunk.index_id)
                .join(RagCollection, RagCollection.id == RagIndex.collection_id)
                .join(Document, Document.id == RagChunk.document_id)
                .where(
                    RagChunk.id == chunk_id,
                    RagCollection.owner_id == owner_id,
                    Document.owner_id == owner_id,
                )
            )
            result = row.one_or_none()
            return (result[0], result[1]) if result is not None else None
