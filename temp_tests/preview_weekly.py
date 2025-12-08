#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, sys
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'modules'))

# Disable Telegram sending
os.environ['SV_SKIP_TELEGRAM'] = '1'

from weekly_generator import get_weekly_Generatetor

g = get_weekly_Generatetor()
text = g.Generatete_weekly_report()

print("\n=== WEEKLY REPORT TEXT (first 600 chars) ===\n")
print(text[:600])
print("\n...\n[Length]", len(text))
