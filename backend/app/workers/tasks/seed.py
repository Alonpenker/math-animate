from psycopg2.errors import UniqueViolation

from app.dependencies.db import get_worker_cursor
from app.llm_knowledge.skill_documents import LLMKNOWLEDGE_DIR, REGISTRY
from app.repositories.knowledge_repository import KnowledgeRepository
from app.services.rag_service import RAGService
from app.utils.logging import Logger, WorkerLog

logger = Logger.get_logger("worker")


def seed_knowledge() -> None:
    inserted = skipped = 0
    with get_worker_cursor() as cursor:
        for entry in REGISTRY:
            if KnowledgeRepository.document_exists(cursor, entry.document_id):
                skipped += 1
                continue

            content = (LLMKNOWLEDGE_DIR / entry.path).read_text(encoding="utf-8")
            embedding = RAGService.embed_text(content)
            try:
                KnowledgeRepository.create_document(
                    cursor,
                    document_id=entry.document_id,
                    doc_type=entry.doc_type.value,
                    title=entry.title,
                    embedding=embedding,
                    category=entry.category,
                    priority=entry.priority,
                    tags=entry.tags,
                )
                inserted += 1
            except UniqueViolation:
                skipped += 1
    logger.info(WorkerLog(
        operation="seed_knowledge",
        event="Seed complete",
        context={"inserted": inserted, "skipped": skipped},
    ))
