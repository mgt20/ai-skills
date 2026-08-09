"""Local CLI for review-only grocery planning artifacts."""
from __future__ import annotations

import argparse
import json
from datetime import date as date_type
from pathlib import Path
from typing import Sequence

from .config import GroceryConfig, load_config
from .render_html import md_to_html
from .weekly_plan import CoverageError, build_weekly_plan, render_plan_markdown


def _config_readiness_errors(cfg: GroceryConfig) -> list[str]:
    errors: list[str] = []
    if cfg.store.store_id in {"", "YOUR_STORE_ID"}:
        errors.append("store.store_id must be set in a private config")
    if cfg.store.postal_code in {"", "POSTAL_CODE_REQUIRED"}:
        errors.append("store.postal_code must be set in a private config")
    if cfg.store.name == "Your Grocery Store":
        errors.append("store.name must be set in a private config")
    return errors


def _validate_config(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    errors = _config_readiness_errors(cfg)
    if errors:
        for error in errors:
            print(f"not ready: {error}")
        return 2
    print(f"ok: config ready for {cfg.store.name}")
    return 0


def _plan(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    if args.date:
        try:
            date_type.fromisoformat(args.date)
        except ValueError:
            print("error: --date must use YYYY-MM-DD")
            return 2
    ad_path = Path(args.ad_json)
    try:
        ad = json.loads(ad_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"error: cannot read ad artifact {ad_path}: {exc}")
        return 2
    try:
        plan = build_weekly_plan(cfg, ad, date=args.date or None)
    except (CoverageError, ValueError) as exc:
        print(f"error: {exc}")
        return 2

    output_dir = Path(args.out_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = plan["date"]
    markdown_path = output_dir / f"weekly_plan_{stamp}.md"
    html_path = output_dir / f"weekly_plan_{stamp}.html"
    json_path = output_dir / f"weekly_plan_{stamp}.json"
    markdown = render_plan_markdown(plan)
    markdown_path.write_text(markdown, encoding="utf-8")
    html_path.write_text(md_to_html(markdown), encoding="utf-8")
    json_path.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote plan: {markdown_path}")
    print(f"wrote html: {html_path}")
    print(f"wrote json: {json_path}")
    print("safety: review-only; no network, cart, checkout, or delivery action was performed")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="grocery-planner", description="Review-only grocery planning from normalized weekly-ad artifacts.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate = subparsers.add_parser("validate-config", help="Check a private household config is ready for a real store.")
    validate.add_argument("--config", required=True, help="Path to private TOML config.")
    validate.set_defaults(func=_validate_config)
    plan = subparsers.add_parser("plan", help="Render review-only plan artifacts from a normalized weekly-ad JSON artifact.")
    plan.add_argument("--config", required=True, help="Path to TOML config (example config is allowed for demos).")
    plan.add_argument("--ad-json", required=True, help="Normalized weekly-ad artifact JSON from a store provider.")
    plan.add_argument("--out-dir", required=True, help="Directory to receive Markdown, HTML, and JSON artifacts.")
    plan.add_argument("--date", default="", help="Optional YYYY-MM-DD output date for deterministic runs.")
    plan.set_defaults(func=_plan)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
