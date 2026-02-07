"""Centralized filesystem paths for runtime and artifacts."""

import os
from pathlib import Path


PACKAGE_DIR = Path(__file__).resolve().parent
DEFAULT_APP_ROOT = PACKAGE_DIR.parent.parent if PACKAGE_DIR.parent.name == "src" else PACKAGE_DIR.parent
APP_ROOT = Path(os.getenv("FLOPORTOP_APP_ROOT", DEFAULT_APP_ROOT)).resolve()

MODELS_DIR = Path(os.getenv("FLOPORTOP_MODELS_DIR", APP_ROOT / "models")).resolve()
CACHE_DIR = Path(os.getenv("FLOPORTOP_CACHE_DIR", APP_ROOT / "cache")).resolve()
DATA_DIR = Path(os.getenv("FLOPORTOP_DATA_DIR", APP_ROOT / "data")).resolve()
