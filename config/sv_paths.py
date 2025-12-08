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

def get_modules_dir():
    """Get modules directory"""
    return os.path.join(get_project_root(), 'modules')

def get_data_dir():
    """Get data directory"""
    return os.path.join(get_project_root(), 'data')

def get_cache_dir():
    """Get cache directory (in data/)"""
    cache_dir = os.path.join(get_data_dir(), 'cache')
    os.makedirs(cache_dir, exist_ok=True)
    return cache_dir

def get_news_cache_dir():
    """Get news cache directory (in data/)"""
    news_cache_dir = os.path.join(get_data_dir(), 'news_cache')
    os.makedirs(news_cache_dir, exist_ok=True)
    return news_cache_dir

def get_backups_dir():
    """Get backups directory (for flags and system state)"""
    backups_dir = os.path.join(get_config_dir(), 'backups')
    os.makedirs(backups_dir, exist_ok=True)
    return backups_dir


def get_debug_previews_dir():
    """Get debug previews directory (text previews of generated content)"""
    previews_dir = os.path.join(get_config_dir(), 'debug_previews')
    os.makedirs(previews_dir, exist_ok=True)
    return previews_dir

def get_reports_dir():
    """Get reports directory"""
    reports_dir = os.path.join(get_project_root(), 'reports')
    os.makedirs(reports_dir, exist_ok=True)
    return reports_dir

def get_templates_dir():
    """Get templates directory"""
    return os.path.join(get_project_root(), 'templates')

def get_config_dir():
    """Get config directory"""
    return os.path.join(get_project_root(), 'config')

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
    """Create all necessary directories"""
    directories = [
        DATA_DIR,
        CACHE_DIR, 
        NEWS_CACHE_DIR,
        BACKUPS_DIR,
        REPORTS_DIR,
        TEMPLATES_DIR,
        CONFIG_DIR,
        DEBUG_PREVIEWS_DIR
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    
    print(f"âœ… [SV-PATHS] All directories verified/created")
    return True

if __name__ == '__main__':
    print("ðŸ”§ [SV-PATHS] Path System Configuration")
    print(f"ðŸ“ Project Root: {PROJECT_ROOT}")
    print(f"ðŸ“ Modules: {MODULES_DIR}")
    print(f"ðŸ“ Data: {DATA_DIR}")
    print(f"ðŸ“ Cache: {CACHE_DIR}")
    print(f"ðŸ“ News Cache: {NEWS_CACHE_DIR}")
    print(f"📁 Backups: {BACKUPS_DIR}")
    print(f"ðŸ“ Reports: {REPORTS_DIR}")
    print(f"ðŸ“ Templates: {TEMPLATES_DIR}")
    print(f"ðŸ“ Config: {CONFIG_DIR}")
    setup_all_directories()

