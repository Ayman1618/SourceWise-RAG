"""CLI runner for SourceWise document ingestion and chunking pipeline."""

from __future__ import annotations

import json
from pathlib import Path
import sys

from app.services.ingestion import run_ingestion_cli


def main() -> None:
    target_dir = sys.argv[1] if len(sys.argv) > 1 else None
    docs, chunks = run_ingestion_cli(target_dir)

    print(f"Number of documents: {len(docs)}")
    print(f"Number of chunks: {len(chunks)}")
    if chunks:
        print("\nSample chunk metadata:")
        print(json.dumps(chunks[0].metadata, indent=2))
        print("\nSample chunk representation:")
        print(f"Chunk ID: {chunks[0].chunk_id}")
        print(f"Document ID: {chunks[0].document_id}")
        print(f"Chunk Index: {chunks[0].chunk_index}")
        print(f"Token Count: {chunks[0].token_count}")
        print(f"Text snippet: {chunks[0].text[:120]}...")


if __name__ == "__main__":
    main()
