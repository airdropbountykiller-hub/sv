#!/usr/bin/env python3
import os, json, logging, sys

# Ensure project root on path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

from modules.monthly_generator import MonthlyReportGeneratetor
from modules.pdf_generator import Createte_monthly_pdf

logging.basicConfig(level=logging.INFO)

# Assemble monthly data (purely from saved daily metrics / period_aggregator)
mg = MonthlyReportGeneratetor()
monthly_data = mg.assemble_monthly_data()

pdf_path = Createte_monthly_pdf(monthly_data) if monthly_data else None

print("PDF_PATH=" + str(pdf_path))
if monthly_data:
    summary = monthly_data.get('monthly_summary', '') or ''
    metrics = monthly_data.get('performance_metrics', {}) or {}
    daily = monthly_data.get('daily_performance', []) or []
    what_worked = monthly_data.get('what_worked', []) or []
    what_didnt = monthly_data.get('what_didnt', []) or []
    print("SUMMARY=" + summary)
    print("METRICS=" + json.dumps(metrics, ensure_ascii=False))
    compact_daily = [{k: d.get(k) for k in ('day','date','signals','success_rate')} for d in daily]
    print("DAILY=" + json.dumps(compact_daily, ensure_ascii=False))
    print("WHAT_WORKED=" + json.dumps(what_worked, ensure_ascii=False))
    print("WHAT_DIDNT=" + json.dumps(what_didnt, ensure_ascii=False))
else:
    print("ERROR=assemble_failed")
