from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.configs.limiter_config import LimitConfig
from app.configs.llm_settings import CODEGEN_SYSTEM_PROMPT
from app.dependencies.db import get_cursor
from app.dependencies.limiter import limiter
from app.repositories.knowledge_repository import KnowledgeRepository
from app.schemas.knowledge import (
    KnowledgeDocumentCreate,
    KnowledgeDocumentResponse,
    KnowledgeDocumentsListResponse,
    KnowledgeType,
)
from app.utils.logging import Logger, APILog
from app.workers.runner import WorkerRunner

router = APIRouter(prefix="/knowledge", tags=["Knowledge"])
internal_router = APIRouter(prefix="/knowledge", tags=["Knowledge"])

logger = Logger.get_logger("api")

@internal_router.post("", status_code=status.HTTP_202_ACCEPTED)
@limiter.limit(LimitConfig.STRICT)
def create_document(request: Request, body: KnowledgeDocumentCreate) -> dict:
    document_id = uuid4()
    WorkerRunner.handle_create_document(
        document_id, body.content, body.doc_type.value, body.title
    )
    logger.info(APILog(
        operation="create_knowledge_document",
        event="Knowledge document creation queued",
        context={"document_id": str(document_id),"title": str(body.title),"doc_type":str(body.doc_type.value)},
    ))
    return {"document_id": str(document_id), "message": "Document creation queued."}


@internal_router.post("/seed", status_code=status.HTTP_202_ACCEPTED)
@limiter.limit(LimitConfig.STRICT)
def seed_knowledge(request: Request) -> dict:
    WorkerRunner.handle_seed()
    logger.info(APILog(
        operation="seed_knowledge",
        event="Knowledge seeding queued",
    ))
    return {"message": "Knowledge seeding queued."}


@router.get("/system-prompt")
@limiter.limit(LimitConfig.NORMAL)
def get_system_prompt(request: Request) -> dict:
    return {"codegen_prompt": CODEGEN_SYSTEM_PROMPT}


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


@internal_router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
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
    logger.info(APILog(
        operation="delete_knowledge_document",
        event="Knowledge document deleted",
        context={"document_id": str(document_id)},
    ))
