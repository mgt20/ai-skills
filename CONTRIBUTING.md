# Contributing

Start with an issue for a new store, recipe provider, harness adapter, or output integration.

## Rules

1. Core code must not depend on a specific agent harness or household.
2. Store integrations require sanitized fixtures and offline tests.
3. Never submit secrets, account identifiers, home addresses, receipts, or generated household artifacts.
4. Cart, order, payment, and message sends must be explicit opt-in adapters with approval gates.
5. Update the compatibility matrix when adding a verified integration.

Run the test suite and public-data scan before opening a pull request.
