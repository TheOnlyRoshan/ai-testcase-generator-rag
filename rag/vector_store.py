from langchain_community.vectorstores import FAISS
from rag.embedding_service import EmbeddingService


class VectorStore:

    def create(self, documents):

        embedding_service = EmbeddingService()

        vector_db = FAISS.from_documents(
            documents,
            embedding_service
        )

        return vector_db