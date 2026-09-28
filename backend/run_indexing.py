"""CLI runner for SourceWise document embedding and Qdrant indexing pipeline."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from app.services.indexing import execute_indexing_cli


def main() -> None:
    """Parse CLI arguments and run document indexing with structured reporting."""
    execute_indexing_cli()


if __name__ == "__main__":
    main()
