import json
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.configs.limiter_config import LimitConfig
from app.dependencies.db import get_cursor
from app.dependencies.limiter import limiter
from app.repositories.knowledge_repository import KnowledgeRepository
from app.schemas.knowledge import (
    KnowledgeDocumentCreate,
    KnowledgeDocumentResponse,
    KnowledgeDocumentsListResponse,
    KnowledgeDocument,
    KnowledgeType,
    SeedKnowledgeResponse,
)
from app.services.rag_service import RAGService

router = APIRouter(prefix="/knowledge", tags=["Knowledge"])

@router.post("",
             status_code=status.HTTP_201_CREATED)
@limiter.limit(LimitConfig.STRICT)
def create_document(request: Request,
                    body: KnowledgeDocumentCreate,
                    cursor=Depends(get_cursor)) -> KnowledgeDocumentResponse:
    document_id = uuid4()
    embedding = RAGService.embed_text(body.content)
    KnowledgeRepository.create_document(
        cursor, document_id, body.content, body.doc_type.value, body.title, embedding
    )
    document = KnowledgeDocument(
        document_id=document_id,
        content=body.content,
        doc_type=body.doc_type,
        title=body.title,
    )
    return KnowledgeDocumentResponse(document=document)


@router.post("/seed", status_code=status.HTTP_200_OK)
@limiter.limit(LimitConfig.STRICT)
def seed_knowledge(request: Request, cursor=Depends(get_cursor)) -> SeedKnowledgeResponse:
    examples_dir = Path(__file__).resolve().parent.parent / "examples"
    index = json.loads((examples_dir / "index.json").read_text(encoding="utf-8"))

    inserted = 0
    skipped = 0
    for entry in index:
        document_id = UUID(entry["document_id"])
        if KnowledgeRepository.document_exists(cursor, document_id):
            skipped += 1
            continue
        content = (examples_dir / entry["file"]).read_text(encoding="utf-8")
        embedding = RAGService.embed_text(content)
        KnowledgeRepository.create_document(
            cursor, document_id, content, entry["doc_type"], entry["title"], embedding
        )
        inserted += 1
    return SeedKnowledgeResponse(inserted=inserted, skipped=skipped)


@router.get("/{document_id}")
@limiter.limit(LimitConfig.NORMAL)
def get_document(request: Request,
                 document_id: UUID,
                 cursor=Depends(get_cursor)) -> KnowledgeDocumentResponse:
    doc = KnowledgeRepository.get_document(cursor, document_id)
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document not found. (document_id={document_id})",
        )
    return KnowledgeDocumentResponse(document=doc)

@router.get("")
@limiter.limit(LimitConfig.NORMAL)
def get_documents(
    request: Request,
    doc_type: KnowledgeType,
    cursor=Depends(get_cursor),
) -> KnowledgeDocumentsListResponse:
    docs = KnowledgeRepository.get_documents(cursor, doc_type.value)
    return KnowledgeDocumentsListResponse(documents=docs)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit(LimitConfig.STRICT)
def delete_document(request: Request,
                    document_id: UUID,
                    cursor=Depends(get_cursor)) -> None:
    deleted = KnowledgeRepository.delete_document(cursor, document_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document not found. (document_id={document_id})",
        )
