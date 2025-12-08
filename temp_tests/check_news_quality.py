#!/usr/bin/env python3
"""Quick test to verify news quality improvements"""

import json
import sys
from pathlib import Path

# Read the latest press review JSON dynamically
BASE_DIR = Path(__file__).resolve().parent.parent
content_dir = BASE_DIR / "reports" / "8_daily_content"
press_files = sorted(content_dir.glob("*_press_review.json"))
if not press_files:
    print(f"❌ No press_review JSON files found in {content_dir}")
    sys.exit(1)

pr_file = press_files[-1]
print(f"[INFO] Using latest press review file: {pr_file}")

with open(pr_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Personal finance keywords to check
personal_keywords = [
    'paycheck', 'my husband', 'my wife', 'budget', 'save money',
    'retirement advice', 'personal finance', '401k', 'social security',
    'netflix', 'best movies', 'vacation', 'gift guide', 'top 10'
]

print('=' * 70)
print('PRESS REVIEW QUALITY CHECK')
print('=' * 70)

# 1. Check for duplicates
print('\n1️⃣ DUPLICATE CHECK')
print('-' * 70)
titles = []
for i, msg in enumerate(data['messages'][3:], 4):  # Messages 4-7
    lines = msg.split('\n')
    for line in lines:
        if any(f'**{j}.**' in line for j in range(1, 10)):
            parts = line.split('**', 2)
            if len(parts) > 2:
                title = parts[2]
                titles.append(title[:80])

print(f'Total titles: {len(titles)}')
print(f'Unique titles: {len(set(titles))}')

if len(titles) != len(set(titles)):
    from collections import Counter
    counts = Counter(titles)
    duplicates = {t: c for t, c in counts.items() if c > 1}
    print(f'\n❌ DUPLICATES FOUND:')
    for title, count in duplicates.items():
        print(f'  [{count}x] {title}')
else:
    print('✅ NO DUPLICATES - All titles are unique!')

# 2. Check for personal finance content
print('\n2️⃣ PERSONAL FINANCE CHECK')
print('-' * 70)
found_personal = False

for i, msg in enumerate(data['messages'][3:], 4):
    lines = msg.split('\n')
    for line in lines:
        if any(f'**{j}.**' in line for j in range(1, 10)):
            parts = line.split('**', 2)
            if len(parts) > 2:
                title = parts[2]
                title_lower = title.lower()
                
                for kw in personal_keywords:
                    if kw in title_lower:
                        print(f'❌ FOUND in Message {i}:')
                        print(f'   Keyword: "{kw}"')
                        print(f'   Title: {title[:100]}')
                        print()
                        found_personal = True

if not found_personal:
    print('✅ NO PERSONAL FINANCE - All news is market-relevant!')

# 3. Category distribution
print('\n3️⃣ CATEGORY DISTRIBUTION')
print('-' * 70)
categories = ['Finance', 'Cryptocurrency', 'Geopolitics', 'Technology']
for i, (msg, cat) in enumerate(zip(data['messages'][3:], categories), 4):
    news_count = sum(1 for line in msg.split('\n') if any(f'**{j}.**' in line for j in range(1, 10)))
    print(f'Message {i} ({cat}): {news_count} news items')

# 4. Heuristic check for suspicious category placements
print('\n4️⃣ SUSPICIOUS PLACEMENT CHECK (heuristic)')
print('-' * 70)

suspicious = []

# Simple keyword sets for quick sanity checks
geo_terms = [
    ' war', 'war ', 'conflict', 'sanction', 'invasion', 'nato', 'russia', 'ukraine',
    'gaza', 'israel', 'hezbollah', 'houthi', 'sudan', 'palestine'
]
tech_sec_terms = [
    'router', 'firmware', 'antivirus', 'malware', 'ransomware', 'hacker', 'hacked',
    'password', 'data breach', 'cybersecurity', 'cyber attack', 'cyberattack'
]
housing_terms = [
    'housing market', 'real estate market', 'home buyer', 'home buyers',
    'homebuyer', 'homebuyers', 'mortgage rate', 'mortgage rates'
]

for i, (msg, cat) in enumerate(zip(data['messages'][3:], categories), 4):
    lines = msg.split('\n')
    for line in lines:
        if not any(f'**{j}.**' in line for j in range(1, 10)):
            continue
        parts = line.split('**', 2)
        if len(parts) <= 2:
            continue
        title = parts[2].strip().lower()

        if cat == 'Finance':
            if any(t in title for t in geo_terms + tech_sec_terms):
                suspicious.append((i, cat, line.strip(), 'Looks geopolitics or pure tech/security'))
        elif cat == 'Geopolitics':
            if any(t in title for t in housing_terms + tech_sec_terms):
                suspicious.append((i, cat, line.strip(), 'Looks housing macro or pure tech/security'))
        elif cat == 'Technology':
            if any(t in title for t in geo_terms + housing_terms):
                suspicious.append((i, cat, line.strip(), 'Looks geopolitics or housing macro'))

if suspicious:
    print('⚠️ Potential misplacements found:')
    for msg_idx, cat, line, reason in suspicious:
        print(f'  - Message {msg_idx} ({cat}): {reason}')
        print(f'    {line[:120]}')
else:
    print('✅ No obvious misplacements detected by heuristics')

print('\n' + '=' * 70)
print('SUMMARY')
print('=' * 70)
print(f'✅ Anti-duplication: {"WORKING" if len(titles) == len(set(titles)) else "FAILED"}')
print(f'✅ Personal finance filter: {"WORKING" if not found_personal else "FAILED"}')
print(f'✅ Total messages: {len(data["messages"])} / 7 expected')
print('=' * 70)
