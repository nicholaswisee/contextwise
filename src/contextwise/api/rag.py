"""Owner-protected collection indexing, retrieval, citation, and debug routes."""

from typing import Annotated, NoReturn

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError

from contextwise.api.dependencies import get_rag_service, require_owner
from contextwise.application.rag.chunking import ChunkConfig
from contextwise.application.rag.embeddings import EmbeddingError
from contextwise.application.rag.service import RagService, RetrievalConfig, RetrievalResult
from contextwise.infrastructure.models import RagRetrievalRun
from contextwise.infrastructure.rag import RagConflictError

router = APIRouter(prefix="/v1", tags=["rag"])


class CollectionInput(BaseModel):
    name: str = Field(min_length=1, max_length=128)


class CollectionView(BaseModel):
    id: str
    name: str
    active_index_id: str | None


class IndexInput(BaseModel):
    chunk: ChunkConfig = Field(default_factory=ChunkConfig)
    embedding_model: str | None = None


class IndexView(BaseModel):
    id: str
    number: int
    chunk_count: int
    embedding_model: str


class QueryInput(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    config: RetrievalConfig = Field(default_factory=RetrievalConfig)
    generation_model: str = "extractive"


class RunView(BaseModel):
    id: str
    collection_id: str
    index_id: str | None
    index_number: int | None
    query: str
    config: dict[str, object]
    candidates: list[dict[str, object]]
    selected_evidence_ids: list[str]
    answer: str | None
    status: str
    latency_ms: int
    estimated_cost_usd: float | None


def _collection(row: object) -> CollectionView:
    return CollectionView.model_validate(row, from_attributes=True)


def _run(row: RagRetrievalRun) -> RunView:
    return RunView.model_validate(row, from_attributes=True)


def _raise_rag_error(error: Exception) -> NoReturn:
    if isinstance(error, RagConflictError):
        status = 404 if str(error) == "collection_not_found" else 409
        raise HTTPException(status_code=status, detail=str(error)) from error
    raise HTTPException(status_code=502, detail=str(error)) from error


@router.post("/rag/collections", response_model=CollectionView, status_code=201)
async def create_collection(
    body: CollectionInput,
    owner_id: Annotated[str, Depends(require_owner)],
    service: Annotated[RagService, Depends(get_rag_service)],
) -> CollectionView:
    try:
        return _collection(await service.repository.create_collection(owner_id, body.name))
    except IntegrityError as error:
        raise HTTPException(status_code=409, detail="collection_name_exists") from error


@router.get("/rag/collections", response_model=list[CollectionView])
async def list_collections(
    owner_id: Annotated[str, Depends(require_owner)],
    service: Annotated[RagService, Depends(get_rag_service)],
) -> list[CollectionView]:
    return [_collection(row) for row in await service.repository.list_collections(owner_id)]


@router.put("/rag/collections/{collection_id}/documents/{document_id}", status_code=204)
async def add_document(
    collection_id: str,
    document_id: str,
    owner_id: Annotated[str, Depends(require_owner)],
    service: Annotated[RagService, Depends(get_rag_service)],
) -> None:
    if not await service.repository.add_document(owner_id, collection_id, document_id):
        raise HTTPException(status_code=404, detail="collection_or_document_not_found")


@router.post("/rag/collections/{collection_id}/indexes", response_model=IndexView, status_code=201)
async def build_index(
    collection_id: str,
    body: IndexInput,
    owner_id: Annotated[str, Depends(require_owner)],
    service: Annotated[RagService, Depends(get_rag_service)],
) -> IndexView:
    try:
        index, count = await service.index(
            owner_id, collection_id, body.chunk, body.embedding_model
        )
    except (RagConflictError, EmbeddingError) as error:
        _raise_rag_error(error)
    return IndexView(
        id=index.id, number=index.number, chunk_count=count, embedding_model=index.embedding_model
    )


async def _query(
    collection_id: str,
    body: QueryInput,
    request: Request,
    owner_id: str,
    service: RagService,
    generation_model: str | None,
) -> RetrievalResult:
    try:
        return await service.retrieve(
            owner_id,
            collection_id,
            body.query,
            body.config,
            request.state.request_id,
            generation_model,
        )
    except (RagConflictError, EmbeddingError) as error:
        _raise_rag_error(error)
    except KeyError as error:
        raise HTTPException(status_code=422, detail="unknown_generation_model") from error


@router.post("/rag/collections/{collection_id}/retrieve", response_model=RetrievalResult)
async def retrieve(
    collection_id: str,
    body: QueryInput,
    request: Request,
    owner_id: Annotated[str, Depends(require_owner)],
    service: Annotated[RagService, Depends(get_rag_service)],
) -> RetrievalResult:
    return await _query(collection_id, body, request, owner_id, service, None)


@router.post("/rag/collections/{collection_id}/ask", response_model=RetrievalResult)
async def ask(
    collection_id: str,
    body: QueryInput,
    request: Request,
    owner_id: Annotated[str, Depends(require_owner)],
    service: Annotated[RagService, Depends(get_rag_service)],
) -> RetrievalResult:
    return await _query(collection_id, body, request, owner_id, service, body.generation_model)


@router.get("/rag/runs/{run_id}", response_model=RunView)
async def get_run(
    run_id: str,
    owner_id: Annotated[str, Depends(require_owner)],
    service: Annotated[RagService, Depends(get_rag_service)],
) -> RunView:
    run = await service.repository.get_run(owner_id, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="run_not_found")
    return _run(run)


@router.get("/rag/evidence/{chunk_id}")
async def get_evidence(
    chunk_id: str,
    owner_id: Annotated[str, Depends(require_owner)],
    service: Annotated[RagService, Depends(get_rag_service)],
) -> dict[str, object]:
    row = await service.repository.get_evidence(owner_id, chunk_id)
    if row is None:
        raise HTTPException(status_code=404, detail="evidence_not_found")
    chunk, document = row
    return {
        "id": chunk.id,
        "filename": document.filename,
        "document_id": document.id,
        "version_id": chunk.version_id,
        "segment_id": chunk.segment_id,
        "page": chunk.page,
        "section": chunk.section,
        "source_start_offset": chunk.source_start_offset,
        "source_end_offset": chunk.source_end_offset,
        "segment_start_offset": chunk.segment_start_offset,
        "segment_end_offset": chunk.segment_end_offset,
        "text": chunk.text,
    }
