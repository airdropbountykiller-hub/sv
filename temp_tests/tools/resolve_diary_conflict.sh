#!/usr/bin/env bash
# Quick helper to resolve DIARY.md conflicts using the built-in `ours` merge driver.
# Usage: bash temp_tests/tools/resolve_diary_conflict.sh
set -euo pipefail

# Ensure the built-in merge driver is registered (idempotent)
git config merge.ours.driver true

# Force our version of DIARY.md if Git marked it conflicted
if git ls-files -u -- DIARY.md >/dev/null 2>&1 && git ls-files -u -- DIARY.md | grep -q .; then
  git checkout --ours DIARY.md
fi

git add DIARY.md

echo "DIARY.md marked resolved with merge=ours."
git status --short -- DIARY.md
