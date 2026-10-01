"""CLI runner for SourceWise document embedding and Qdrant indexing pipeline."""

from __future__ import annotations

from pathlib import Path
import sys

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.services.indexing import execute_indexing_cli


def main() -> None:
    """Parse CLI arguments and run document indexing with structured reporting."""
    execute_indexing_cli()


if __name__ == "__main__":
    main()

