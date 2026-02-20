# Modular Architecture

Chuscraper is moving toward an industry-grade modular structure so the project is easier to maintain at scale.

## Design rules

1. Single responsibility per module.
2. Keep public APIs stable, even if internals move.
3. Add compatibility wrappers during refactors.
4. Add focused tests for each module.

## Core module boundaries

- `core/config.py` → runtime policy and launch configuration.
- `core/util.py` → public utility API and compatibility surface.
- `core/process.py` → browser process lifecycle helpers (spawn/cleanup/stderr).
- `core/browsers/context.py` → runtime context behavior (stealth, locale, headers, humanization).
- `core/stealth.py` → stealth script generation and fingerprint coherence.

## Refactor pattern to follow

- Step 1: extract a concern into a new module.
- Step 2: keep old function signatures as thin wrappers.
- Step 3: add tests for both the new module and wrapper behavior.
- Step 4: update docs and examples.

This pattern keeps churn low and reduces breakage for existing users.
