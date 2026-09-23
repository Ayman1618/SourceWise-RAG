"""CLI runner for SourceWise document embedding and Qdrant indexing pipeline."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from app.services.indexing import run_indexing_cli


def main() -> None:
    """Parse CLI arguments and run document indexing."""
    parser = argparse.ArgumentParser(
        description="Index documents into Qdrant vector database."
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=None,
        help="Path to directory containing Markdown documents (defaults to data/sample-documents).",
    )
    parser.add_argument(
        "--collection",
        default=None,
        help="Target Qdrant collection name.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=None,
        help="Batch size for embedding generation and upsert.",
    )
    parser.add_argument(
        "--in-memory",
        action="store_true",
        help="Run completely offline using in-memory Qdrant and SHA256-stub embeddings (no API keys required).",
    )

    args = parser.parse_args()

    mode_label = "in-memory / offline mode" if args.in_memory else "live service mode"
    print(f"Starting document indexing pipeline ({mode_label})...")

    try:
        docs, chunks, point_ids = run_indexing_cli(
            directory_path=args.directory,
            collection_name=args.collection,
            batch_size=args.batch_size,
            in_memory=args.in_memory,
        )
    except Exception as exc:
        print(f"Error during indexing: {exc}", file=sys.stderr)
        sys.exit(1)

    print("\n--- Indexing Summary ---")
    print(f"Documents processed: {len(docs)}")
    print(f"Chunks produced:     {len(chunks)}")
    print(f"Points indexed:      {len(point_ids)}")

    if point_ids:
        print(f"\nSample point ID:     {point_ids[0]}")
        print(f"Sample chunk ID:     {chunks[0].chunk_id}")
        print(f"Sample parent doc:   {chunks[0].document_id}")
        print(f"Sample text snippet: {chunks[0].text[:100]}...")


if __name__ == "__main__":
    main()
