from __future__ import annotations

import re
from typing import Any, Mapping, Sequence

DEFAULT_HOUSEHOLD_RULES: list[dict[str, Any]] = [
    {"tag": "milk", "score": 8, "needles": ["milk", "horizon organic", "lucerne milk"], "reason": "milk recurring staple"},
    {"tag": "egg_bites", "score": 9, "needles": ["egg bites", "three bridges"], "reason": "egg bites recurring breakfast staple"},
    {"tag": "berries_fruit", "score": 7, "needles": ["blackberries", "berries", "strawberries", "banana", "mandarin", "clementine", "grapes", "orange", "fruit"], "reason": "fruit/berries recurring produce staple"},
    {"tag": "easy_veg", "score": 8, "needles": ["cucumber", "avocado", "onion", "salad kit", "spinach", "brussels", "tomato", "bell pepper", "vegetable"], "reason": "easy vegetables recurring produce staple"},
    {"tag": "cheese_dairy", "score": 6, "needles": ["tillamook", "cheese", "yogurt"], "reason": "cheese/dairy repeat signal"},
    {"tag": "kid_snacks_drinks", "score": 7, "needles": ["mott", "juice", "gogo squeez", "applesauce", "snack tray", "lunchables", "fruit snacks"], "reason": "kid snacks/drinks repeat signal"},
    {"tag": "chicken_turkey", "score": 6, "needles": ["chicken", "turkey"], "reason": "chicken/turkey repeat protein signal"},
    {"tag": "seafood", "score": 5, "needles": ["salmon", "shrimp", "fish", "seafood", "crab"], "reason": "seafood repeat protein signal"},
    {"tag": "frozen_convenience", "score": 5, "needles": ["frozen", "waffles", "pizza", "fish sticks"], "reason": "frozen/convenience backup repeat signal"},
    {"tag": "eggs", "score": 5, "needles": ["eggs", "large brown", "cage free"], "reason": "eggs recurring breakfast staple"},
]


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")
    return slug or "household_rule"


def _string_list(value: Any, *, field: str, index: int) -> list[str]:
    if isinstance(value, str):
        values = [value]
    elif isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        values = [str(item).strip() for item in value]
    else:
        raise ValueError(f"household.staples[{index}].{field} must be a string or list of strings")
    values = [item for item in values if item]
    if not values:
        raise ValueError(f"household.staples[{index}].{field} must not be empty")
    return values


def normalize_household_rules(raw_rules: Any) -> list[dict[str, Any]]:
    """Validate and normalize config-driven household staple rules.

    TOML rules are expected under ``[[household.staples]]`` and may use either
    the legacy scorer shape (``tag``/``needles``) or the shareable config shape
    (``name``/``keywords`` plus ``tag`` or ``tags``).
    """
    if raw_rules is None:
        return []
    if not isinstance(raw_rules, list):
        raise ValueError("household.staples must be a list of rule tables")

    normalized: list[dict[str, Any]] = []
    for index, raw in enumerate(raw_rules):
        if not isinstance(raw, Mapping):
            raise ValueError(f"household.staples[{index}] must be a table")
        name = str(raw.get("name") or raw.get("tag") or "").strip()
        keywords_value = raw.get("keywords", raw.get("needles"))
        if keywords_value is None:
            raise ValueError(f"household.staples[{index}] requires keywords (or legacy needles)")
        keywords = _string_list(keywords_value, field="keywords", index=index)
        try:
            score = int(raw.get("score"))
        except (TypeError, ValueError):
            raise ValueError(f"household.staples[{index}].score must be an integer") from None
        if score <= 0:
            raise ValueError(f"household.staples[{index}].score must be positive")

        tags_value = raw.get("tags", raw.get("tag"))
        if tags_value is None:
            if not name:
                raise ValueError(f"household.staples[{index}] requires name, tag, or tags")
            tags = [_slug(name)]
        else:
            tags = [_slug(tag) for tag in _string_list(tags_value, field="tags", index=index)]
        reason = str(raw.get("reason") or (f"{name} household staple" if name else f"{tags[0]} household staple"))
        normalized.append({"name": name or tags[0], "keywords": keywords, "needles": keywords, "score": score, "tags": tags, "tag": tags[0], "reason": reason})
    return normalized


def category_words(product: Mapping[str, Any]) -> str:
    bits: list[str] = []
    bits.append(str(product.get("name") or ""))
    bits.append(str(product.get("description") or ""))
    cats = product.get("categories") or []
    if isinstance(cats, list):
        bits.extend(str(cat or "") for cat in cats)
    item_categories = product.get("item_categories") or {}
    if isinstance(item_categories, dict):
        for entry in item_categories.values():
            if isinstance(entry, dict):
                bits.append(str(entry.get("category_name") or ""))
    return " ".join(bits).lower()


def score_household_match(product: Mapping[str, Any], rules: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    haystack = category_words(product)
    score = 0
    tags: list[str] = []
    reasons: list[str] = []
    for rule in rules or DEFAULT_HOUSEHOLD_RULES:
        needles = rule.get("keywords", rule.get("needles", []))
        if any(str(needle).lower() in haystack for needle in needles):
            score += int(rule["score"])
            rule_tags = rule.get("tags") or [rule.get("tag")]
            tags.extend(str(tag) for tag in rule_tags if tag)
            reasons.append(str(rule.get("reason") or rule.get("name") or rule_tags[0]))
    return {"household_score": score, "household_reasons": reasons, "household_tags": tags}
