"""Ensure backend/ is on sys.path for direct module imports (e.g. run_pipeline)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
