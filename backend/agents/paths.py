"""Central path constants for the backend package.

Import from here instead of computing Path(__file__).resolve().parents[N].
"""

from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_DIR.parent
DATA_DIR = REPO_ROOT / "data"
OUTPUTS_DIR = DATA_DIR / "outputs"
DB_PATH = DATA_DIR / "predictions.db"
