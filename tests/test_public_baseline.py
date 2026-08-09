import json
import subprocess
import sys
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
        forbidden = (
            "Mor" + "teza",
            "Berna" + "dette",
            "ghaz" + "itehrani",
            "C0B6" + "PPP62KT",
            "192.168.0." + "229",
            "River" + "mark",
        )
        tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode("utf-8").split("\0")
        for relative in filter(None, tracked):
            path = ROOT / relative
            if path.suffix in {".pyc", ".whl"}:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for marker in forbidden:
                self.assertNotIn(marker, text, f"{marker} in {relative}")


if __name__ == "__main__":
    unittest.main()
