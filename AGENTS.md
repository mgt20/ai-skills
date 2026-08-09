# AI Skills Repository Contract

## Purpose

This repository stores shareable AI operating material: portable skills, rules,
prompts, templates, examples, and supporting documentation. It must remain safe to
clone, review, and merge into another harness.

## Placement

- Put a reusable skill in `skills/<skill-name>/SKILL.md`.
- Keep skill-specific references in `skills/<skill-name>/references/`, neutral
  starter files in `templates/`, and optional non-secret assets under that skill.
- Put cross-skill behavioral constraints in `rules/`.
- Put reusable prompts in `prompts/` and starting structures in `templates/`.
- Put only sanitized, reproducible examples in `examples/`.

## Safety boundary

Never commit credentials, API tokens, cookies, addresses, private store/account
identifiers, receipt data, direct-message destinations, personal config files, or
generated household artifacts. Keep these in local secrets/config outside this
repository.

Skills must make external actions opt-in: no send, cart mutation, checkout,
payment, ordering, or destructive system action without explicit user approval.

## Verification

- New skills need YAML frontmatter and a non-empty `SKILL.md`.
- References linked by a skill must exist after copying that skill directory alone.
- Add or update a focused regression test when changing a portable contract.
- Run `PYTHONPATH=src python3 -m unittest discover -s tests -v` before committing
  changes that affect the grocery engine or its examples.
