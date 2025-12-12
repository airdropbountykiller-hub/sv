#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SV - System Paths Configuration
Centralized configuration dei percorsi of the system
"""

import os
from pathlib import Path


def get_project_root():
    """Get project root directory (SV main folder)"""
    # This file is in config/, so go up one level
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_config_dir():
    """Get config directory"""
    return os.path.join(get_project_root(), 'config')


def get_modules_dir():
    """Get modules directory"""
    return os.path.join(get_project_root(), 'modules')


def get_data_dir():
    """Get data directory"""
    return os.path.join(get_project_root(), 'data')


def get_cache_dir():
    """Get cache directory (in data/)"""
    cache_dir = os.path.join(get_data_dir(), 'cache')
    return cache_dir


def get_news_cache_dir():
    """Get news cache directory (in data/)"""
    news_cache_dir = os.path.join(get_data_dir(), 'news_cache')
    return news_cache_dir


def _safe_makedirs(path: str) -> Path:
    """Create directories unless they are under the externally managed data/ root."""

    target = Path(path).resolve()
    data_root = Path(DATA_DIR).resolve()

    if target == data_root or data_root in target.parents:
        raise RuntimeError(
            "[SV-PATHS] Refusing to auto-create data directory; provision data/ externally"
        )

    os.makedirs(target, exist_ok=True)
    return target


def get_reports_dir():
    """Get reports directory"""
    reports_dir = os.path.join(get_project_root(), 'reports')
    _safe_makedirs(reports_dir)
    return reports_dir


def get_templates_dir():
    """Get templates directory"""
    return os.path.join(get_config_dir(), 'templates')


def get_daily_contexts_dir():
    """Location for narrative context snapshots (formerly under backups/)."""
    return os.path.join(get_config_dir(), 'daily_contexts')


def get_ml_analysis_dir():
    """Location for coherence and ML analysis artifacts (formerly under backups/)."""
    return os.path.join(get_config_dir(), 'ml_analysis')


def get_preview_dir():
    """Plain-text previews directory (stored alongside other configs)."""
    return os.path.join(get_config_dir(), 'previews')


def get_flags_file():
    """Scheduler flags file stored alongside config state."""
    return os.path.join(get_config_dir(), 'sv_flags.json')


def get_portfolio_state_file():
    """Portfolio manager state file under config/."""
    return os.path.join(get_config_dir(), 'portfolio_state.json')


def get_portfolio_signals_file():
    """Operational signals emitted by the portfolio decision layer."""
    return os.path.join(get_config_dir(), 'portfolio_signals.json')


# Path constants
PROJECT_ROOT = get_project_root()
MODULES_DIR = get_modules_dir()
DATA_DIR = get_data_dir()
CACHE_DIR = get_cache_dir()
NEWS_CACHE_DIR = get_news_cache_dir()
REPORTS_DIR = get_reports_dir()
TEMPLATES_DIR = get_templates_dir()
CONFIG_DIR = get_config_dir()
DAILY_CONTEXTS_DIR = get_daily_contexts_dir()
ML_ANALYSIS_DIR = get_ml_analysis_dir()
PREVIEWS_DIR = get_preview_dir()
FLAGS_FILE = get_flags_file()
PORTFOLIO_STATE_FILE = get_portfolio_state_file()
PORTFOLIO_SIGNALS_FILE = get_portfolio_signals_file()


def setup_all_directories():
    """Create necessary non-data directories"""
    directories = [
        REPORTS_DIR,
        TEMPLATES_DIR,
        CONFIG_DIR,
        DAILY_CONTEXTS_DIR,
        ML_ANALYSIS_DIR,
        PREVIEWS_DIR,
    ]

    for directory in directories:
        _safe_makedirs(directory)

    print("✅ [SV-PATHS] Directories verified (data/ remains external and untouched)")
    return True


if __name__ == '__main__':
    print("🛠 [SV-PATHS] Path System Configuration")
    print(f"📂 Project Root: {PROJECT_ROOT}")
    print(f"📂 Modules: {MODULES_DIR}")
    print(f"📂 Data (external): {DATA_DIR}")
    print(f"📂 Cache (depends on data): {CACHE_DIR}")
    print(f"📂 News Cache (depends on data): {NEWS_CACHE_DIR}")
    print(f"📂 Reports: {REPORTS_DIR}")
    print(f"📂 Templates: {TEMPLATES_DIR}")
    print(f"📂 Config: {CONFIG_DIR}")
    print(f"📂 Daily contexts: {DAILY_CONTEXTS_DIR}")
    print(f"📂 ML analysis: {ML_ANALYSIS_DIR}")
    print(f"📂 Previews: {PREVIEWS_DIR}")
    setup_all_directories()
