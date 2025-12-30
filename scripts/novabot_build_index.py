#!/usr/bin/env python3
"""
Build / refresh the NovaBot vector index from NoveumDocsData/processed/docs.json.

This script intentionally runs independently from the API server.

Requires:
- OPENAI_API_KEY (env var)

Outputs:
- NoveumDocsData/index/vectors.npy
- NoveumDocsData/index/metadata.json
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict, List


def repo_root() -> Path:
    # scripts/novabot_build_index.py -> repo root
    return Path(__file__).resolve().parents[1]


def load_docs(docs_path: Path) -> List[Dict[str, Any]]:
    data = json.loads(docs_path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("docs.json must be a list")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description="Build NovaBot embeddings index")
    parser.add_argument(
        "--docs",
        default=str(repo_root() / "NoveumDocsData" / "processed" / "docs.json"),
        help="Path to docs.json",
    )
    parser.add_argument(
        "--out-dir",
        default=str(repo_root() / "NoveumDocsData" / "index"),
        help="Output directory for vectors.npy + metadata.json",
    )
    parser.add_argument(
        "--embedding-model",
        default=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
        help="OpenAI embedding model name",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=64,
        help="Batch size for embeddings requests",
    )
    args = parser.parse_args()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("Missing OPENAI_API_KEY env var (required for embeddings).")

    docs_path = Path(args.docs)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    docs = load_docs(docs_path)
    texts = []
    for d in docs:
        title = str(d.get("title", ""))
        section = str(d.get("section_path", ""))
        content = str(d.get("content", ""))
        texts.append(f"{title}\n{section}\n\n{content}".strip())

    from openai import OpenAI

    client = OpenAI(api_key=api_key)

    import numpy as np

    vectors = []
    items = []

    for start in range(0, len(texts), args.batch_size):
        batch = texts[start : start + args.batch_size]
        resp = client.embeddings.create(model=args.embedding_model, input=batch)
        for j, row in enumerate(resp.data):
            vec = np.array(row.embedding, dtype="float32")
            vectors.append(vec)
            items.append(
                {
                    "doc_idx": start + j,
                    "chunk_id": docs[start + j].get("chunk_id"),
                    "url": docs[start + j].get("url"),
                }
            )

    if not vectors:
        print("⚠️  No documents to process. Exiting without creating index.")
        return 1

    mat = np.vstack(vectors)
    # Normalize to unit length for cosine similarity via dot product
    norms = np.linalg.norm(mat, axis=1, keepdims=True) + 1e-12
    mat = mat / norms

    (out_dir / "vectors.npy").write_bytes(b"")  # ensure writable
    np.save(out_dir / "vectors.npy", mat)

    meta = {
        "embedding_model": args.embedding_model,
        "normalized": True,
        "count": len(docs),
        "items": items,
    }
    (out_dir / "metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    print(f"✅ Wrote {len(docs)} vectors to {out_dir / 'vectors.npy'}")
    print(f"✅ Wrote metadata to {out_dir / 'metadata.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


