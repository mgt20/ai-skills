# AI Skills

A privacy-first, harness-neutral foundation for sale-aware grocery planning. It
contains a Python core and an agent skill usable with Hermes, OpenClaw, or another
LLM harness.

## Status

**Private bootstrap; Phase 1 vertical slice is usable locally.** The first supported
store extractor is Safeway/Flipp. The portable planner accepts any normalized
weekly-ad artifact that satisfies the documented contract.

## What works today

- `skills/grocery-planner/SKILL.md`: agent behavior and safety contract.
- `skills/grocery-planner/LLM_SETUP.md`: guided household onboarding.
- `scripts/extract_safeway_weekly_ad.py`: optional Safeway/Flipp extraction to a normalized artifact.
- `python -m grocery_agent_kit plan`: creates review-only Markdown, HTML, and JSON plan artifacts from a verified normalized ad.
- `python -m grocery_agent_kit validate-config`: prevents use of placeholder store settings in a real household configuration.

Recipe selection, messaging, cart integration, and scheduling remain **edge adapters**.
They are intentionally not invoked by the planner CLI.

## Quick start: fixture-only demo

```bash
python3 -m unittest discover -s tests -v

# Make a private copy before using a real store or household.
cp examples/basic-local/config/grocery.example.toml /secure/path/grocery.local.toml
PYTHONPATH=src python3 -m grocery_agent_kit validate-config --config /secure/path/grocery.local.toml

# Plan only from a normalized artifact whose coverage.status is "ok".
PYTHONPATH=src python3 -m grocery_agent_kit plan \
  --config examples/basic-local/config/grocery.example.toml \
  --ad-json /path/to/latest_extract.json \
  --out-dir ./out \
  --date 2026-01-01
```

The plan command is local and review-only: it performs no network call, delivery,
cart mutation, checkout, or payment.

## Safety and privacy

Never commit household configuration, receipt data, email/Slack destinations,
loyalty data, tokens, generated shopping artifacts, or payment information. The
engine may create a reviewable shopping list; cart edits require explicit approval
in a separate adapter, and checkout/payment is out of scope.

## Layout

- `skills/` — portable agent instructions and setup prompts.
- `src/` — harness-neutral Python engine.
- `scripts/` — optional store adapters and local runners.
- `examples/` — copyable, non-secret configuration.
- `docs/` — architecture and contributor contracts.
- `tests/` — fixture-only regressions; no test needs a live store, account, or token.

See `docs/architecture.md` before adding a store, recipe provider, or harness adapter.
