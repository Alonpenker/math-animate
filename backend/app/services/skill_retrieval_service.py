from langchain_core.tools import BaseTool, tool

from app.configs.llm_settings import MAX_TOOL_LOADS, RAG_EXAMPLE_CAP, RAG_RULE_CAP, RAG_TEMPLATE_CAP
from app.llm_knowledge.skill_documents import read_knowledge_file
from app.repositories.knowledge_repository import KnowledgeRepository
from app.schemas.knowledge import CandidateResult, KnowledgeDocumentSeed, KnowledgeType
from app.services.rag_service import RAGService


class SkillRetrievalService:
    UNKNOWN_OR_NON_CANDIDATE_ERROR = "unknown or non-candidate"
    DUPLICATE_LOAD_ERROR = "already loaded"
    LOAD_LIMIT_ERROR = "load limit reached"

    @staticmethod
    def retrieve(cursor, plan_text: str) -> CandidateResult:
        embedding = RAGService.embed_text(plan_text)
        return CandidateResult(
            candidate_rules=KnowledgeRepository.search_similar(
                cursor, embedding, KnowledgeType.RULE.value, RAG_RULE_CAP
            ),
            candidate_templates=KnowledgeRepository.search_similar(
                cursor, embedding, KnowledgeType.TEMPLATE.value, RAG_TEMPLATE_CAP
            ),
            candidate_examples=KnowledgeRepository.search_similar(
                cursor, embedding, KnowledgeType.EXAMPLE.value, RAG_EXAMPLE_CAP
            ),
        )

    @staticmethod
    def make_load_skill_document(candidates: dict[str, KnowledgeDocumentSeed]) -> BaseTool:
        loaded: set[str] = set()

        @tool
        def load_skill_document(title: str) -> str:
            """Load the markdown content of a skill document by its title."""
            if title not in candidates:
                return f"Error: {SkillRetrievalService.UNKNOWN_OR_NON_CANDIDATE_ERROR} document title '{title}'"
            if title in loaded:
                return f"Error: '{title}' was {SkillRetrievalService.DUPLICATE_LOAD_ERROR} in this call"
            if len(loaded) >= MAX_TOOL_LOADS:
                return f"Error: skill document {SkillRetrievalService.LOAD_LIMIT_ERROR} ({MAX_TOOL_LOADS})"
            loaded.add(title)
            return read_knowledge_file(candidates[title].path)

        load_skill_document.metadata = {"available_optional_titles": list(candidates.keys())}
        return load_skill_document
