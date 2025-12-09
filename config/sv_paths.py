#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SV - System Paths Configuration
Centralized configuration dei percorsi of the system
"""

import os


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


def get_reports_dir():
    """Get reports directory"""
    reports_dir = os.path.join(get_project_root(), 'reports')
    os.makedirs(reports_dir, exist_ok=True)
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


# Verify all directories exist

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
        os.makedirs(directory, exist_ok=True)

    print("✅ [SV-PATHS] Directories verified (data creation skipped)")
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
