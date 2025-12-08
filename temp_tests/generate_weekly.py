#!/usr/bin/env python3
import os, json, logging, sys
# Ensure project root on path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)
from modules.weekly_generator import WeeklyDataAssembler
from modules.pdf_generator import Createte_weekly_pdf

logging.basicConfig(level=logging.INFO)

assembler = WeeklyDataAssembler()
weekly_data = assembler.assemble_weekly_data()
pdf_path = Createte_weekly_pdf(weekly_data) if weekly_data else None

print("PDF_PATH=" + str(pdf_path))
if weekly_data:
    summary = weekly_data.get('weekly_summary', '') or ''
    metrics = weekly_data.get('performance_metrics', {}) or {}
    daily = weekly_data.get('daily_performance', []) or []
    print("SUMMARY=" + summary)
    print("METRICS=" + json.dumps(metrics, ensure_ascii=False))
    # keep daily output compact
    compact_daily = [{k: d.get(k) for k in ('day','date','signals','success_rate')} for d in daily]
    print("DAILY=" + json.dumps(compact_daily, ensure_ascii=False))
else:
    print("ERROR=assemble_failed")
