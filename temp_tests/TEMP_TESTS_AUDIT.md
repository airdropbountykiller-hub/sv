# temp_tests audit

Summary of duplicate, obsolete, or unused items found in the `temp_tests` sandbox.

## Generated artifacts
- `temp_tests/__pycache__/` contained compiled `.pyc` files for the ad-hoc scripts and tests. These are runtime byproducts and have been removed; they should remain untracked going forward.

## Stale documentation snapshots
- `temp_tests/PROJECT_STRUCTURE.md` is a static listing dated "02 Nov 2025" that reflects a Windows drive layout (`H:\\il mio drive\\sv`). It no longer matches the current repository structure.
- `temp_tests/MODULES_STRUCTURE.md` and `temp_tests/MODULES_COMPLETE_DESCRIPTION.md` both capture historical module sizes/statuses and duplicate each other. They predate recent changes and are not referenced by any scripts or tests.
- `temp_tests/MODULI_ANALISI.md` compares the current system with hypothetical modules (`narrative_continuity.py`, `ml_coherence_analyzer.py`) that are not present in the codebase, so the analysis is obsolete.

## Unmaintained tooling
- `temp_tests/tools/split_generators.py` hard-codes a Windows path (`H:\\il mio drive\\sv`) and writes into a `modules/generators/` tree that is not part of the repository. It appears to be an old refactor aid rather than an active tool.
