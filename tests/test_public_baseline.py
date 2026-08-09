import json
import subprocess
import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PublicBaselineTests(unittest.TestCase):
    def test_recipe_provider_defaults_do_not_use_a_private_host_or_dotenv(self):
        sys.path.insert(0, str(ROOT / "src"))
        from grocery_agent_kit import recipe_api
        self.assertEqual(recipe_api.DEFAULT_MEALIE_BASE, "")
        self.assertEqual(recipe_api._read_global_env(), {})

    def test_safeway_adapter_normalizes_sanitized_fixture(self):
        spec = spec_from_file_location("safeway_adapter", ROOT / "scripts" / "extract_safeway_weekly_ad.py")
        if spec is None or spec.loader is None:
            self.fail("could not load Safeway adapter")
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        products = json.loads((ROOT / "tests" / "fixtures" / "safeway_flipp_minimal.json").read_text())
        artifact = module.build_artifact(products, store_id="example", postal_code="POSTAL_CODE_REQUIRED", products_url="https://example.test/products", min_products=1, min_pages=1)
        self.assertEqual(artifact["product_count"], len(products))
        self.assertIn("coverage", artifact)

    def test_no_private_markers_in_tracked_source(self):
        forbidden = (
            "Mor" + "teza",
            "Berna" + "dette",
            "ghaz" + "itehrani",
            "C0B6" + "PPP62KT",
            "192.168.0." + "229",
            "River" + "mark",
        )
        for path in ROOT.rglob("*"):
            if not path.is_file() or ".git" in path.parts or "__pycache__" in path.parts or "build" in path.parts or path.suffix in {".json", ".pyc"}:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for marker in forbidden:
                self.assertNotIn(marker, text, f"{marker} in {path.relative_to(ROOT)}")


if __name__ == "__main__":
    unittest.main()
