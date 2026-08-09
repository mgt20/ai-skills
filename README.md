# Grocery Agent Skills

A privacy-first **skills repository** with an optional harness-neutral Python core
for sale-aware grocery planning. A friend can merge `skills/` into an existing
Hermes, OpenClaw, or directory-based agent skills folder without importing any
private household data.

## Status

**Private bootstrap; Phase 1 vertical slice is usable locally.** The first supported
store extractor is Safeway/Flipp. The portable planner accepts any normalized
weekly-ad artifact that satisfies the documented contract.

## What works today

- `skills/README.md`: the portable-skills manifest and merge contract.
- `skills/grocery-planner/SKILL.md`: the grocery-planning skill behavior and safety contract.
- `skills/grocery-planner/references/LLM_SETUP.md`: guided household onboarding.
- `skills/grocery-planner/templates/grocery.example.toml`: neutral private-config starting point.
- `scripts/extract_safeway_weekly_ad.py`: optional Safeway/Flipp extraction to a normalized artifact.
- `python -m grocery_agent_kit plan`: creates review-only Markdown, HTML, and JSON plan artifacts from a verified normalized ad.
- `python -m grocery_agent_kit validate-config`: prevents use of placeholder store settings in a real household configuration.

Recipe selection, messaging, cart integration, and scheduling remain **edge adapters**.
They are intentionally not invoked by the planner CLI.

## Install a skill and run the fixture-only demo

```bash
git clone https://github.com/mgt20/ai-skills.git
cd ai-skills
python3 -m pip install -e .

# Merge portable skills without flattening their folders.
mkdir -p ~/.hermes/skills
cp -a skills/. ~/.hermes/skills/

python3 -m unittest discover -s tests -v

# Make a private copy before using a real store or household.
cp skills/grocery-planner/templates/grocery.example.toml ~/grocery.local.toml
grocery-planner validate-config --config ~/grocery.local.toml

# Plan only from a normalized artifact whose coverage.status is "ok".
grocery-planner plan \
  --config skills/grocery-planner/templates/grocery.example.toml \
  --ad-json /path/to/latest_extract.json \
  --out-dir ./out \
  --date 2026-01-01
```

The plan command is local and review-only: it performs no network call, delivery,
cart mutation, checkout, or payment.

## Distribution

The installable wheel contains the **core CLI only**. The portable agent skill,
LLM setup guide, examples, and contributor documentation are intentionally kept in
the source checkout under `skills/`, `examples/`, and `docs/`; copy the skill from
a tagged source release into the target harness rather than treating it as an
installed Python package resource.

## Safety and privacy

Never commit household configuration, receipt data, email/Slack destinations,
loyalty data, tokens, generated shopping artifacts, or payment information. The
engine may create a reviewable shopping list; cart edits require explicit approval
in a separate adapter, and checkout/payment is out of scope.

## Layout

- `skills/` — mergeable skill directories; each has its own `SKILL.md`, references, and neutral templates.
- `src/` — optional harness-neutral Python engine.
- `scripts/` — optional store adapters and local runners.
- `docs/` — architecture and contributor contracts for the engine/adapters.
- `tests/` — fixture-only regressions; no test needs a live store, account, or token.

See `docs/architecture.md` before adding a store, recipe provider, or harness adapter.
