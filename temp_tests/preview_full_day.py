#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate full-day previews for SV system (Press → Morning → Noon → Evening → Summary).

Outputs plain-text previews under config/debug_previews/ so we can manually inspect
coerenza narrativa, categorie news e tono ML senza toccare Telegram.
"""

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import sv_paths

from modules.daily_generator import (
    generate_press_review_wrapper,
    generate_morning,
    generate_noon_update,
    generate_evening,
    generate_summary,
)


def ensure_preview_dir() -> Path:
    preview_dir = Path(sv_paths.DEBUG_PREVIEWS_DIR)
    preview_dir.mkdir(parents=True, exist_ok=True)
    return preview_dir


def save_preview(name: str, messages: list[str]) -> Path:
    preview_dir = ensure_preview_dir()
    path = preview_dir / f"{name}.txt"
    # Join with clear separators but keep it human-readable
    sep = "\n\n" + "=" * 80 + "\n\n"
    text = sep.join(messages)
    path.write_text(text, encoding="utf-8")
    return path


def main() -> None:
    print("[PREVIEW] Generating full-day previews (Press → Morning → Noon → Evening → Summary)...")

    # PRESS
    try:
        press_msgs = generate_press_review_wrapper()
        press_path = save_preview("press", press_msgs)
        print(f"[PREVIEW] Press Review: {len(press_msgs)} messages → {press_path}")
    except Exception as e:
        print(f"[ERROR] Press preview failed: {e}")

    # MORNING
    try:
        morning_msgs = generate_morning()
        morning_path = save_preview("morning", morning_msgs)
        print(f"[PREVIEW] Morning: {len(morning_msgs)} messages → {morning_path}")
    except Exception as e:
        print(f"[ERROR] Morning preview failed: {e}")

    # NOON
    try:
        noon_msgs = generate_noon_update()
        noon_path = save_preview("noon", noon_msgs)
        print(f"[PREVIEW] Noon: {len(noon_msgs)} messages → {noon_path}")
    except Exception as e:
        print(f"[ERROR] Noon preview failed: {e}")

    # EVENING
    try:
        evening_msgs = generate_evening()
        evening_path = save_preview("evening", evening_msgs)
        print(f"[PREVIEW] Evening: {len(evening_msgs)} messages → {evening_path}")
    except Exception as e:
        print(f"[ERROR] Evening preview failed: {e}")

    # SUMMARY
    try:
        summary_msgs = generate_summary()
        summary_path = save_preview("summary", summary_msgs)
        print(f"[PREVIEW] Summary: {len(summary_msgs)} pages → {summary_path}")
    except Exception as e:
        print(f"[ERROR] Summary preview failed: {e}")

    print("[PREVIEW] Done.")


if __name__ == "__main__":
    main()
