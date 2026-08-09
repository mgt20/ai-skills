# AI Skills

A privacy-first, harness-neutral foundation for sale-aware grocery planning.
It contains a Python core plus an agent skill that can be used with Hermes,
OpenClaw, or another LLM harness.

## Status

**Private bootstrap.** The first supported store adapter is Safeway/Flipp.
The repository is intentionally being generalized before public release.

## What is stable

- `skills/grocery-planner/SKILL.md`: agent behavior and safety contract.
- `skills/grocery-planner/LLM_SETUP.md`: guided household onboarding.
- `src/grocery_agent_kit/`: config, household scoring, recipe providers, HTML rendering.
- `scripts/extract_safeway_weekly_ad.py`: Safeway/Flipp ad extraction.

## Safety

Never commit household configuration, receipt data, email/Slack destinations,
loyalty data, tokens, generated shopping artifacts, or payment information.
The engine may create a reviewable shopping list; cart edits require explicit
approval and checkout/payment is out of scope.

## Layout

- `skills/` — portable agent instructions and setup prompts.
- `src/` — harness-neutral Python engine.
- `scripts/` — optional store adapters and local runners.
- `examples/` — copyable, non-secret configuration.
- `docs/` — architecture and contributor contracts.

## Local development

```bash
python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 -m py_compile src/grocery_agent_kit/*.py
```

See `docs/architecture.md` before adding a store, recipe provider, or harness adapter.
