"""Local CLI for validated, review-only grocery planning artifacts."""
from __future__ import annotations

import argparse
import json
import os
from datetime import date as date_type
from pathlib import Path
import tempfile
from typing import Sequence

from .config import GroceryConfig, load_config
from .render_html import md_to_html
from .weekly_plan import PlanValidationError, build_weekly_plan, render_plan_markdown


def _config_readiness_errors(cfg: GroceryConfig) -> list[str]:
    errors: list[str] = []
    if cfg.store.store_id in {"", "YOUR_STORE_ID"}:
        errors.append("store.store_id must be set in a private config")
    if cfg.store.postal_code in {"", "POSTAL_CODE_REQUIRED"}:
        errors.append("store.postal_code must be set in a private config")
    if cfg.store.name == "Your Grocery Store":
        errors.append("store.name must be set in a private config")
    if cfg.store.address == "Your store address":
        errors.append("store.address must be set in a private config")
    if cfg.delivery.email_to == ["family@example.com"]:
        errors.append("delivery.email_to must be set or removed in a private config")
    if "your-forwarding-address@example.com" in cfg.receipts.gmail_query:
        errors.append("receipts.gmail_query must be set or removed in a private config")
    return errors


def _load_private_config(path: str) -> GroceryConfig | None:
    try:
        return load_config(path)
    except (OSError, ValueError) as exc:
        print(f"error: cannot load config: {exc}")
        return None


def _validate_config(args: argparse.Namespace) -> int:
    cfg = _load_private_config(args.config)
    if cfg is None:
        return 2
    errors = _config_readiness_errors(cfg)
    if errors:
        for error in errors:
            print(f"not ready: {error}")
        return 2
    print(f"ok: config ready for {cfg.store.name}")
    return 0


def _write_private(path: Path, text: str) -> None:
    """Atomically replace one private review artifact with owner-only permissions."""
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False) as handle:
        temporary = Path(handle.name)
        try:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
            os.chmod(temporary, 0o600)
            os.replace(temporary, path)
            os.chmod(path, 0o600)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise


def _plan(args: argparse.Namespace) -> int:
    cfg = _load_private_config(args.config)
    if cfg is None:
        return 2
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
        markdown = render_plan_markdown(plan)
        html = md_to_html(markdown)
        serialized = json.dumps(plan, indent=2, sort_keys=True) + "\n"
    except (PlanValidationError, ValueError) as exc:
        print(f"error: {exc}")
        return 2

    output_dir = Path(args.out_dir)
    try:
        output_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(output_dir, 0o700)
        stamp = plan["date"]
        markdown_path = output_dir / f"weekly_plan_{stamp}.md"
        html_path = output_dir / f"weekly_plan_{stamp}.html"
        json_path = output_dir / f"weekly_plan_{stamp}.json"
        _write_private(markdown_path, markdown)
        _write_private(html_path, html)
        _write_private(json_path, serialized)
    except OSError as exc:
        print(f"error: cannot write private plan artifacts: {exc}")
        return 2
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
    plan.add_argument("--out-dir", required=True, help="Directory to receive private Markdown, HTML, and JSON artifacts.")
    plan.add_argument("--date", default="", help="Optional YYYY-MM-DD output date for deterministic runs.")
    plan.set_defaults(func=_plan)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
