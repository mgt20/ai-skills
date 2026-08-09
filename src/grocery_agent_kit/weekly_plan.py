"""Harness-neutral, review-only planning from a normalized weekly-ad artifact.

This module deliberately does not fetch network data, send messages, modify a cart,
or select a recipe service. Providers and delivery adapters belong at the edges.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date as date_type
from typing import Any, Mapping

from .config import GroceryConfig


class CoverageError(ValueError):
    """Raised when a planner would rely on incomplete or unverified ad data."""


PLANNING_BUCKETS = ("proteins", "produce", "pantry", "dairy/breakfast", "freezer")


def _text(value: Any, fallback: str = "") -> str:
    value = str(value or "").strip()
    return value or fallback


def _is_friday_only(product: Mapping[str, Any]) -> bool:
    start = _text(product.get("valid_from"))[:10]
    end = _text(product.get("valid_to"))[:10]
    return bool(start and start == end)


def _item(product: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "name": _text(product.get("name"), "Unnamed item"),
        "deal": _text(product.get("deal_text"), "price not supplied"),
        "bucket": _text(product.get("bucket"), "other"),
        "page": product.get("page"),
        "valid_from": _text(product.get("valid_from"))[:10],
        "valid_to": _text(product.get("valid_to"))[:10],
        "household_score": int(product.get("household_score") or 0),
    }


def _rank(products: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        (_item(product) for product in products),
        key=lambda item: (-item["household_score"], item["page"] if isinstance(item["page"], int) else 9999, item["name"].lower()),
    )


def build_weekly_plan(cfg: GroceryConfig, ad: Mapping[str, Any], *, date: str | None = None) -> dict[str, Any]:
    """Build a portable, review-only plan from a normalized provider artifact.

    The caller must obtain and normalize provider data first. Coverage status is a
    hard gate so a partial ad cannot be presented as a complete weekly plan.
    """
    coverage = ad.get("coverage")
    if not isinstance(coverage, Mapping) or coverage.get("status") != "ok":
        status = coverage.get("status") if isinstance(coverage, Mapping) else "missing"
        raise CoverageError(f"Weekly-ad coverage must be 'ok' before planning; got {status!r}.")
    products = ad.get("products")
    if not isinstance(products, list) or not products:
        raise ValueError("Weekly-ad artifact requires a non-empty products list.")

    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    friday_only: list[Mapping[str, Any]] = []
    for product in products:
        if not isinstance(product, Mapping):
            continue
        bucket = _text(product.get("bucket"), "other")
        if bucket in PLANNING_BUCKETS and not _is_friday_only(product):
            grouped[bucket].append(product)
        if _is_friday_only(product):
            friday_only.append(product)

    raw_store = ad.get("store")
    raw_publication = ad.get("publication")
    store: Mapping[str, Any] = raw_store if isinstance(raw_store, Mapping) else {}
    publication: Mapping[str, Any] = raw_publication if isinstance(raw_publication, Mapping) else {}
    selected_by_bucket = {bucket: _rank(grouped[bucket])[:3] for bucket in PLANNING_BUCKETS if grouped[bucket]}
    dinner_anchors = selected_by_bucket.get("proteins", [])[:2]

    return {
        "schema_version": 1,
        "date": date or date_type.today().isoformat(),
        "store": {
            "name": _text(store.get("name"), cfg.store.name),
            "store_code": _text(store.get("store_code"), cfg.store.store_id),
            "postal_code": _text(store.get("postal_code"), cfg.store.postal_code),
        },
        "publication": {
            "id": publication.get("id"),
            "valid_from": _text(publication.get("valid_from"))[:10],
            "valid_to": _text(publication.get("valid_to"))[:10],
        },
        "coverage": dict(coverage),
        "dinner_anchors": dinner_anchors,
        "sale_anchors": selected_by_bucket,
        "friday_only": _rank(friday_only)[:6],
        "safety": {
            "cart_modified": False,
            "checkout_performed": False,
            "note": "Review-only output. Choose recipes and approve any cart action in a separate adapter.",
        },
    }


def _line(item: Mapping[str, Any]) -> str:
    window = ""
    if item.get("valid_from") and item.get("valid_to"):
        window = f" ({item['valid_from']}–{item['valid_to']})"
    return f"{item['name']} — {item['deal']}{window}"


def render_plan_markdown(plan: Mapping[str, Any]) -> str:
    """Render a portable review packet without household, harness, or retailer copy."""
    store = plan["store"]
    publication = plan["publication"]
    coverage = plan["coverage"]
    lines = [
        "# This week's grocery plan",
        "",
        f"**Store:** {store['name']} (store `{store['store_code']}`, postal `{store['postal_code']}`)",
        f"**Ad verification:** publication `{publication.get('id')}`; valid {publication.get('valid_from') or 'unknown'} to {publication.get('valid_to') or 'unknown'}.",
        f"**Coverage:** {coverage.get('status')} — {coverage.get('product_count')} products across {coverage.get('page_count')} pages.",
        "**Cart boundary:** No cart was modified. Recipe selection and cart actions require separate explicit approval.",
        "",
        "## Dinner anchors",
    ]
    dinners = plan.get("dinner_anchors", [])
    if dinners:
        lines.extend(f"- {_line(item)}" for item in dinners)
    else:
        lines.append("- No protein anchors were found. Select recipes manually after reviewing the ad.")
    lines.extend(["", "## Best sale anchors"])
    for bucket, items in plan.get("sale_anchors", {}).items():
        if items:
            lines.append(f"### {bucket}")
            lines.extend(f"- {_line(item)}" for item in items)
    lines.extend(["", "## Single-day offers"])
    friday_only = plan.get("friday_only", [])
    if friday_only:
        lines.extend(f"- {_line(item)}" for item in friday_only)
    else:
        lines.append("- None detected in the verified artifact.")
    lines.extend(["", "## Next review step", "- Pick up to two recipes that fit the dinner anchors and your household constraints. Confirm any member/coupon requirements in the retailer cart before purchasing."])
    return "\n".join(lines) + "\n"
