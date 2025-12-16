#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SV - Private configuration loader.

Centralizes reading of `config/private.txt` so all integrations (Telegram, market
providers, brokers) can share the same parsing rules.

Rules:
- Lines are KEY=VALUE
- Blank lines and lines starting with # are ignored
- Environment variables override file values

IMPORTANT: Never log or print secret values.
"""

from __future__ import annotations

from pathlib import Path
import os
import threading
from typing import Dict, Optional

from config import sv_paths


_LOCK = threading.Lock()
_CACHE: Optional[Dict[str, str]] = None
_CACHE_MTIME: float = 0.0


def load_private_config(path: str | Path | None = None, *, refresh: bool = False) -> Dict[str, str]:
    """Load private config from disk.

    Args:
        path: Optional explicit path to a private config file.
        refresh: If True, bypass the in-memory cache.

    Returns:
        A dict of raw key/value pairs (strings).
    """

    cfg_path = Path(path) if path else (Path(sv_paths.CONFIG_DIR) / "private.txt")

    try:
        mtime = cfg_path.stat().st_mtime
    except FileNotFoundError:
        return {}
    except Exception:
        # If stat fails (permissions, etc.), do a best-effort read below.
        mtime = 0.0

    global _CACHE, _CACHE_MTIME
    with _LOCK:
        if not refresh and _CACHE is not None and mtime and mtime == _CACHE_MTIME:
            return dict(_CACHE)

        config: Dict[str, str] = {}
        try:
            # utf-8-sig to tolerate BOM
            text = cfg_path.read_text(encoding="utf-8-sig")
        except Exception:
            return {}

        for raw in text.splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue

            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip()
            if not k:
                continue

            # Allow inline comments (e.g. IG_ENV=demo  # comment)
            # We only strip when the # is preceded by whitespace to avoid
            # breaking secrets that may contain '#'.
            for sep in (" #", "\t#"):
                idx = v.find(sep)
                if idx != -1:
                    v = v[:idx].rstrip()
                    break

            config[k] = v

        _CACHE = dict(config)
        _CACHE_MTIME = mtime
        return dict(config)


def get_private_value(key: str, default: Optional[str] = None, *, refresh: bool = False) -> Optional[str]:
    """Get a single config value, with environment variables overriding private.txt."""

    if key in os.environ and os.environ[key] != "":
        return os.environ[key]

    cfg = load_private_config(refresh=refresh)
    return cfg.get(key, default)
