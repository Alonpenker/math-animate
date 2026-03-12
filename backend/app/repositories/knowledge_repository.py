from typing import Optional, List
from uuid import UUID

import numpy as np

from app.repositories.repository import Repository
from app.schemas.knowledge import (
    KnowledgeDocument, KnowledgeDocumentSchema, KnowledgeType
)


class KnowledgeRepository(Repository):

    TABLE_NAME = "knowledge_documents"
    SCHEMA = KnowledgeDocumentSchema
    PRIMARY_KEY = "document_id"

    @classmethod
    def create_document(cls, cursor, document_id: UUID,
                        content: str, doc_type: str,
                        title: str, embedding: np.ndarray) -> None:
        cursor.execute(cls.insert(), (str(document_id), content, doc_type, title, embedding))

    @classmethod
    def get_document(cls, cursor, document_id: UUID) -> Optional[KnowledgeDocument]:
        cursor.execute(cls.get(), (str(document_id),))
        row = cursor.fetchone()
        if row is None:
            return None
        return KnowledgeDocument(
            document_id=row[KnowledgeDocumentSchema.DOCUMENT_ID.name],
            content=row[KnowledgeDocumentSchema.CONTENT.name],
            doc_type=KnowledgeType(row[KnowledgeDocumentSchema.DOC_TYPE.name]),
            title=row[KnowledgeDocumentSchema.TITLE.name],
        )
    
    @classmethod
    def get_documents(cls, cursor, doc_type: str) -> List[KnowledgeDocument]:
        cursor.execute(
            cls.get_all_by_field(KnowledgeDocumentSchema.DOC_TYPE.name),
            (doc_type,),
        )
        rows = cursor.fetchall()
        return [
            KnowledgeDocument(
                document_id=row[KnowledgeDocumentSchema.DOCUMENT_ID.name],
                content=row[KnowledgeDocumentSchema.CONTENT.name],
                doc_type=KnowledgeType(row[KnowledgeDocumentSchema.DOC_TYPE.name]),
                title=row[KnowledgeDocumentSchema.TITLE.name],
            )
            for row in rows
        ]

    @classmethod
    def delete_document(cls, cursor, document_id: UUID) -> bool:
        cursor.execute(cls.delete(), (str(document_id),))
        return cursor.rowcount > 0

    @classmethod
    def document_exists(cls, cursor, document_id: UUID) -> bool:
        cursor.execute(cls.get(), (str(document_id),))
        return cursor.fetchone() is not None

    @classmethod
    def search_similar(cls, cursor, embedding: np.ndarray,
                       doc_type: str, limit: int = 3) -> List[KnowledgeDocument]:
        cursor.execute(
            cls.search_by_vector(
                KnowledgeDocumentSchema.EMBEDDING.name,
                KnowledgeDocumentSchema.DOC_TYPE.name,
            ),
            (embedding, doc_type, limit),
        )
        rows = cursor.fetchall()
        return [
            KnowledgeDocument(
                document_id=row[KnowledgeDocumentSchema.DOCUMENT_ID.name],
                content=row[KnowledgeDocumentSchema.CONTENT.name],
                doc_type=KnowledgeType(row[KnowledgeDocumentSchema.DOC_TYPE.name]),
                title=row[KnowledgeDocumentSchema.TITLE.name],
            )
            for row in rows
        ]
