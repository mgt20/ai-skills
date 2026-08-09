# Architecture

`grocery_agent_kit` is the harness-neutral layer: config loading, household scoring, recipe selection, and renderers. Store-specific extraction lives in `scripts/` until it is promoted behind a `StoreAdProvider` contract. Harness adapters must only orchestrate setup, scheduling, and delivery; they must not change planning logic.

## Extension contracts

- **Store providers** produce normalized product records with name, deal text, date window, category, and coverage metadata.
- **Recipe providers** implement the existing `RecipeProvider` protocol.
- **Harness adapters** consume local artifacts and enforce approval gates for external sends/cart actions.

The next milestone extracts the Safeway renderer into a generic plan model and adds provider interfaces under `src/grocery_agent_kit/providers/`.
