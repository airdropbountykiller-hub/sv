"""Sanity checks to ensure the runtime data/ directory is neither tracked nor auto-created."""

import os
import sys
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from config import sv_paths


def _data_root() -> Path:
    return Path(sv_paths.DATA_DIR).resolve()


def _assert_no_data_creation(recorded_paths):
    data_root = _data_root()
    offenders = [p for p in recorded_paths if data_root == p or data_root in p.parents]
    if offenders:
        raise AssertionError(f"data/ must be external; attempted to create: {offenders}")


def check_safe_makedirs_guard():
    """_safe_makedirs must refuse to build the external data/ tree."""
    try:
        sv_paths._safe_makedirs(str(_data_root()))
    except RuntimeError:
        return True
    raise AssertionError("_safe_makedirs should not allow creating data/ or its children")


def check_setup_all_directories_skips_data():
    """setup_all_directories should not touch data/ paths."""
    recorded = []

    def fake_makedirs(path, exist_ok=False):
        recorded.append(Path(path).resolve())

    with patch("config.sv_paths.os.makedirs", side_effect=fake_makedirs):
        sv_paths.setup_all_directories()

    _assert_no_data_creation(recorded)
    return True


if __name__ == "__main__":
    check_safe_makedirs_guard()
    check_setup_all_directories_skips_data()
    print("✅ data/ remains external: no auto-creation detected")
