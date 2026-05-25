from app.configs.llm_settings import RAG_EXAMPLE_CAP, RAG_RULE_CAP, RAG_TEMPLATE_CAP
from app.llm_knowledge.skill_documents import CORE_DOCUMENTS
from app.repositories.knowledge_repository import KnowledgeRepository
from app.schemas.knowledge import CandidateResult, KnowledgeDocument, KnowledgeType
from app.services.rag_service import RAGService


class SkillRetrievalService:
    UNKNOWN_OR_NON_CANDIDATE_ERROR = "unknown or non-candidate"
    DUPLICATE_LOAD_ERROR = "already loaded"
    LOAD_LIMIT_ERROR = "load limit reached"

    @staticmethod
    def retrieve(cursor, plan_text: str) -> CandidateResult:
        embedding = RAGService.embed_text(plan_text)
        core_document_ids = {doc.document_id for doc in CORE_DOCUMENTS}

        def exclude_core_documents(documents: list[KnowledgeDocument]) -> list[KnowledgeDocument]:
            return [
                document
                for document in documents
                if document.document_id not in core_document_ids
            ]

        return CandidateResult(
            candidate_rules=exclude_core_documents(KnowledgeRepository.search_similar(
                cursor, embedding, KnowledgeType.RULE.value, RAG_RULE_CAP
            )),
            candidate_templates=exclude_core_documents(KnowledgeRepository.search_similar(
                cursor, embedding, KnowledgeType.TEMPLATE.value, RAG_TEMPLATE_CAP
            )),
            candidate_examples=exclude_core_documents(KnowledgeRepository.search_similar(
                cursor, embedding, KnowledgeType.EXAMPLE.value, RAG_EXAMPLE_CAP
            )),
        )
