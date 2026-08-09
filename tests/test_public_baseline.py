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

    def test_legacy_repository_brand_is_absent_from_reachable_history(self):
        legacy_name = "grocery" + "-agent-kit"
        history = subprocess.check_output(
            ["git", "log", "--all", "--format=%H", "-S", legacy_name],
            cwd=ROOT,
            text=True,
        ).strip()
        self.assertEqual(history, "", "legacy repository brand remains reachable in Git history")

    def test_catalog_metadata_and_license_are_branded(self):
        metadata = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
        self.assertIn('name = "ai-skills-grocery-planner"', metadata)
        self.assertIn('grocery-planner = "grocery_agent_kit.__main__:main"', metadata)
        self.assertTrue(license_text.startswith("MIT License\n\nCopyright (c) 2026 Mortezagt\n"))

    def test_removed_recipe_module_is_absent_from_reachable_history(self):
        history = subprocess.check_output(
            ["git", "log", "--all", "--format=%H", "--", "src/grocery_agent_kit/recipe_api.py"],
            cwd=ROOT,
            text=True,
        ).strip()
        self.assertEqual(history, "", "removed household-policy module remains reachable in Git history")

    def test_email_domains_are_sanitized(self):
        allowed_domains = {"example.com", "example-grocery.com", "sample.test"}
        email_pattern = re.compile(r"\b[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+\.[A-Za-z]{2,})\b")
        tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode("utf-8").split("\0")
        for relative in filter(None, tracked):
            text = (ROOT / relative).read_text(encoding="utf-8", errors="ignore")
            for domain in email_pattern.findall(text):
                self.assertIn(domain.lower(), allowed_domains, f"non-sanitized email domain in {relative}")

    def test_ai_skills_catalog_scaffold_is_present(self):
        self.assertTrue((ROOT / "AGENTS.md").is_file())
        for directory in ("skills", "rules", "prompts", "templates", "examples"):
            self.assertTrue((ROOT / directory / "README.md").is_file(), directory)
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("# AI Skills", readme)
        self.assertIn("BEGIN GROCERY-PLANNER-EXAMPLE", readme)
        self.assertIn("offline, sanitized fixture output", readme)

    def test_portable_skill_is_self_contained(self):
        skill_dir = ROOT / "skills" / "grocery-planner"
        skill = skill_dir / "SKILL.md"
        self.assertTrue(skill.is_file())
        self.assertTrue((skill_dir / "references" / "LLM_SETUP.md").is_file())
        self.assertTrue((skill_dir / "templates" / "grocery.example.toml").is_file())
        content = skill.read_text(encoding="utf-8")
        self.assertTrue(content.startswith("---\nname: grocery-planner\n"))
        self.assertIn("references/LLM_SETUP.md", content)
        self.assertIn("templates/grocery.example.toml", content)
        self.assertNotIn("/home/", content)

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
            r"-----BEGIN (?:[A-Z0-9 ]+ )?PRIVATE KEY-----",
            r"\b(?:xox[baprs]-|gh[opusr]_|github_pat_|sk-[A-Za-z0-9]|AKIA|ASIA)[A-Za-z0-9_-]{8,}\b",
            r"\b(?:192\.168|10\.|172\.(?:1[6-9]|2\d|3[0-1]))\.\d{1,3}\.\d{1,3}\b",
            r"\b\d{5}(?:-\d{4})?\b",
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
