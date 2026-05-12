from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.configs.limiter_config import LimitConfig
from app.configs.llm_settings import CODEGEN_SYSTEM_PROMPT
from app.dependencies.db import get_cursor
from app.dependencies.limiter import limiter
from app.repositories.knowledge_repository import KnowledgeRepository
from app.schemas.knowledge import (
    KnowledgeDocumentResponse,
    KnowledgeDocumentsListResponse,
    KnowledgeType,
)
from app.utils.logging import Logger, APILog
from app.workers.runner import WorkerRunner

router = APIRouter(prefix="/knowledge", tags=["Knowledge"])
internal_router = APIRouter(prefix="/knowledge", tags=["Knowledge"])

logger = Logger.get_logger("api")


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
