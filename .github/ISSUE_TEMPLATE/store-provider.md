---
name: Store provider proposal
about: Propose a new grocery-store ad provider
title: "provider: "
labels: "provider"
---

## Store and region

Which retailer/region does this provider support? Link to the official weekly-ad
source if it is publicly accessible. Do not include login sessions, loyalty IDs,
access tokens, receipts, or personal addresses.

## Data availability

- Is the source public, authenticated, browser-only, or API-based?
- How will validity dates and store selection be verified?
- What rate limits, terms, or reliability constraints apply?

## Normalized artifact mapping

Show a **sanitized** example mapping into the [v1 artifact contract](../../docs/architecture.md).
Include product name, deal text, bucket, validity window, coverage calculation,
and any known ambiguities.

## Test plan

- [ ] Static, sanitized fixture with no live-network dependency
- [ ] Coverage-failure case
- [ ] Store/region selection check
- [ ] Contract test through `grocery_agent_kit.weekly_plan`

## Safety

Explain how the provider avoids collecting or committing credentials, account data,
cart state, or payment information.
