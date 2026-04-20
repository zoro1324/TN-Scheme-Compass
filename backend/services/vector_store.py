import hashlib
import re
from typing import Iterable

import chromadb
import numpy as np

from backend.config import settings
from backend.models import Scheme


class SchemeVectorStore:
    embedding_dim = 384

    def __init__(self):
        self.client = chromadb.PersistentClient(path=settings.chroma_path)
        self.collection = self.client.get_or_create_collection(
            name=settings.chroma_collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def _embed(self, text: str) -> list[float]:
        vector = np.zeros(self.embedding_dim, dtype=np.float32)
        tokens = re.findall(r"[\\w']+", (text or "").lower())
        if not tokens:
            return vector.tolist()

        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "little") % self.embedding_dim
            vector[index] += 1.0

        norm = float(np.linalg.norm(vector))
        if norm > 0:
            vector /= norm

        return vector.tolist()

    def _scheme_text(self, scheme: Scheme) -> str:
        parts: Iterable[str | None] = [
            scheme.scheme_name,
            scheme.scheme_level,
            scheme.administering_body,
            scheme.target_beneficiaries,
            scheme.eligibility_criteria,
            scheme.income_limit,
            scheme.age_range,
            scheme.benefit_description,
            scheme.benefit_amount,
            scheme.application_process,
            scheme.required_documents,
            scheme.notes,
        ]
        return " ".join([p for p in parts if p])

    def index_schemes(self, schemes: list[Scheme]) -> int:
        if not schemes:
            return 0

        # Chroma versions differ in delete-filter behavior; recreating collection is stable.
        try:
            self.client.delete_collection(name=settings.chroma_collection_name)
        except Exception:
            pass

        self.collection = self.client.get_or_create_collection(
            name=settings.chroma_collection_name,
            metadata={"hnsw:space": "cosine"},
        )

        ids = []
        docs = []
        embeddings = []
        metadatas = []

        for scheme in schemes:
            text = self._scheme_text(scheme)
            ids.append(str(scheme.id))
            docs.append(text)
            embeddings.append(self._embed(text))
            metadatas.append({"scheme_id": scheme.scheme_id, "scheme_name": scheme.scheme_name})

        self.collection.add(ids=ids, documents=docs, embeddings=embeddings, metadatas=metadatas)
        return len(ids)

    def query(self, query_text: str, top_k: int) -> list[int]:
        query_embedding = self._embed(query_text)
        result = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["metadatas", "distances"],
        )

        ids = result.get("ids", [[]])
        if not ids or not ids[0]:
            return []

        parsed: list[int] = []
        for value in ids[0]:
            try:
                parsed.append(int(value))
            except ValueError:
                continue
        return parsed
