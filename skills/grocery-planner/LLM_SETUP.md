# LLM-guided setup

This kit is **harness-neutral Python**. It can run with Hermes, OpenClaw, or another LLM/automation harness; the harness supplies the conversation, optional scheduling, and optional delivery. The engine itself produces local Markdown, HTML, and Slack-summary files.

## What the LLM should do

Use an LLM as a setup guide, not as an unchecked operator. It should:

1. Ask for the household, preferred store/location, dietary restrictions, food dislikes, budget, meal count, leftover target, and prep tolerance.
2. Help the user copy and fill `config/grocery.example.toml` into the private `config/grocery.local.toml`.
3. Discover or ask for the correct local store ID / weekly-ad source; do not guess store-specific prices.
4. Run the extractor and build a local preview.
5. Check the output for exactly the requested meal count, realistic quantities, valid recipe links, and clearly separated one-day versus week-long deals.
6. Offer optional receipt learning, schedules, email, Slack, or cart assistance only after the base local preview works.

The LLM must keep real household data, store addresses, emails, loyalty identifiers, API keys, and raw receipts in private local configuration or secrets—not in prompts, public notes, or a shared copy of this kit.

## Paste this into your LLM/harness

```text
You are setting up the Grocery Planner Kit for a new household. Work interactively and make no irreversible or external changes without explicit approval.

First, ask concise questions for:
- household size and kid/texture/allergy constraints;
- preferred grocery store, location/postal code, and shopping day;
- number of dinners, leftover target, budget, preferred/avoided proteins, prep devices, and convenience preferences;
- whether receipt learning, scheduling, email, Slack, or cart assistance is wanted.

Then:
1. Copy config/grocery.example.toml to config/grocery.local.toml and help fill it with the answers. Never expose that local file or any secrets.
2. Verify the correct local weekly-ad source/store ID. Never invent prices; label unavailable sale data clearly.
3. Run the weekly-ad extractor, then python3 build_weekly_plan.py.
4. Present the generated Markdown/HTML/Slack-summary artifacts for review. Confirm recipe links, quantity math, pantry checks, and the no-checkout boundary.
5. Only after the local dry run succeeds, offer optional harness-specific scheduling/delivery. Keep cart additions approval-gated; never check out or pay.

For any configuration or command you do not recognize in the selected harness, stop and explain what information is needed rather than guessing.
```

## Harness adapters

### Hermes

- Run the engine from a profile/workdir and let the agent use `LLM_SETUP.md` during setup.
- For recurring generation, create a Hermes cron job only after a successful local dry run. The job should run in this kit's workdir and deliver the generated short summary; do not encode secrets in the cron prompt.
- Use Hermes-native credentials/tools for optional Gmail, Slack, or Drive delivery. Keep the underlying engine and `grocery.local.toml` private.

### OpenClaw

- Place this kit in an OpenClaw workspace and have its agent follow the prompt above.
- Use OpenClaw's own scheduler and messaging configuration only after the local extractor/build path works.
- Keep workspace secrets, delivery destinations, and receipt sources outside this shareable repository.

### Other harnesses and plain cron

- Any harness that can run Python and provide an LLM with file/terminal access can use the kit.
- A simple local scheduler can run the extractor followed by `python3 build_weekly_plan.py`; add sending or cart integration separately and only with explicit approval gates.
- Treat the generated files as the stable integration boundary:
  - `weekly_shopping_list_latest.md`
  - `weekly_shopping_list_latest.html`
  - `weekly_shopping_list_slack_root_latest.txt`

## Safety contract

- Generate lists and previews freely; do not send messages, mutate carts, check out, pay, or place orders without explicit approval.
- Never claim a store price or deal was verified unless the current local ad source confirms it.
- Preserve household-specific data locally. The supplied example configuration is intentionally neutral.
