# LLM-guided setup

Use this reference when helping a new household install the Grocery Planner skill.
The shared repository contains only a review-only engine and portable instructions;
private household data and every external integration stay outside the checkout.

## Intake

Ask concise questions for:

- household size, allergies, texture/spice constraints, and preferred/avoided foods;
- preferred store, location/postal code, and shopping day;
- dinner count, leftovers target, budget, prep devices, and convenience needs;
- whether future receipt learning, scheduling, delivery, or cart help is wanted.

Do not ask for credentials, account passwords, payment information, or loyalty IDs
until a user explicitly chooses an optional integration. Do not put any private
answer into the repository or shared skill files.

## Setup workflow

1. Confirm the engine checkout and its skill installation path. For Hermes, copy
   `skills/grocery-planner/` into `~/.hermes/skills/grocery-planner/` and start a
   fresh session.
2. Copy `templates/grocery.example.toml` to a private path outside the checkout,
   such as `~/grocery.local.toml`.
3. Fill the config interactively. Store and household fields must match the
   household; placeholder values are intentionally rejected by `validate-config`.
4. Run:

   ```bash
   grocery-planner validate-config --config ~/grocery.local.toml
   ```

5. Verify a current store-specific weekly-ad source. The shared planner consumes a
   normalized artifact; it never treats memory, old ads, or an LLM guess as a
   current price source.
6. Generate a local review packet:

   ```bash
   grocery-planner plan \
     --config ~/grocery.local.toml \
     --ad-json /private/path/latest_extract.json \
     --out-dir /private/path/grocery-review \
     --date YYYY-MM-DD
   ```

7. Review the Markdown, HTML, and JSON files with the household. Confirm the ad
   store and date, dinner anchors, single-day offers, and private-file boundary.
8. Only after a successful local preview, offer separate harness-specific work for
   scheduling, messaging, receipt learning, or approval-gated cart assistance.

## Paste into another LLM or harness

```text
You are setting up the Grocery Planner skill for a new household. Work
interactively and make no external or irreversible changes without explicit
approval.

Ask for household food constraints, preferred store/location/shopping day, dinner
count and leftovers target, budget/prep preferences, and whether future scheduling
or delivery is wanted. Keep all household answers in a private local config outside
the shared repository.

Use templates/grocery.example.toml as the starting point. Run grocery-planner
validate-config before planning. Use only a current normalized weekly-ad artifact
with coverage.status == "ok" and a matching store/date. Then run grocery-planner
plan to create a private local review packet.

Explain any missing or stale provider data plainly. Do not make current-price
claims without a verified artifact. Do not send messages, mutate carts, check out,
pay, or order anything without explicit approval and a separate reviewed adapter.
```

## Harness integration boundary

- **Hermes:** use its normal skills directory and start a new session after copying
  the skill. Create a cron job only after review-only local output is verified.
- **OpenClaw:** copy this complete skill directory into its skill location and set
  the cloned repository as a workspace/workdir for Python execution.
- **Other harnesses:** any system with file and Python access can use this skill;
  invoke the CLI and treat its generated local files as the integration boundary.

No harness is automatically configured by this repository. Credentials, schedules,
delivery destinations, and external actions must remain explicit, private, and
separately approved.
