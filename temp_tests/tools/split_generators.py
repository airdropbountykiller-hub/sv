from __future__ import annotations

"""Utility script to split intraday generators out of daily_generator.py.

This script extracts the four main intraday generators
(Morning, Noon, Evening, Summary) from DailyContentGenerator in
modules/daily_generator.py and writes them into dedicated modules under
modules/generators/.

It also rewrites DailyContentGenerator methods into thin wrappers that
delegate to the new modules, preserving the public API.
"""

import textwrap
from pathlib import Path

BASE_DIR = Path(r"H:\il mio drive\sv")
DG_PATH = BASE_DIR / "modules" / "daily_generator.py"
GEN_DIR = BASE_DIR / "modules" / "generators"


def _read_daily_generator() -> str:
    if not DG_PATH.exists():
        raise SystemExit(f"daily_generator.py not found at {DG_PATH}")
    return DG_PATH.read_text(encoding="utf-8")


def _write_daily_generator(text: str) -> None:
    DG_PATH.write_text(text, encoding="utf-8")


def _extract_block(source: str, start_marker: str, end_marker: str) -> tuple[str, int, int]:
    """Return (block_text, start_index, end_index) for [start_marker, end_marker).

    Both markers must be unique in the file.
    """

    try:
        start = source.index(start_marker)
    except ValueError as exc:
        raise SystemExit(f"Start marker not found: {start_marker!r}") from exc
    try:
        end = source.index(end_marker, start)
    except ValueError as exc:
        raise SystemExit(f"End marker not found after {start_marker!r}: {end_marker!r}") from exc
    return source[start:end], start, end


COMMON_HEADER = """\
# Intraday generator for the {name} block.
#
# Extracted from DailyContentGenerator.{method} in modules.daily_generator.

from typing import Any, Dict, List
import datetime

from modules import daily_generator as dg

EMOJI = dg.EMOJI
log = dg.log
_now_it = dg._now_it
get_enhanced_news = dg.get_enhanced_news
get_fallback_data = dg.get_fallback_data
get_live_crypto_prices = dg.get_live_crypto_prices
get_live_equity_fx_quotes = dg.get_live_equity_fx_quotes
calculate_crypto_support_resistance = dg.calculate_crypto_support_resistance
GOLD_GRAMS_PER_TROY_OUNCE = dg.GOLD_GRAMS_PER_TROY_OUNCE

# Optional dependency flags (mirrors modules.daily_generator)
DEPENDENCIES_AVAILABLE = getattr(dg, "DEPENDENCIES_AVAILABLE", False)
PERIOD_AGGREGATOR_AVAILABLE = getattr(dg, "PERIOD_AGGREGATOR_AVAILABLE", False)
COHERENCE_MANAGER_AVAILABLE = getattr(dg, "COHERENCE_MANAGER_AVAILABLE", False)
REGIME_MANAGER_AVAILABLE = getattr(dg, "REGIME_MANAGER_AVAILABLE", False)
PORTFOLIO_MANAGER_AVAILABLE = getattr(dg, "PORTFOLIO_MANAGER_AVAILABLE", False)

get_portfolio_manager = getattr(dg, "get_portfolio_manager", None)
get_daily_regime_manager = getattr(dg, "get_daily_regime_manager", None)
coherence_manager = getattr(dg, "coherence_manager", None)
period_aggregator = getattr(dg, "period_aggregator", None)
"""


def _make_module(name: str, method: str, block: str) -> str:
    """Return full module source for a given generator block.

    The input *block* is the original indented method definition,
    starting with ``    def {method}(self) -> List[str]:``.
    """

    header_old = f"    def {method}(self) -> List[str]:"
    header_new = f"def {method}(ctx) -> List[str]:"
    if header_old not in block:
        raise SystemExit(f"Header {header_old!r} not found in block for {name}")

    code = block.replace(header_old, header_new)
    # Replace method receiver
    code = code.replace("self.", "ctx.")

    # Remove one level of indentation (4 spaces) from all lines in the block
    lines = []
    for line in code.splitlines():
        if line.startswith("    "):
            lines.append(line[4:])
        else:
            lines.append(line)
    code = "\n".join(lines).rstrip() + "\n"

    pre = COMMON_HEADER.format(name=name, method=method)
    return textwrap.dedent(pre).lstrip() + "\n" + code


def main() -> None:
    GEN_DIR.mkdir(parents=True, exist_ok=True)

    # Ensure generators package exists
    init_path = GEN_DIR / "__init__.py"
    if not init_path.exists():
        init_path.write_text("# SV intraday generators package\n", encoding="utf-8")

    source = _read_daily_generator()

    morning_start = "    def generate_morning_report(self) -> List[str]:"
    noon_start = "    def generate_noon_update(self) -> List[str]:"
    evening_start = "    def generate_evening_analysis(self) -> List[str]:"
    summary_start = "    def generate_daily_summary(self) -> List[str]:"
    after_summary = "\n# Singleton instance"

    morning_block, m_start, m_end = _extract_block(source, morning_start, noon_start)
    noon_block, n_start, n_end = _extract_block(source, noon_start, evening_start)
    evening_block, e_start, e_end = _extract_block(source, evening_start, summary_start)
    summary_block, s_start, s_end = _extract_block(source, summary_start, after_summary)

    modules_spec = {
        "morning": ("Morning", "generate_morning_report", morning_block),
        "noon": ("Noon", "generate_noon_update", noon_block),
        "evening": ("Evening", "generate_evening_analysis", evening_block),
        "summary": ("Summary", "generate_daily_summary", summary_block),
    }

    for filename, (name, method, block) in modules_spec.items():
        out_path = GEN_DIR / f"{filename}.py"
        content = _make_module(name, method, block)
        out_path.write_text(content, encoding="utf-8")
        print(f"[split_generators] Wrote {out_path}")

    # Rebuild daily_generator.py with thin wrappers
    segments: list[str] = []
    cursor = 0

    def stub(method: str, short_desc: str, module_name: str) -> str:
        body = f'''\
    def {method}(self) -> List[str]:
        """{short_desc}"""
        from modules.generators.{module_name} import {method} as _impl
        return _impl(self)
'''
        return body

    for start, end, method, module_name, desc in [
        (m_start, m_end, "generate_morning_report", "morning", "Generate the 8:30 AM Morning Report (3 messages)."),
        (n_start, n_end, "generate_noon_update", "noon", "Generate the 13:00 Noon Update (3 messages)."),
        (e_start, e_end, "generate_evening_analysis", "evening", "Generate the 18:30 Evening Analysis (3 messages)."),
        (s_start, s_end, "generate_daily_summary", "summary", "Generate the 20:00 Daily Summary (6 pages)."),
    ]:
        segments.append(source[cursor:start])
        segments.append(stub(method, desc, module_name))
        cursor = end

    segments.append(source[cursor:])

    new_source = "".join(segments)
    _write_daily_generator(new_source)
    print(f"[split_generators] Updated {DG_PATH}")


if __name__ == "__main__":
    main()
