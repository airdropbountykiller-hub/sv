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


def get_backups_dir():
    """Get backups directory (for flags and system state)"""
    return os.path.join(get_config_dir(), 'backups')


def get_debug_previews_dir():
    """Get debug previews directory (text previews of generated content)"""
    return os.path.join(get_config_dir(), 'debug_previews')


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
    return os.path.join(get_project_root(), 'templates')


# Path constants
PROJECT_ROOT = get_project_root()
MODULES_DIR = get_modules_dir()
DATA_DIR = get_data_dir()
CACHE_DIR = get_cache_dir()
NEWS_CACHE_DIR = get_news_cache_dir()
BACKUPS_DIR = get_backups_dir()
REPORTS_DIR = get_reports_dir()
TEMPLATES_DIR = get_templates_dir()
CONFIG_DIR = get_config_dir()
DEBUG_PREVIEWS_DIR = get_debug_previews_dir()


def setup_all_directories():
    """Create necessary non-data directories"""
    directories = [
        BACKUPS_DIR,
        REPORTS_DIR,
        TEMPLATES_DIR,
        CONFIG_DIR,
        DEBUG_PREVIEWS_DIR,
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
    print(f"📁 Backups: {BACKUPS_DIR}")
    print(f"📂 Reports: {REPORTS_DIR}")
    print(f"📂 Templates: {TEMPLATES_DIR}")
    print(f"📂 Config: {CONFIG_DIR}")
    setup_all_directories()
