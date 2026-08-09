---
name: grocery-planner-kit
description: Build a practical, sale-aware household grocery plan with two realistic dinners, verified local deals, recipe links, quantity math, and approval-gated cart help.
---

# Grocery Planner Kit

Use this skill when a user wants a weekly grocery plan, sale-aware dinner ideas, a cart-ready list, or help setting up this automation for their household.

This skill is **harness-neutral**: it can be used by Hermes, OpenClaw, or another LLM agent that can read files and run Python. The core engine is local Python; scheduling, credentials, delivery, and cart integrations are harness-specific.

## Setup mode

For a new household, read `LLM_SETUP.md` first and follow its intake and safety contract.

1. Ask for household size, allergies, texture/spice constraints, preferred/avoided foods, meal count, leftovers target, budget, prep tolerance, store location, and shopping day.
2. Copy `config/grocery.example.toml` to the private `config/grocery.local.toml`; never share the local file.
3. Verify the correct store ID and current weekly-ad source. Do not invent a store-specific price or deal.
4. Run the weekly-ad extractor, then `python3 build_weekly_plan.py`.
5. Review the generated Markdown, HTML, and Slack-summary artifacts with the user before scheduling delivery or assisting with a cart.

## Planning rules

- Default to exactly two practical dinner candidates unless the user asks otherwise.
- Favor low-prep, family-tolerant meals and realistic leftovers; avoid aspirational seven-night meal plans.
- Start with household staples and explicit feedback, then use verified sales to select proteins and produce.
- Include recipe links, rough quantity/package math, grouped shopping lists, pantry/freezer checks, and a clear separation of one-day deals from week-long deals.
- Treat receipt history as purchase-frequency evidence, not satisfaction proof. Explicit feedback overrides it.
- If current sale data cannot be verified, say so plainly and do not present estimates as deals.

## Safety and privacy

- Generate and preview freely, but do not send messages, mutate carts, check out, pay, or place orders without explicit approval.
- Keep raw receipts, store/loyalty identifiers, home addresses, email/Slack destinations, API keys, and household-specific preferences in private local config or secrets.
- Never include private configuration or generated household artifacts in a share bundle.

## Harness integration

- **Hermes:** run inside a dedicated profile/workdir; use its native scheduler and messaging only after a successful local dry run.
- **OpenClaw:** run in an OpenClaw workspace; use its scheduler/messaging configuration only after the engine has produced a reviewed local plan.
- **Other harnesses / plain cron:** invoke the extractor and `build_weekly_plan.py`, then consume the generated files as the integration boundary:
  - `weekly_shopping_list_latest.md`
  - `weekly_shopping_list_latest.html`
  - `weekly_shopping_list_slack_root_latest.txt`

## Verification

Before declaring a setup or change complete:

1. Run `python3 -m unittest discover -s tests -v`.
2. Confirm the ad extractor targets the intended store and has adequate coverage.
3. Generate a local plan and check it has the requested meal count, recipe links, quantity math, pantry checks, and the no-checkout boundary.
4. If delivery is enabled, verify its credentials and use a dry run before any live send.
