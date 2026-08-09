import json
import re
import subprocess
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PublicBaselineTests(unittest.TestCase):
    def test_core_does_not_ship_unvetted_live_recipe_integrations(self):
        self.assertFalse((ROOT / "src" / "grocery_agent_kit" / "recipe_api.py").exists())

    def test_safeway_adapter_normalizes_sanitized_fixture(self):
        spec = spec_from_file_location("safeway_adapter", ROOT / "scripts" / "extract_safeway_weekly_ad.py")
        if spec is None or spec.loader is None:
            self.fail("could not load Safeway adapter")
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        products = json.loads((ROOT / "tests" / "fixtures" / "safeway_flipp_minimal.json").read_text())
        artifact = module.build_artifact(products, store_id="example", postal_code="POSTAL_CODE_REQUIRED", products_url="https://example.test/products?access_token=unit-test-secret&locale=en", min_products=1, min_pages=1)
        self.assertEqual(artifact["product_count"], len(products))
        self.assertIn("coverage", artifact)
        self.assertNotIn("unit-test-secret", artifact["products_url"])
        self.assertNotIn("access_token", artifact["products_url"])
        self.assertTrue(module._trusted_products_url("https://dam.flippenterprise.net/flyerkit/publication/123/products?access_token=runtime-only"))
        self.assertFalse(module._trusted_products_url("file:///tmp/products.json"))
        self.assertFalse(module._trusted_products_url("https://dam.flippenterprise.net.evil/flyerkit/publication/123/products"))

    def test_no_private_markers_in_tracked_source(self):
        forbidden_patterns = (
            r"\b(?:xox[baprs]-|gh[opusr]_|sk-[A-Za-z0-9])[A-Za-z0-9_-]{8,}\b",
            r"\b(?:192\.168|10\.|172\.(?:1[6-9]|2\d|3[0-1]))\.\d{1,3}\.\d{1,3}\b",
            r"\bC[0-9][A-Z0-9]{7,}\b",
        )
        tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode("utf-8").split("\0")
        for relative in filter(None, tracked):
            path = ROOT / relative
            if path.suffix in {".pyc", ".whl"}:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for pattern in forbidden_patterns:
                self.assertIsNone(re.search(pattern, text), f"sensitive marker matching {pattern!r} in {relative}")


if __name__ == "__main__":
    unittest.main()
