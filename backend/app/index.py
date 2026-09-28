"""Entrypoint for `python -m app.index` CLI document indexing command."""

from __future__ import annotations

from pathlib import Path
import sys

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.services.indexing import execute_indexing_cli

if __name__ == "__main__":
    execute_indexing_cli()
