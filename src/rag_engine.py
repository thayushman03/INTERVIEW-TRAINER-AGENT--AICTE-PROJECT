"""
rag_engine.py
-------------
RAG (Retrieval-Augmented Generation) pipeline.

Uses ChromaDB as the vector store and sentence-transformers for local
embeddings. The knowledge base is seeded on first run; subsequent runs
load the persisted collection.
"""

import logging
import os
from typing import Optional

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

from src.config import CHROMA_PERSIST_DIR, EMBEDDING_MODEL, RAG_TOP_K
from src.knowledge_base import (
    TECHNICAL_QUESTIONS,
    BEHAVIORAL_QUESTIONS,
    HR_GUIDELINES,
    EXPERIENCE_LEVELS,
)

logger = logging.getLogger(__name__)

# Collection names
COLLECTION_TECHNICAL = "technical_questions"
COLLECTION_BEHAVIORAL = "behavioral_questions"
COLLECTION_HR = "hr_guidelines"


class RAGEngine:
    """
    Manages the ChromaDB vector store and provides semantic search
    over the interview knowledge base.
    """

    def __init__(self, persist_dir: Optional[str] = None):
        self.persist_dir = persist_dir or CHROMA_PERSIST_DIR
        os.makedirs(self.persist_dir, exist_ok=True)

        # Local embedding model – no external API needed
        logger.info("Loading embedding model: %s", EMBEDDING_MODEL)
        self.embedder = SentenceTransformer(EMBEDDING_MODEL)

        # Persistent ChromaDB client
        self.client = chromadb.PersistentClient(
            path=self.persist_dir,
            settings=Settings(anonymized_telemetry=False),
        )

        self._collections: dict[str, chromadb.Collection] = {}
        self._seed_knowledge_base()

    # ------------------------------------------------------------------
    # Seeding
    # ------------------------------------------------------------------

    def _seed_knowledge_base(self) -> None:
        """Populate ChromaDB with all knowledge base documents."""
        self._seed_technical_questions()
        self._seed_behavioral_questions()
        self._seed_hr_guidelines()
        logger.info("Knowledge base seeded successfully.")

    def _get_or_create_collection(self, name: str) -> chromadb.Collection:
        if name not in self._collections:
            self._collections[name] = self.client.get_or_create_collection(
                name=name,
                metadata={"hnsw:space": "cosine"},
            )
        return self._collections[name]

    def _upsert_documents(
        self,
        collection: chromadb.Collection,
        documents: list[str],
        metadatas: list[dict],
        ids: list[str],
    ) -> None:
        """Embed and upsert documents; skip if already present."""
        existing_ids = set(collection.get(ids=ids)["ids"])
        new_docs, new_metas, new_ids = [], [], []
        for doc, meta, doc_id in zip(documents, metadatas, ids):
            if doc_id not in existing_ids:
                new_docs.append(doc)
                new_metas.append(meta)
                new_ids.append(doc_id)

        if not new_docs:
            return

        embeddings = self.embedder.encode(new_docs, show_progress_bar=False).tolist()
        collection.upsert(
            documents=new_docs,
            embeddings=embeddings,
            metadatas=new_metas,
            ids=new_ids,
        )
        logger.debug("Upserted %d documents into '%s'", len(new_docs), collection.name)

    def _seed_technical_questions(self) -> None:
        col = self._get_or_create_collection(COLLECTION_TECHNICAL)
        docs, metas, ids = [], [], []
        for role, questions in TECHNICAL_QUESTIONS.items():
            for i, item in enumerate(questions):
                doc_id = f"tech_{role}_{i}"
                docs.append(item["q"])
                metas.append({"role": role, "topic": item["topic"], "type": "technical"})
                ids.append(doc_id)
        self._upsert_documents(col, docs, metas, ids)

    def _seed_behavioral_questions(self) -> None:
        col = self._get_or_create_collection(COLLECTION_BEHAVIORAL)
        docs, metas, ids = [], [], []
        for i, item in enumerate(BEHAVIORAL_QUESTIONS):
            docs.append(item["q"])
            metas.append({
                "category": item["category"],
                "framework": item["framework"],
                "tip": item["tip"],
                "type": "behavioral",
            })
            ids.append(f"behav_{i}")
        self._upsert_documents(col, docs, metas, ids)

    def _seed_hr_guidelines(self) -> None:
        col = self._get_or_create_collection(COLLECTION_HR)
        docs, metas, ids = [], [], []
        for i, item in enumerate(HR_GUIDELINES):
            docs.append(f"{item['title']}\n{item['content']}")
            metas.append({"title": item["title"], "type": "hr_guideline"})
            ids.append(f"hr_{i}")
        self._upsert_documents(col, docs, metas, ids)

    # ------------------------------------------------------------------
    # Query API
    # ------------------------------------------------------------------

    def query_technical(
        self, query: str, role: Optional[str] = None, top_k: int = RAG_TOP_K
    ) -> list[dict]:
        """Retrieve relevant technical interview questions."""
        col = self._get_or_create_collection(COLLECTION_TECHNICAL)
        embedding = self.embedder.encode([query], show_progress_bar=False).tolist()

        where_filter = {"role": role} if role else None
        results = col.query(
            query_embeddings=embedding,
            n_results=min(top_k, col.count()),
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )
        return self._format_results(results)

    def query_behavioral(self, query: str, top_k: int = RAG_TOP_K) -> list[dict]:
        """Retrieve relevant behavioral interview questions."""
        col = self._get_or_create_collection(COLLECTION_BEHAVIORAL)
        embedding = self.embedder.encode([query], show_progress_bar=False).tolist()
        results = col.query(
            query_embeddings=embedding,
            n_results=min(top_k, col.count()),
            include=["documents", "metadatas", "distances"],
        )
        return self._format_results(results)

    def query_hr_guidelines(self, query: str, top_k: int = 3) -> list[dict]:
        """Retrieve HR guidelines relevant to a query."""
        col = self._get_or_create_collection(COLLECTION_HR)
        embedding = self.embedder.encode([query], show_progress_bar=False).tolist()
        results = col.query(
            query_embeddings=embedding,
            n_results=min(top_k, col.count()),
            include=["documents", "metadatas", "distances"],
        )
        return self._format_results(results)

    def add_custom_document(
        self, text: str, metadata: dict, doc_id: str
    ) -> None:
        """Add a custom document (e.g. parsed resume content) to a dedicated collection."""
        col = self.client.get_or_create_collection(
            name="custom_docs",
            metadata={"hnsw:space": "cosine"},
        )
        embedding = self.embedder.encode([text], show_progress_bar=False).tolist()
        col.upsert(documents=[text], embeddings=embedding, metadatas=[metadata], ids=[doc_id])

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _format_results(results: dict) -> list[dict]:
        """Flatten ChromaDB query results into a list of dicts."""
        output = []
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        for doc, meta, dist in zip(docs, metas, distances):
            output.append({
                "text": doc,
                "metadata": meta,
                "relevance_score": round(1 - dist, 4),
            })
        return output


# Module-level singleton
_rag_instance: Optional[RAGEngine] = None


def get_rag_engine() -> RAGEngine:
    """Return (or create) the module-level RAGEngine singleton."""
    global _rag_instance
    if _rag_instance is None:
        _rag_instance = RAGEngine()
    return _rag_instance
