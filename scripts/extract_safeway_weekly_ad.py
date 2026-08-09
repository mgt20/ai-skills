#!/usr/bin/env python3
"""Extract and normalize Safeway weekly-ad products from Flipp JSON.

Stdlib-only on purpose: this is intended to be safe for cron/profile usage without
extra package dependencies. Safeway's weekly-ad page is often JS-heavy, so a
browser-discovered --products-url is the reliable first-class path.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import pathlib
import re
import sys
import urllib.error

# Allow direct execution from a source checkout without requiring installation.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
import urllib.parse
import urllib.request
from collections import Counter
from typing import Any

from grocery_agent_kit.config import load_config
from grocery_agent_kit.household import DEFAULT_HOUSEHOLD_RULES, score_household_match as configured_household_score

SAFEWAY_SET_STORE_URL = "https://www.safeway.com/set-store.html"
DEFAULT_STORE_ID = ""
DEFAULT_POSTAL_CODE = ""
STORE_NAME_BY_ID: dict[str, str] = {}
BUCKETS = ["proteins", "produce", "dairy/breakfast", "pantry", "freezer", "beverages", "household", "other"]
USER_AGENT = "Mozilla/5.0 (compatible; HermesSafewayWeeklyAdExtractor/1.0)"
HOUSEHOLD_RULES = DEFAULT_HOUSEHOLD_RULES


def _text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _format_money(value: str) -> str:
    value = _text(value)
    if not value:
        return ""
    if value.startswith("$"):
        numeric = value[1:]
    else:
        numeric = value
    if re.fullmatch(r"\d+(?:\.\d+)?", numeric):
        return f"${float(numeric):.2f}"
    return value


def format_price(item: dict[str, Any]) -> str:
    """Return a readable deal string from Flipp price fragments."""
    pre = _text(item.get("pre_price_text"))
    price = _format_money(_text(item.get("price_text")))
    post = _text(item.get("post_price_text"))
    return " ".join(part for part in (pre, price, post) if part)


def _extract_unit_hint(description: Any) -> str:
    desc = _text(description)
    if not desc:
        return ""
    match = re.search(r"(?:Member Price:\s*)?(\$\d+(?:\.\d{1,2})?\s*(?:ea|lb|oz|each|/lb)\.?)", desc, re.I)
    if not match:
        return ""
    return match.group(1).rstrip(".")


def _category_words(product: dict[str, Any]) -> str:
    bits: list[str] = []
    bits.append(_text(product.get("name")))
    bits.append(_text(product.get("description")))
    cats = product.get("categories") or []
    if isinstance(cats, list):
        bits.extend(_text(cat) for cat in cats)
    item_categories = product.get("item_categories") or {}
    if isinstance(item_categories, dict):
        for entry in item_categories.values():
            if isinstance(entry, dict):
                bits.append(_text(entry.get("category_name")))
    return " ".join(bits).lower()


def category_bucket(product: dict[str, Any]) -> str:
    """Map a normalized/raw product to grocery-planner buckets."""
    words = _category_words(product)
    rules = [
        ("proteins", ["meat", "seafood", "chicken", "beef", "pork", "salmon", "lamb", "turkey", "crab", "shrimp", "sausage", "bacon", "egg"]),
        ("produce", ["fruit", "vegetable", "produce", "cucumber", "orange", "lemon", "apple", "berry", "salad", "lettuce", "tomato", "avocado"]),
        ("dairy/breakfast", ["dairy", "milk", "cheese", "yogurt", "butter", "cream", "breakfast", "cereal", "bagel", "muffin", "coffee creamer"]),
        ("freezer", ["frozen", "ice cream", "freezer"]),
        ("beverages", ["beverage", "water", "soda", "coffee", "tea", "juice", "drink", "hydration", "latte"]),
        ("household", ["paper", "cleaning", "home", "laundry", "detergent", "tide", "bounty", "foil", "trash", "roses", "floral", "baby care"]),
        ("pantry", ["pasta", "grain", "snack", "cracker", "cookie", "bread", "bakery", "sauce", "canned", "condiment", "bar", "fruit snacks"]),
    ]
    for bucket, needles in rules:
        if any(needle in words for needle in needles):
            return bucket
    return "other"


def score_household_match(product: dict[str, Any]) -> dict[str, Any]:
    return configured_household_score(product, HOUSEHOLD_RULES)


def normalize_product(item: dict[str, Any]) -> dict[str, Any]:
    preserved = (
        "name",
        "page",
        "categories",
        "pre_price_text",
        "price_text",
        "post_price_text",
        "description",
        "valid_from",
        "valid_to",
    )
    product = {field: item.get(field) for field in preserved}
    product["deal_text"] = format_price(item)
    product["unit_hint"] = _extract_unit_hint(item.get("description"))
    product["bucket"] = category_bucket(item)
    product.update(score_household_match(product))
    # Useful compact traceability for appendix/debugging without carrying every raw field.
    for field in ("id", "flyer_id", "valid_from_timestamp", "valid_to_timestamp"):
        if field in item:
            product[field] = item.get(field)
    return product


def summarize_pages(products: list[dict[str, Any]]) -> dict[str, int]:
    counts = Counter(str(product.get("page")) for product in products if product.get("page") is not None)
    return {page: counts[page] for page in sorted(counts, key=lambda value: int(value) if value.isdigit() else value)}


def _page_sort_value(product: dict[str, Any]) -> int:
    page = product.get("page")
    return page if isinstance(page, int) else 9999


def build_coverage(products: list[dict[str, Any]], min_products: int, min_pages: int) -> dict[str, Any]:
    page_values: set[int] = set()
    for product in products:
        page = product.get("page")
        if isinstance(page, int):
            page_values.add(page)
    pages = sorted(page_values)
    page_counts = summarize_pages(products)
    min_page = min(pages) if pages else None
    max_page = max(pages) if pages else None
    expected_pages = set(range(min_page, max_page + 1)) if min_page is not None and max_page is not None else set()
    missing_pages = sorted(expected_pages - set(pages))
    first_page_only = pages == [1]
    warnings: list[str] = []
    if len(products) < min_products:
        warnings.append(f"Product count {len(products)} is below expected minimum {min_products}.")
    if len(pages) < min_pages:
        warnings.append(f"Page coverage {len(pages)} is below expected minimum {min_pages}.")
    if first_page_only:
        warnings.append("Coverage appears to include first page only; flyer extraction is likely truncated.")
    if missing_pages:
        warnings.append(f"Missing flyer pages inside observed range: {missing_pages}.")
    failed = first_page_only or len(products) < min_products or len(pages) < min_pages
    status = "ok" if not warnings else "failed" if failed else "warning"
    page_range = f"{min_page}-{max_page}" if min_page is not None and max_page is not None else "none"
    return {
        "status": status,
        "product_count": len(products),
        "page_count": len(pages),
        "min_page": min_page,
        "max_page": max_page,
        "page_range": page_range,
        "pages_present": pages,
        "missing_pages": missing_pages,
        "page_counts": page_counts,
        "first_page_only": first_page_only,
        "warnings": warnings,
    }


def is_exact_five_candidate(product: dict[str, Any]) -> bool:
    price = _text(product.get("price_text"))
    if price.startswith("$"):
        price = price[1:]
    if not re.fullmatch(r"5(?:\.0{1,2})?", price):
        return False
    deal = _text(product.get("deal_text") or format_price(product)).lower()
    return bool(re.search(r"(?:^|\s)(?:\d+\s+for\s+)?\$?5\.00\s*(?:ea|each|member price|lb|/lb)?", deal))


def _publication_id_from_url(url: str) -> int | None:
    match = re.search(r"/publication/(\d+)/products", url)
    return int(match.group(1)) if match else None


def fetch_json(url: str, timeout: int = 45) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json,*/*"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return json.loads(response.read().decode(charset))


def fetch_text(url: str, timeout: int = 30) -> tuple[str, str]:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,*/*"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace"), response.geturl()


def discover_products_url(store_id: str, postal_code: str) -> tuple[str | None, list[str]]:
    """Best-effort stdlib discovery from Safeway HTML; returns warnings on JS-only pages."""
    warnings: list[str] = []
    params = urllib.parse.urlencode({"storeId": store_id, "target": "weeklyad"})
    url = f"{SAFEWAY_SET_STORE_URL}?{params}"
    try:
        html, final_url = fetch_text(url)
    except (urllib.error.URLError, TimeoutError) as exc:
        return None, [f"Could not fetch Safeway weekly-ad discovery page: {exc}. Use --products-url."]

    match = re.search(r"https://dam\.flippenterprise\.net/flyerkit/publication/\d+/products\?[^\"'<>\\]+", html)
    if match:
        return match.group(0).replace("&amp;", "&"), warnings

    pub_match = re.search(r"publication[/=](\d{6,})", html)
    token_match = re.search(r"access_token[=:][\"']?([a-zA-Z0-9]+)", html)
    if pub_match and token_match:
        pub = pub_match.group(1)
        token = token_match.group(1)
        return f"https://dam.flippenterprise.net/flyerkit/publication/{pub}/products?display_type=all&locale=en&access_token={token}", warnings

    warnings.append(
        "Safeway weekly-ad discovery appears JS-only or did not expose the Flipp products URL "
        f"(final URL: {final_url}); rerun with --products-url."
    )
    return None, warnings


def _trusted_products_url(url: str) -> bool:
    """Allow only the HTTPS Flipp products endpoint used by this adapter."""
    try:
        parsed = urllib.parse.urlparse(url)
        return (
            parsed.scheme == "https"
            and parsed.hostname == "dam.flippenterprise.net"
            and bool(re.fullmatch(r"/flyerkit/publication/\d+/products", parsed.path))
        )
    except ValueError:
        return False


def _coerce_products(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("products", "items", "data"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
    raise ValueError("Products JSON did not contain a product list")


def _build_publication(raw_products: list[dict[str, Any]], products_url: str) -> dict[str, Any]:
    pub_id = _publication_id_from_url(products_url)
    valid_from = next((p.get("valid_from_timestamp") or p.get("valid_from") for p in raw_products if p.get("valid_from_timestamp") or p.get("valid_from")), None)
    valid_to = next((p.get("valid_to_timestamp") or p.get("valid_to") for p in raw_products if p.get("valid_to_timestamp") or p.get("valid_to")), None)
    pages: list[int] = []
    for product in raw_products:
        page = product.get("page")
        if isinstance(page, int):
            pages.append(page)
    return {
        "id": pub_id,
        "valid_from": valid_from,
        "valid_to": valid_to,
        "total_pages": max(pages) if pages else 0,
    }


def summarize_by_bucket(products: list[dict[str, Any]]) -> dict[str, Any]:
    summaries: dict[str, Any] = {bucket: [] for bucket in BUCKETS}
    sorted_products = sorted(products, key=lambda p: (-int(p.get("household_score") or 0), _page_sort_value(p), _text(p.get("name")).lower()))
    for product in sorted_products:
        bucket = product.get("bucket") or "other"
        if bucket not in summaries:
            bucket = "other"
        if len(summaries[bucket]) < 12:
            summaries[bucket].append(product)
    summaries["five_friday_candidates"] = [p for p in products if is_exact_five_candidate(p)]
    summaries["notable_easy_produce"] = [p for p in sorted_products if p.get("bucket") == "produce"][:12]
    summaries["household_staple_matches"] = [p for p in sorted_products if int(p.get("household_score") or 0) > 0][:20]
    return summaries


def _redact_products_url(url: str) -> str:
    """Keep a source reference without persisting access credentials in artifacts."""
    parsed = urllib.parse.urlparse(url)
    query = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    sensitive = {"access_token", "api_key", "token", "authorization"}
    redacted = [(key, value) for key, value in query if key.lower() not in sensitive]
    return urllib.parse.urlunparse(parsed._replace(query=urllib.parse.urlencode(redacted)))


def build_artifact(
    raw_products: list[dict[str, Any]],
    store_id: str = DEFAULT_STORE_ID,
    postal_code: str = DEFAULT_POSTAL_CODE,
    products_url: str = "",
    discovery_warnings: list[str] | None = None,
    min_products: int = 100,
    min_pages: int = 3,
) -> dict[str, Any]:
    products = [normalize_product(item) for item in raw_products]
    pages = summarize_pages(products)
    coverage = build_coverage(products, min_products=min_products, min_pages=min_pages)
    warnings = list(discovery_warnings or [])
    warnings.extend(coverage["warnings"])
    if (DEFAULT_STORE_ID and store_id != DEFAULT_STORE_ID) or (DEFAULT_POSTAL_CODE and postal_code != DEFAULT_POSTAL_CODE):
        warnings.append(f"Store/postal values differ from configured defaults: store_id={store_id} postal_code={postal_code}.")
    if not products_url:
        warnings.append("Products URL is missing.")

    return {
        "store": {"name": STORE_NAME_BY_ID.get(store_id, "Safeway"), "store_code": str(store_id), "postal_code": str(postal_code)},
        "publication": _build_publication(raw_products, products_url),
        "products_url": _redact_products_url(products_url),
        "product_count": len(products),
        "page_count": len(pages),
        "pages": pages,
        "coverage": coverage,
        "warnings": warnings,
        "products": products,
        "summaries": summarize_by_bucket(products),
        "generated_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
    }


def _household_note(item: dict[str, Any]) -> str:
    score = int(item.get("household_score") or 0)
    if score <= 0:
        return ""
    reasons = "; ".join(_text(reason) for reason in item.get("household_reasons", []) if _text(reason))
    return f" — score {score}; {reasons}" if reasons else f" — score {score}"


def render_markdown(artifact: dict[str, Any]) -> str:
    store = artifact["store"]
    pub = artifact["publication"]
    pages = artifact["pages"]
    summaries = artifact["summaries"]
    coverage = artifact.get("coverage") or {}
    lines: list[str] = []
    lines.append(f"# Safeway Weekly Ad Extract — {store['name']}")
    lines.append("")
    lines.append(
        f"Store `{store['store_code']}` / `{store['postal_code']}`; publication `{pub.get('id')}`; "
        f"valid `{pub.get('valid_from')}` to `{pub.get('valid_to')}`."
    )
    lines.append(
        f"Products: **{artifact['product_count']}** across **{artifact['page_count']}** pages "
        f"(range {coverage.get('page_range', 'unknown')}; coverage {coverage.get('status', 'unknown')}; max page {pub.get('total_pages')})."
    )
    lines.append("")
    lines.append("## Coverage / warnings")
    lines.append(f"Page range: {coverage.get('page_range', 'unknown')}; status: {coverage.get('status', 'unknown')}")
    lines.append(f"Pages present: {', '.join(str(page) for page in coverage.get('pages_present', [])) or 'none'}")
    if coverage.get("missing_pages"):
        lines.append(f"Missing pages: {', '.join(str(page) for page in coverage['missing_pages'])}")
    if coverage.get("first_page_only"):
        lines.append("First-page-only: true")
    lines.append(f"Page counts: {', '.join(f'{page}:{count}' for page, count in pages.items())}")
    if artifact.get("warnings"):
        lines.extend(f"- WARNING: {warning}" for warning in artifact["warnings"])
    else:
        lines.append("- No warnings.")
    lines.append("")
    lines.append("## Household staple sale matches")
    household_matches = summaries.get("household_staple_matches", [])[:15]
    if household_matches:
        for item in household_matches:
            hint = f" ({item['unit_hint']})" if item.get("unit_hint") else ""
            lines.append(f"- p{item.get('page')}: {item.get('name')} — {item.get('deal_text')}{hint}{_household_note(item)}")
    else:
        lines.append("- None detected.")
    lines.append("")
    lines.append("## Best sale anchors by category")
    for bucket in BUCKETS:
        items = summaries.get(bucket, [])[:6]
        if not items:
            continue
        lines.append(f"### {bucket}")
        for item in items:
            hint = f" ({item['unit_hint']})" if item.get("unit_hint") else ""
            lines.append(f"- p{item.get('page')}: {item.get('name')} — {item.get('deal_text')}{hint}{_household_note(item)}")
        lines.append("")
    lines.append("## Notable easy produce")
    for item in summaries.get("notable_easy_produce", [])[:12]:
        hint = f" ({item['unit_hint']})" if item.get("unit_hint") else ""
        lines.append(f"- p{item.get('page')}: {item.get('name')} — {item.get('deal_text')}{hint}{_household_note(item)}")
    lines.append("")
    lines.append("## $5 Friday candidates")
    candidates = summaries.get("five_friday_candidates", [])
    if candidates:
        for item in candidates:
            lines.append(f"- p{item.get('page')}: {item.get('name')} — {item.get('deal_text')}")
    else:
        lines.append("- None detected.")
    lines.append("")
    lines.append("## Compact appendix")
    lines.append("| Page | Bucket | Item | Deal | Unit hint |")
    lines.append("|---:|---|---|---|---|")
    for item in artifact.get("products", []):
        name = _text(item.get("name")).replace("|", "\\|")
        deal = _text(item.get("deal_text")).replace("|", "\\|")
        hint = _text(item.get("unit_hint")).replace("|", "\\|")
        lines.append(f"| {item.get('page', '')} | {item.get('bucket', '')} | {name} | {deal} | {hint} |")
    lines.append("")
    return "\n".join(lines)


def write_artifacts(artifact: dict[str, Any], out_dir: pathlib.Path) -> dict[str, pathlib.Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "latest_extract.json"
    md_path = out_dir / "latest_extract.md"
    json_path.write_text(json.dumps(artifact, indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(render_markdown(artifact), encoding="utf-8")
    stamp = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    stamped_json = out_dir / f"extract_{stamp}.json"
    stamped_md = out_dir / f"extract_{stamp}.md"
    stamped_json.write_text(json_path.read_text(encoding="utf-8"), encoding="utf-8")
    stamped_md.write_text(md_path.read_text(encoding="utf-8"), encoding="utf-8")
    return {"json": json_path, "markdown": md_path, "stamped_json": stamped_json, "stamped_markdown": stamped_md}


def run(args: argparse.Namespace) -> int:
    global HOUSEHOLD_RULES
    if args.config:
        try:
            cfg = load_config(args.config)
        except Exception as exc:
            print(f"error: failed to load grocery config: {exc}", file=sys.stderr)
            return 2
        HOUSEHOLD_RULES = cfg.household.staples or DEFAULT_HOUSEHOLD_RULES

    warnings: list[str] = []
    products_url = args.products_url
    if not products_url:
        products_url, warnings = discover_products_url(args.store_id, args.postal_code)
        if not products_url:
            for warning in warnings:
                print(f"warning: {warning}", file=sys.stderr)
            print("error: Flipp products URL could not be discovered from stdlib HTML fetch; pass --products-url.", file=sys.stderr)
            return 2

    if not _trusted_products_url(products_url):
        print("error: --products-url must be an HTTPS dam.flippenterprise.net flyerkit products endpoint.", file=sys.stderr)
        return 2

    try:
        payload = fetch_json(products_url)
        raw_products = _coerce_products(payload)
    except Exception as exc:  # CLI boundary: report clearly.
        print(f"error: failed to fetch/parse products JSON: {exc}", file=sys.stderr)
        return 2

    artifact = build_artifact(
        raw_products,
        store_id=args.store_id,
        postal_code=args.postal_code,
        products_url=products_url,
        discovery_warnings=warnings,
        min_products=args.min_products,
        min_pages=args.min_pages,
    )
    paths = write_artifacts(artifact, pathlib.Path(args.out_dir))

    cucumber = any(product.get("name") == "Cucumber" and product.get("page") == 2 for product in artifact["products"])
    five_count = len(artifact["summaries"]["five_friday_candidates"])
    coverage = artifact["coverage"]
    status = "ok" if not artifact["warnings"] else coverage["status"] if coverage["status"] != "ok" else "warning"
    message = (
        f"{status}: {artifact['store']['name']} weekly ad extracted; "
        f"publication={artifact['publication'].get('id')} products={artifact['product_count']} "
        f"pages={coverage['page_range']} page_count={coverage['page_count']} coverage={coverage['status']} "
        f"cucumber={'yes' if cucumber else 'no'} five_friday_candidates={five_count}"
    )
    print(message)
    if not args.smoke_test:
        print(f"wrote: {paths['json']}")
        print(f"wrote: {paths['markdown']}")
    if args.fail_on_warning and artifact["warnings"]:
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Extract Safeway weekly-ad products from Flipp JSON.")
    parser.add_argument("--store-id", default=DEFAULT_STORE_ID)
    parser.add_argument("--postal-code", default=DEFAULT_POSTAL_CODE)
    parser.add_argument("--out-dir", default="safeway_ad_extract")
    parser.add_argument("--config", default="", help="Optional grocery TOML config for household.staples scoring rules.")
    parser.add_argument("--products-url", default="")
    parser.add_argument("--smoke-test", action="store_true", help="Print a one-line validation summary after writing artifacts.")
    parser.add_argument("--fail-on-warning", action="store_true")
    parser.add_argument("--min-products", type=int, default=100)
    parser.add_argument("--min-pages", type=int, default=3)
    return parser


def main(argv: list[str] | None = None) -> int:
    return run(build_parser().parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
