# Architecture

`grocery_agent_kit` is the harness-neutral layer: configuration loading,
household scoring, plan construction, recipe-provider protocols, and rendering.
Store-specific extraction and all external side effects live at the edges.

## Core boundary

The core accepts a **normalized weekly-ad artifact** and emits reviewable plan
artifacts. It does not know about a specific retailer, home address, family, agent
harness, messaging service, cart, payment method, or credentials.

`grocery_agent_kit.weekly_plan.build_weekly_plan()` has a hard precondition:
`artifact.coverage.status` must be `"ok"`. It rejects partial/unverified ad data
rather than presenting it as a current plan.

## Normalized ad artifact contract (v1)

A store provider must produce JSON containing:

```json
{
  "store": {"name": "Example Market", "store_code": "example-001", "postal_code": "POSTAL_CODE_REQUIRED"},
  "publication": {"id": "provider-week", "valid_from": "YYYY-MM-DD", "valid_to": "YYYY-MM-DD"},
  "coverage": {"status": "ok", "product_count": 42, "page_count": 4, "page_range": "1-4"},
  "products": [
    {
      "name": "Product name",
      "deal_text": "$3.99 each",
      "bucket": "proteins",
      "page": 1,
      "valid_from": "YYYY-MM-DD",
      "valid_to": "YYYY-MM-DD",
      "household_score": 0
    }
  ]
}
```

Supported planning buckets are `proteins`, `produce`, `pantry`,
`dairy/breakfast`, and `freezer`; other values are retained by a provider but not
used as default plan anchors. A single-day item (`valid_from == valid_to`) is
rendered separately, never mixed into week-long anchors.

## Extension contracts

- **Store providers** fetch and normalize a retailer’s data into the v1 artifact.
  They must report coverage honestly and use sanitized static fixtures in tests.
- **Recipe providers** implement the existing `RecipeProvider` protocol. They may
  use plan anchors but must be optional, failure-tolerant, and network-isolated in
  unit tests.
- **Harness adapters** perform setup, scheduling, delivery, and approval-gated
  cart actions. They consume core artifacts; they must not change core planning
  rules.
- **Output adapters** may transform core Markdown/JSON to Slack, email, or a
  shopping-list application. They need explicit user approval before sends or
  cart mutations.

## Privacy model

A shared checkout starts with no household ranking rules. Put family preferences,
store identifiers, receipt history, destinations, and credentials only in an
ignored private config or external secret store. The repository’s privacy test
must remain green before any public release.

## Current milestone

Phase 1 delivers fixture-driven, review-only plan generation. The next increment
is a recipe-selection adapter that consumes `dinner_anchors` without moving live
network access or household assumptions into the core.
