#!/usr/bin/env bash
# Quick helper to resolve DIARY.md conflicts if Git didn't apply merge=union automatically.
# Usage: bash config/tools/resolve_diary_conflict.sh
set -euo pipefail

# If DIARY.md is conflicted, prefer the current branch version to unblock the merge.
if git ls-files -u -- DIARY.md >/dev/null 2>&1 && git ls-files -u -- DIARY.md | grep -q .; then
  git checkout --ours DIARY.md
fi

git add DIARY.md

echo "DIARY.md marked resolved (merge=union fallback)."
git status --short -- DIARY.md
