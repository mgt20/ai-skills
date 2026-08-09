# AI Skills

A private, version-controlled home for reusable AI skills, behavioral rules,
prompts, templates, and operator-facing Markdown. Each portable skill lives in its
own subdirectory so it can be copied into another agent harness without flattening
its supporting files.

## Repository layout

```text
skills/       # portable SKILL.md directories, references, templates, assets
rules/        # reusable agent policies and operating constraints
prompts/      # reusable task/system/onboarding prompts
templates/    # starter files for new skills, rules, and prompts
docs/         # architecture and contributor documentation
examples/     # sanitized, committed outputs and fixtures
AGENTS.md     # repository-wide contribution and safety contract
```

## Install a skill

```bash
git clone https://github.com/mgt20/ai-skills.git
cd ai-skills

# For Hermes or another directory-based skill loader:
mkdir -p ~/.hermes/skills
cp -a skills/. ~/.hermes/skills/
```

Copying `skills/` preserves each skill directory. A skill may reference an optional
engine or adapter stored elsewhere in this repository; keep the clone available
when the skill says it needs a repository workdir.

## Included skill: Grocery Planner

`skills/grocery-planner/` is a portable, review-only grocery-planning skill. It
contains its own `SKILL.md`, LLM onboarding reference, and neutral config template.
The optional Python engine is tested locally and deliberately excludes recipe
providers, messaging, cart actions, payment, checkout, credentials, and household
history.

Install its optional local engine:

```bash
python3 -m pip install -e .
```

## Example review packet

The following is an **offline, sanitized fixture output**, not a current ad or
shopping recommendation. It demonstrates the local review packet produced by the
Grocery Planner skill after a provider artifact passes coverage, store, and date
validation.

<!-- BEGIN GROCERY-PLANNER-EXAMPLE -->

```markdown
# This week's grocery plan

**Store:** Example Market (store `demo`, postal `POSTAL_CODE_REQUIRED`)
**Ad verification:** publication `demo-2026-01`; valid 2026-01-01 to 2026-01-07.
**Coverage:** ok — 7 products across 2 pages.
**Cart boundary:** No cart was modified. Recipe selection and cart actions require separate explicit approval.

## Dinner anchors
- Chicken Thighs — $2.49 lb (2026-01-01–2026-01-07)
- Frozen Shrimp — $7.99 ea (2026-01-01–2026-01-07)

## Best sale anchors
### proteins
- Chicken Thighs — $2.49 lb (2026-01-01–2026-01-07)
- Frozen Shrimp — $7.99 ea (2026-01-01–2026-01-07)
### produce
- Salad Kit — 2 for $5.00 (2026-01-01–2026-01-07)
### pantry
- Pasta — $1.25 ea (2026-01-01–2026-01-07)
### dairy/breakfast
- Milk — $3.49 ea (2026-01-01–2026-01-07)
### freezer
- Frozen Pizza — $4.99 ea (2026-01-01–2026-01-07)

## Single-day offers
- Friday Strawberries — $5.00 ea (2026-01-02–2026-01-02)

## Next review step
- Pick up to two recipes that fit the dinner anchors and your household constraints. Confirm any member/coupon requirements in the retailer cart before purchasing.
```

<!-- END GROCERY-PLANNER-EXAMPLE -->

The source fixture and regression tests are local-only and contain no live store,
household, account, receipt, or payment data.

## Rules for contributions

Read [AGENTS.md](AGENTS.md) before adding a skill, rule, prompt, or template.
Keep private configs, receipts, credentials, personal destinations, and generated
household artifacts out of the repository. Add a small example or test whenever a
new portable contract is introduced.
