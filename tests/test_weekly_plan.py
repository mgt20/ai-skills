from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from grocery_agent_kit.config import load_config
from grocery_agent_kit.__main__ import main
from grocery_agent_kit.weekly_plan import CoverageError, build_weekly_plan, render_plan_markdown


class WeeklyPlanTests(unittest.TestCase):
    def setUp(self) -> None:
        self.cfg = load_config(ROOT / "examples" / "basic-local" / "config" / "grocery.example.toml")
        self.ad = {
            "store": {"name": "Example Market", "store_code": "demo", "postal_code": "POSTAL_CODE_REQUIRED"},
            "publication": {"id": "demo-2026-01", "valid_from": "2026-01-01", "valid_to": "2026-01-07"},
            "coverage": {"status": "ok", "product_count": 8, "page_count": 2, "page_range": "1-2"},
            "products": [
                {"name": "Chicken Thighs", "deal_text": "$2.49 lb", "bucket": "proteins", "page": 1, "valid_from": "2026-01-01", "valid_to": "2026-01-07", "household_score": 6},
                {"name": "Frozen Shrimp", "deal_text": "$7.99 ea", "bucket": "proteins", "page": 1, "valid_from": "2026-01-01", "valid_to": "2026-01-07", "household_score": 3},
                {"name": "Salad Kit", "deal_text": "2 for $5.00", "bucket": "produce", "page": 1, "valid_from": "2026-01-01", "valid_to": "2026-01-07", "household_score": 8},
                {"name": "Pasta", "deal_text": "$1.25 ea", "bucket": "pantry", "page": 1, "valid_from": "2026-01-01", "valid_to": "2026-01-07", "household_score": 0},
                {"name": "Milk", "deal_text": "$3.49 ea", "bucket": "dairy/breakfast", "page": 2, "valid_from": "2026-01-01", "valid_to": "2026-01-07", "household_score": 5},
                {"name": "Frozen Pizza", "deal_text": "$4.99 ea", "bucket": "freezer", "page": 2, "valid_from": "2026-01-01", "valid_to": "2026-01-07", "household_score": 1},
                {"name": "Friday Strawberries", "deal_text": "$5.00 ea", "bucket": "produce", "page": 2, "valid_from": "2026-01-02", "valid_to": "2026-01-02", "household_score": 4},
            ],
        }

    def test_builds_harness_neutral_plan_from_verified_ad(self):
        plan = build_weekly_plan(self.cfg, self.ad, date="2026-01-01")
        self.assertEqual(plan["store"]["name"], "Example Market")
        self.assertEqual([item["name"] for item in plan["dinner_anchors"]], ["Chicken Thighs", "Frozen Shrimp"])
        self.assertEqual([item["name"] for item in plan["friday_only"]], ["Friday Strawberries"])
        markdown = render_plan_markdown(plan)
        self.assertIn("Dinner anchors", markdown)
        self.assertIn("No cart was modified", markdown)
        self.assertNotIn("Safeway", markdown)

    def test_rejects_unverified_ad_coverage(self):
        self.ad["coverage"]["status"] = "warning"
        with self.assertRaises(CoverageError):
            build_weekly_plan(self.cfg, self.ad)

    def test_shared_defaults_do_not_embed_a_household(self):
        from grocery_agent_kit.household import DEFAULT_HOUSEHOLD_RULES

        self.assertEqual(DEFAULT_HOUSEHOLD_RULES, [])

    def test_safeway_artifact_is_accepted_through_the_generic_contract(self):
        spec = spec_from_file_location("safeway_adapter", ROOT / "scripts" / "extract_safeway_weekly_ad.py")
        if spec is None or spec.loader is None:
            self.fail("could not load Safeway adapter")
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        raw_products = [
            item for item in json.loads((ROOT / "tests" / "fixtures" / "safeway_flipp_minimal.json").read_text(encoding="utf-8"))
            if item.get("page") in {1, 2}
        ]
        artifact = module.build_artifact(raw_products, store_id="demo", postal_code="POSTAL_CODE_REQUIRED", products_url="https://example.test/publication/1/products", min_products=1, min_pages=1)
        plan = build_weekly_plan(self.cfg, artifact, date="2026-01-01")
        self.assertEqual(plan["coverage"]["status"], "ok")
        self.assertIn("produce", plan["sale_anchors"])

    def test_cli_rejects_invalid_output_date_before_writing(self):
        result = main([
            "plan", "--config", str(ROOT / "examples" / "basic-local" / "config" / "grocery.example.toml"),
            "--ad-json", "does-not-matter.json", "--out-dir", "/tmp/ignored", "--date", "../../escape",
        ])
        self.assertEqual(result, 2)

    def test_config_validation_rejects_all_shipped_placeholders(self):
        example = ROOT / "examples" / "basic-local" / "config" / "grocery.example.toml"
        self.assertEqual(main(["validate-config", "--config", str(example)]), 2)
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "grocery.local.toml"
            config_path.write_text(
                example.read_text(encoding="utf-8")
                .replace("Your Grocery Store", "Example Market")
                .replace("YOUR_STORE_ID", "example-123")
                .replace("POSTAL_CODE_REQUIRED", "POSTAL_CODE_FOR_TESTING")
                .replace("Your store address", "123 Example Street")
                .replace("family@example.com", "family@sample.test")
                .replace("your-forwarding-address@example.com", "receipts@sample.test"),
                encoding="utf-8",
            )
            self.assertEqual(main(["validate-config", "--config", str(config_path)]), 0)

    def test_cli_writes_review_artifacts_without_network_or_cart_side_effects(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            ad_path = temp / "ad.json"
            out_dir = temp / "out"
            ad_path.write_text(json.dumps(self.ad), encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable, "-m", "grocery_agent_kit", "plan",
                    "--config", str(ROOT / "examples" / "basic-local" / "config" / "grocery.example.toml"),
                    "--ad-json", str(ad_path), "--out-dir", str(out_dir), "--date", "2026-01-01",
                ],
                cwd=ROOT,
                env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
                text=True,
                capture_output=True,
                check=True,
            )
            self.assertIn("wrote plan", result.stdout)
            self.assertTrue((out_dir / "weekly_plan_2026-01-01.md").exists())
            self.assertTrue((out_dir / "weekly_plan_2026-01-01.html").exists())
            plan = json.loads((out_dir / "weekly_plan_2026-01-01.json").read_text(encoding="utf-8"))
            self.assertEqual(plan["safety"]["cart_modified"], False)


if __name__ == "__main__":
    unittest.main()
