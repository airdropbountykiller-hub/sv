#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SV - System Paths Configuration
Centralized configuration of project paths.
"""
from __future__ import annotations

from pathlib import Path

# Core locations
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
MODULES_DIR = PROJECT_ROOT / "modules"
DATA_DIR = PROJECT_ROOT / "data"  # externally managed; do not auto-create
TEMPLATES_DIR = CONFIG_DIR / "templates"
REPORTS_DIR = PROJECT_ROOT / "reports"

# Portfolio outputs
PORTFOLIO_STATE_FILE = CONFIG_DIR / "portfolio_state.json"
PORTFOLIO_SIGNALS_FILE = CONFIG_DIR / "portfolio_signals.json"


def _safe_makedirs(path: Path) -> Path:
    """Create directories unless they belong to the external data/ tree."""

    target = path.resolve()
    data_root = DATA_DIR.resolve()

    if target == data_root or data_root in target.parents:
        raise RuntimeError(
            "[SV-PATHS] Refusing to auto-create data directory; provision data/ externally"
        )

    target.mkdir(parents=True, exist_ok=True)
    return target


def get_project_root() -> str:
    return str(PROJECT_ROOT)


def get_config_dir() -> str:
    return str(CONFIG_DIR)


def get_modules_dir() -> str:
    return str(MODULES_DIR)


def get_templates_dir() -> str:
    return str(TEMPLATES_DIR)


def get_reports_dir() -> str:
    _safe_makedirs(REPORTS_DIR)
    return str(REPORTS_DIR)


def setup_all_directories() -> bool:
    """Create necessary non-data directories."""
    for directory in (TEMPLATES_DIR, REPORTS_DIR, CONFIG_DIR):
        _safe_makedirs(directory)
    print("✅ [SV-PATHS] Directories verified (data/ remains external and untouched)")
    return True


if __name__ == '__main__':
    print("🛠 [SV-PATHS] Path System Configuration")
    print(f"📂 Project Root: {PROJECT_ROOT}")
    print(f"📂 Modules: {MODULES_DIR}")
    print(f"📂 Data (external): {DATA_DIR}")
    print(f"📂 Templates: {TEMPLATES_DIR}")
    print(f"📂 Reports: {REPORTS_DIR}")
    setup_all_directories()
