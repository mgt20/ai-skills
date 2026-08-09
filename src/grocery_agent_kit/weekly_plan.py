"""Harness-neutral, review-only planning from a normalized weekly-ad artifact.

This module performs no network, delivery, cart, checkout, or recipe-provider
operations. It validates provider data before rendering a review artifact.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date as date_type
import re
from typing import Any, Mapping

from .config import GroceryConfig
from .household import score_household_match


class PlanValidationError(ValueError):
    """Raised when a provider artifact violates the normalized-plan contract."""


class CoverageError(PlanValidationError):
    """Raised when a planner would rely on incomplete or unverified ad data."""


PLANNING_BUCKETS = ("proteins", "produce", "pantry", "dairy/breakfast", "freezer")
_PLACEHOLDER_STORE_VALUES = {"", "YOUR_STORE_ID", "POSTAL_CODE_REQUIRED", "Your Grocery Store"}


def _text(value: Any, field: str, *, maximum: int = 300) -> str:
    if not isinstance(value, str):
        raise PlanValidationError(f"{field} must be a string")
    normalized = re.sub(r"\s+", " ", value).strip()
    if not normalized:
        raise PlanValidationError(f"{field} must not be empty")
    if len(normalized) > maximum:
        raise PlanValidationError(f"{field} exceeds {maximum} characters")
    return normalized


def _date(value: Any, field: str) -> date_type:
    raw = _text(value, field, maximum=64)
    if len(raw) < 10:
        raise PlanValidationError(f"{field} must use YYYY-MM-DD")
    try:
        return date_type.fromisoformat(raw[:10])
    except ValueError as exc:
        raise PlanValidationError(f"{field} must use YYYY-MM-DD") from exc


def _mapping(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise PlanValidationError(f"{field} must be an object")
    return value


def _is_single_day(product: Mapping[str, Any]) -> bool:
    return product["valid_from"] == product["valid_to"]


def _normalized_product(raw: Any, index: int, publication_start: date_type, publication_end: date_type, rules: list[dict[str, Any]] | None) -> dict[str, Any]:
    product = _mapping(raw, f"products[{index}]")
    start = _date(product.get("valid_from"), f"products[{index}].valid_from")
    end = _date(product.get("valid_to"), f"products[{index}].valid_to")
    if end < start:
        raise PlanValidationError(f"products[{index}] has an invalid date window")
    if end < publication_start or start > publication_end:
        raise PlanValidationError(f"products[{index}] falls outside the publication window")
    page = product.get("page")
    if not isinstance(page, int) or page < 1:
        raise PlanValidationError(f"products[{index}].page must be a positive integer")
    bucket = _text(product.get("bucket"), f"products[{index}].bucket", maximum=64)
    dynamic_match = score_household_match(product, rules) if rules else None
    score = int(dynamic_match["household_score"]) if dynamic_match else int(product.get("household_score") or 0)
    return {
        "name": _text(product.get("name"), f"products[{index}].name"),
        "deal": _text(product.get("deal_text"), f"products[{index}].deal_text"),
        "bucket": bucket,
        "page": page,
        "valid_from": start.isoformat(),
        "valid_to": end.isoformat(),
        "household_score": score,
    }


def _rank(products: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(products, key=lambda item: (-item["household_score"], item["page"], item["name"].lower()))


def _assert_expected_store(cfg: GroceryConfig, store: Mapping[str, Any]) -> None:
    expected = (("store_code", cfg.store.store_id), ("postal_code", cfg.store.postal_code))
    for artifact_field, configured_value in expected:
        if configured_value not in _PLACEHOLDER_STORE_VALUES and store[artifact_field] != configured_value:
            raise PlanValidationError(
                f"Provider artifact {artifact_field}={store[artifact_field]!r} does not match configured store {configured_value!r}"
            )


def build_weekly_plan(cfg: GroceryConfig, ad: Any, *, date: str | None = None) -> dict[str, Any]:
    """Build a portable, review-only plan from a validated provider artifact."""
    if not isinstance(ad, Mapping):
        raise PlanValidationError("Weekly-ad artifact must be a JSON object")
    coverage = _mapping(ad.get("coverage"), "coverage")
    if coverage.get("status") != "ok":
        raise CoverageError(f"Weekly-ad coverage must be 'ok' before planning; got {coverage.get('status')!r}.")
    product_count = coverage.get("product_count")
    page_count = coverage.get("page_count")
    if not isinstance(product_count, int) or product_count < 1:
        raise PlanValidationError("coverage.product_count must be a positive integer")
    if not isinstance(page_count, int) or page_count < 1:
        raise PlanValidationError("coverage.page_count must be a positive integer")

    raw_store = _mapping(ad.get("store"), "store")
    store = {
        "name": _text(raw_store.get("name"), "store.name"),
        "store_code": _text(raw_store.get("store_code"), "store.store_code", maximum=100),
        "postal_code": _text(raw_store.get("postal_code"), "store.postal_code", maximum=32),
    }
    _assert_expected_store(cfg, store)

    raw_publication = _mapping(ad.get("publication"), "publication")
    publication_start = _date(raw_publication.get("valid_from"), "publication.valid_from")
    publication_end = _date(raw_publication.get("valid_to"), "publication.valid_to")
    if publication_end < publication_start:
        raise PlanValidationError("publication has an invalid date window")
    publication_id = _text(str(raw_publication.get("id") or ""), "publication.id", maximum=100)
    plan_date = _date(date or date_type.today().isoformat(), "date")
    if not publication_start <= plan_date <= publication_end:
        raise PlanValidationError("Plan date falls outside the verified publication window")

    raw_products = ad.get("products")
    if not isinstance(raw_products, list) or not raw_products:
        raise PlanValidationError("Weekly-ad artifact requires a non-empty products list")
    if product_count != len(raw_products):
        raise PlanValidationError("coverage.product_count does not match products length")
    products = [
        _normalized_product(product, index, publication_start, publication_end, cfg.household.staples)
        for index, product in enumerate(raw_products)
    ]
    observed_pages = {product["page"] for product in products}
    if page_count != len(observed_pages):
        raise PlanValidationError("coverage.page_count does not match product pages")

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    single_day_offers: list[dict[str, Any]] = []
    for product in products:
        if product["bucket"] in PLANNING_BUCKETS and not _is_single_day(product):
            grouped[product["bucket"]].append(product)
        if _is_single_day(product):
            single_day_offers.append(product)
    selected_by_bucket = {bucket: _rank(grouped[bucket])[:3] for bucket in PLANNING_BUCKETS if grouped[bucket]}

    return {
        "schema_version": 1,
        "date": plan_date.isoformat(),
        "store": store,
        "publication": {"id": publication_id, "valid_from": publication_start.isoformat(), "valid_to": publication_end.isoformat()},
        "coverage": {"status": "ok", "product_count": product_count, "page_count": page_count, "page_range": str(coverage.get("page_range") or "unknown")},
        "dinner_anchors": selected_by_bucket.get("proteins", [])[:2],
        "sale_anchors": selected_by_bucket,
        "single_day_offers": _rank(single_day_offers)[:6],
        "safety": {"cart_modified": False, "checkout_performed": False, "note": "Review-only output. Choose recipes and approve any cart action in a separate adapter."},
    }


def _line(item: Mapping[str, Any]) -> str:
    return f"{item['name']} — {item['deal']} ({item['valid_from']}–{item['valid_to']})"


def render_plan_markdown(plan: Mapping[str, Any]) -> str:
    """Render a portable review packet from values validated by ``build_weekly_plan``."""
    store = plan["store"]
    publication = plan["publication"]
    coverage = plan["coverage"]
    lines = [
        "# This week's grocery plan", "",
        f"**Store:** {store['name']} (store `{store['store_code']}`, postal `{store['postal_code']}`)",
        f"**Ad verification:** publication `{publication['id']}`; valid {publication['valid_from']} to {publication['valid_to']}.",
        f"**Coverage:** {coverage['status']} — {coverage['product_count']} products across {coverage['page_count']} pages.",
        "**Cart boundary:** No cart was modified. Recipe selection and cart actions require separate explicit approval.", "",
        "## Dinner anchors",
    ]
    dinners = plan["dinner_anchors"]
    lines.extend(f"- {_line(item)}" for item in dinners) if dinners else lines.append("- No protein anchors were found. Select recipes manually after reviewing the ad.")
    lines.extend(["", "## Best sale anchors"])
    for bucket, items in plan["sale_anchors"].items():
        if items:
            lines.append(f"### {bucket}")
            lines.extend(f"- {_line(item)}" for item in items)
    lines.extend(["", "## Single-day offers"])
    offers = plan["single_day_offers"]
    lines.extend(f"- {_line(item)}" for item in offers) if offers else lines.append("- None detected in the verified artifact.")
    lines.extend(["", "## Next review step", "- Pick up to two recipes that fit the dinner anchors and your household constraints. Confirm any member/coupon requirements in the retailer cart before purchasing."])
    return "\n".join(lines) + "\n"
