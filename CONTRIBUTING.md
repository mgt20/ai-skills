# Contributing to AI Skills

This repository is a catalog of portable AI skills, rules, prompts, templates, and
supporting Markdown. Start with [AGENTS.md](AGENTS.md), then open an issue before
a substantial new skill, external integration, or behavioral rule.

## Contribution rules

1. Put reusable skills in `skills/<skill-name>/` with a valid `SKILL.md` and
   self-contained references/templates.
2. Keep root-level rules, prompts, and templates harness-neutral and reusable.
3. Never submit secrets, account identifiers, home addresses, receipts, private
   preferences, delivery destinations, or generated household artifacts.
4. External actions—messages, cart edits, orders, payments, deployment, or
   destructive system changes—must be explicit opt-in adapters with approval gates.
5. Add sanitized examples and focused tests for any portable contract.
6. Run the relevant test suite and public-data/history checks before opening a PR.

The Grocery Planner is one included skill. Its engine and adapter-specific design
docs live with its implementation; they do not define the scope of this catalog.
