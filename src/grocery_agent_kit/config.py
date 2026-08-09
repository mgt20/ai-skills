from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any
import os
import re
import tomllib

from .household import normalize_household_rules

ROOT = Path(__file__).resolve().parents[2]

# Current, store-specific sale lines are generated from an ad-provider artifact.
# The public kit deliberately has no historical price or retailer fallback data.
DEFAULT_SALE_LINES: dict[str, str] = {}

DEFAULT_WEEKLY_POEM = ""
DEFAULT_FRIDAY_POEM = ""

@dataclass
class StoreConfig:
    name: str = 'Your Grocery Store'
    store_id: str = 'YOUR_STORE_ID'
    postal_code: str = 'POSTAL_CODE_REQUIRED'
    address: str = 'Your store address'

@dataclass
class DeliveryConfig:
    email_to: list[str] = field(default_factory=lambda: ['family@example.com'])
    email_subject: str = "This week's grocery plan"
    slack_title: str = "🛒 This week’s grocery plan"

@dataclass
class PersonalizationConfig:
    weekly_poem: str = DEFAULT_WEEKLY_POEM
    friday_poem: str = DEFAULT_FRIDAY_POEM
    poem_enabled: bool = False

@dataclass
class PathsConfig:
    root: Path = ROOT
    ad_extract: str = 'weekly_ad/latest_extract.json'
    weekly_latest_md: str = 'weekly_shopping_list_latest.md'
    weekly_latest_html: str = 'weekly_shopping_list_latest.html'
    weekly_slack_root: str = 'weekly_shopping_list_slack_root_latest.txt'

@dataclass
class ReceiptConfig:
    gmail_query: str = 'from:your-forwarding-address@example.com subject:Your grocery receipt'


class TemplateMode(str, Enum):
    WEEKLY_FULL = 'weekly_full'
    FRIDAY_REMINDER = 'friday_reminder'
    SHORT_PREVIEW = 'short_preview'
    FRIEND_DEMO = 'friend_demo'


def validate_template_mode(value: str | TemplateMode) -> TemplateMode:
    if isinstance(value, TemplateMode):
        return value
    try:
        return TemplateMode(str(value))
    except ValueError:
        allowed = ', '.join(mode.value for mode in TemplateMode)
        raise ValueError(f"Invalid template/output mode {value!r}; expected one of: {allowed}") from None


@dataclass
class RenderConfig:
    output_mode: TemplateMode = TemplateMode.WEEKLY_FULL
    template_mode: TemplateMode = TemplateMode.WEEKLY_FULL


@dataclass
class HouseholdConfig:
    staples: list[dict[str, Any]] | None = None


@dataclass
class GroceryConfig:
    store: StoreConfig = field(default_factory=StoreConfig)
    delivery: DeliveryConfig = field(default_factory=DeliveryConfig)
    personalization: PersonalizationConfig = field(default_factory=PersonalizationConfig)
    paths: PathsConfig = field(default_factory=PathsConfig)
    receipts: ReceiptConfig = field(default_factory=ReceiptConfig)
    render: RenderConfig = field(default_factory=RenderConfig)
    household: HouseholdConfig = field(default_factory=HouseholdConfig)
    sale_lines: dict[str, str] = field(default_factory=lambda: dict(DEFAULT_SALE_LINES))


def _merge_table(cfg: GroceryConfig, data: dict[str, Any]) -> GroceryConfig:
    if 'store' in data:
        for k, v in data['store'].items():
            if hasattr(cfg.store, k):
                setattr(cfg.store, k, str(v))
    if 'delivery' in data:
        d = data['delivery']
        if 'email_to' in d:
            cfg.delivery.email_to = [str(x) for x in d['email_to']]
        if 'email_subject' in d:
            cfg.delivery.email_subject = str(d['email_subject'])
        if 'slack_title' in d:
            cfg.delivery.slack_title = str(d['slack_title'])
    if 'personalization' in data:
        p = data['personalization']
        if 'weekly_poem' in p:
            cfg.personalization.weekly_poem = str(p['weekly_poem'])
        if 'friday_poem' in p:
            cfg.personalization.friday_poem = str(p['friday_poem'])
        if 'poem_enabled' in p:
            cfg.personalization.poem_enabled = bool(p['poem_enabled'])
    if 'paths' in data:
        p = data['paths']
        if 'root' in p:
            cfg.paths.root = Path(str(p['root'])).expanduser()
        for k in ('ad_extract', 'weekly_latest_md', 'weekly_latest_html', 'weekly_slack_root'):
            if k in p:
                setattr(cfg.paths, k, str(p[k]))
    if 'receipts' in data:
        r = data['receipts']
        if 'gmail_query' in r:
            cfg.receipts.gmail_query = str(r['gmail_query'])
    if 'render' in data:
        r = data['render']
        if 'output_mode' in r:
            cfg.render.output_mode = validate_template_mode(str(r['output_mode']))
        if 'template_mode' in r:
            cfg.render.template_mode = validate_template_mode(str(r['template_mode']))
    if 'household' in data:
        h = data['household']
        if 'staples' in h:
            cfg.household.staples = normalize_household_rules(h['staples'])
    if 'sale_lines' in data:
        cfg.sale_lines.update({str(k): str(v) for k, v in data['sale_lines'].items()})
    return cfg


def load_config(path: str | os.PathLike[str] | None = None) -> GroceryConfig:
    cfg = GroceryConfig()
    candidates: list[Path] = []
    if path:
        candidates.append(Path(path).expanduser())
    elif os.environ.get('GROCERY_CONFIG'):
        candidates.append(Path(os.environ['GROCERY_CONFIG']).expanduser())
    else:
        candidates.append(ROOT / 'config/grocery.local.toml')
    for candidate in candidates:
        if candidate.exists():
            cfg = _merge_table(cfg, tomllib.loads(candidate.read_text(encoding='utf-8')))
            break
    cfg.paths.root = cfg.paths.root.resolve()
    if not cfg.store.store_id or not cfg.store.postal_code:
        raise ValueError('Grocery config requires store.store_id and store.postal_code')
    return cfg


def shareable_config_has_private_data(text: str) -> bool:
    needles = [
        'mor' + 'teza',
        'berna' + 'dette',
        'C0B6' + 'PPP62KT',
        'gt.berna' + 'dette',
        'ghazi' + 'tehrani',
    ]
    return any(n.lower() in text.lower() for n in needles)
