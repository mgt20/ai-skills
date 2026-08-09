---
name: grocery-planner
description: Use when planning verified sale-aware groceries and two practical dinners.
metadata:
  compatible_harnesses: [Hermes, OpenClaw, generic]
  requires: [python>=3.11]
---

# Grocery Planner

Use this skill to guide a household through a **review-only**, sale-aware grocery
plan: verified weekly-ad data, two practical dinner anchors, a grouped shopping
list, and clearly separated single-day offers. It is portable across Hermes,
OpenClaw, and other harnesses that can read files and run Python.

## Install this skill

This repository is intentionally a **skills repository**. A recipient can merge
only its skills into an existing skills directory while keeping the Python engine
in the cloned repository:

```bash
git clone https://github.com/mgt20/ai-skills.git
cd ai-skills
python3 -m pip install -e .

# Hermes (or any directory-based skills loader)
mkdir -p ~/.hermes/skills
cp -a skills/. ~/.hermes/skills/
```

For another harness, copy `skills/grocery-planner/` into that harness's skill
folder. Keep the repository checkout available as the engine workdir; do not copy
household settings into the skill directory.

## First-time household setup

1. Read [references/LLM_SETUP.md](references/LLM_SETUP.md).
2. Copy [templates/grocery.example.toml](templates/grocery.example.toml) to a
   private location outside the repository, for example `~/grocery.local.toml`.
3. Have the user fill household preferences, store identity, and optional local
   paths. Never commit, upload, or quote that private config.
4. Validate it:

   ```bash
   grocery-planner validate-config --config ~/grocery.local.toml
   ```

5. Obtain a current normalized weekly-ad JSON artifact from a provider adapter.
   The included Safeway/Flipp adapter is optional and should only be used after
   the household has verified its store. Do not invent a current price or deal.
6. Create a local review packet:

   ```bash
   grocery-planner plan \
     --config ~/grocery.local.toml \
     --ad-json /private/path/latest_extract.json \
     --out-dir /private/path/grocery-review \
     --date YYYY-MM-DD
   ```

The CLI accepts only a complete, date-current normalized artifact and writes
owner-only Markdown, HTML, and JSON review files. It does not fetch live data,
send messages, change carts, check out, pay, or place orders.

## Planning behavior

- Default to **two** practical dinner anchors unless the user requests another
  number.
- Apply the household rules in the private config to rank provider items; do not
  embed family preferences in this shared skill.
- Keep staples and explicit user feedback ahead of novelty.
- Show what is verified, what is assumed, and what needs a human decision.
- Keep single-day offers separate from week-long sale anchors.
- If the artifact is incomplete, stale, from the wrong store, or fails coverage
  validation, stop and explain the failure rather than producing a confident plan.

## Safety and privacy

- Keep receipts, loyalty/store identifiers, addresses, emails, chat destinations,
  API keys, and household preferences in private config or secrets only.
- No external delivery, cart mutation, checkout, payment, or order placement
  without explicit approval and a separately reviewed adapter.
- Never claim current prices without a current provider artifact.
- Do not put private artifacts or a local config back into this repository.

## Harness notes

- **Hermes:** copy this directory into `~/.hermes/skills/` (or install it via the
  harness's skill mechanism), then start a new session so it is reloaded. Use
  Hermes cron/messaging only after a local review packet has been verified.
- **OpenClaw / other harnesses:** copy this directory into the harness skill
  directory and point its terminal/workdir at the cloned repository. Scheduling
  and delivery remain harness-specific edge adapters.

## Verification

Before claiming the setup works:

1. `grocery-planner validate-config` accepts the private config.
2. The provider artifact has `coverage.status == "ok"`, matches the requested
   store, and covers the requested plan date.
3. The local review packet is generated and checked for realistic dinner anchors,
   grouped sale items, and a clear approval boundary.
4. Only then offer optional scheduling, delivery, receipt learning, or cart help.
