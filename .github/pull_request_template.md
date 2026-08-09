## Summary

What does this change add or alter? Keep the core harness-neutral.

## Safety and scope

- [ ] No credentials, personal configuration, receipts, destinations, generated plans, or account/cart state included
- [ ] No checkout/payment capability added
- [ ] Any network, messaging, or cart action remains an explicit edge adapter
- [ ] Current-price claims are backed by a provider artifact with coverage metadata

## Verification

- [ ] Added/updated a sanitized fixture when changing a provider
- [ ] Added regression tests for changed behavior
- [ ] `python3 -m unittest discover -s tests -v` passes
- [ ] `PYTHONPATH=src python3 -m py_compile src/grocery_agent_kit/*.py` passes
- [ ] Privacy scan remains green

## Compatibility

List any changes to artifact schemas, CLI behavior, config keys, or harness adapters.
