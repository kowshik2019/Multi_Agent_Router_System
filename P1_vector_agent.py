"""
agents/vector_agent.py
----------------------
VectorAgent — the semantic memory layer of the multi-agent system.

Responsibility:
  Given an incoming user query, embed it and find the closest matching
  department knowledge document via cosine similarity in a FAISS index.
  Returns a department suggestion + similarity score to the Router Agent.

How it works:
  1. On first run, embeds DEPARTMENT_DOCS from config and builds a FAISS index.
  2. On each query, embeds the query text and runs a nearest-neighbour search.
  3. Returns the top-matching department label and distance score.

This agent does NOT talk to the LLM — it is purely vector/embedding based,
making it fast, deterministic, and cheap to run on every request.
"""

from __future__ import annotations

import os
import json
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer
import faiss

from config.settings import DEPARTMENT_DOCS, EMBEDDING_MODEL, VECTOR_DB_PATH


class VectorAgent:
    """Semantic routing agent backed by FAISS + sentence-transformers."""

    INDEX_FILE = "dept_index.faiss"
    META_FILE  = "dept_meta.json"

    def __init__(self):
        self.model  = SentenceTransformer(EMBEDDING_MODEL)
        self.index  = None
        self.meta   = []          # list of {"content":..., "department":...}
        self._store = Path(VECTOR_DB_PATH)
        self._store.mkdir(parents=True, exist_ok=True)
        self._load_or_build()

    # ── Public API ────────────────────────────────────────────────────────────

    def suggest_department(self, query: str) -> dict:
        """
        Embed query and return the best-matching department.

        Returns
        -------
        dict  {"department": str, "similarity": float, "matched_doc": str}
        """
        vec = self._embed([query])
        distances, indices = self.index.search(vec, k=1)

        idx        = int(indices[0][0])
        distance   = float(distances[0][0])
        # FAISS inner-product on normalised vectors == cosine similarity
        similarity = round(float(distance), 4)

        hit = self.meta[idx]
        return {
            "department":   hit["department"],
            "similarity":   similarity,
            "matched_doc":  hit["content"][:120] + "...",
        }

    def add_documents(self, docs: list[dict]) -> None:
        """Hot-add new department documents and persist the updated index."""
        texts  = [d["content"] for d in docs]
        vecs   = self._embed(texts)
        self.index.add(vecs)
        self.meta.extend(docs)
        self._save()

    # ── Private helpers ───────────────────────────────────────────────────────

    def _load_or_build(self) -> None:
        idx_path  = self._store / self.INDEX_FILE
        meta_path = self._store / self.META_FILE

        if idx_path.exists() and meta_path.exists():
            self.index = faiss.read_index(str(idx_path))
            with open(meta_path) as f:
                self.meta = json.load(f)
            print(f"[VectorAgent] Loaded index ({len(self.meta)} docs).")
        else:
            print("[VectorAgent] Building index from DEPARTMENT_DOCS …")
            self._build_index(DEPARTMENT_DOCS)

    def _build_index(self, docs: list[dict]) -> None:
        texts = [d["content"] for d in docs]
        vecs  = self._embed(texts)
        dim   = vecs.shape[1]

        # IndexFlatIP for cosine similarity (after L2 normalisation)
        self.index = faiss.IndexFlatIP(dim)
        self.index.add(vecs)
        self.meta  = list(docs)
        self._save()
        print(f"[VectorAgent] Index built with {len(docs)} documents.")

    def _embed(self, texts: list[str]) -> np.ndarray:
        vecs = self.model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
        return vecs.astype(np.float32)

    def _save(self) -> None:
        faiss.write_index(self.index, str(self._store / self.INDEX_FILE))
        with open(self._store / self.META_FILE, "w") as f:
            json.dump(self.meta, f, indent=2)
