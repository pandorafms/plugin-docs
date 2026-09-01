import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_docs.py"
SPEC = importlib.util.spec_from_file_location("validate_docs", SCRIPT)
validator = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = validator
SPEC.loader.exec_module(validator)


class DocsFixture:
    def __init__(self, root: Path):
        self.docs = root / "docs"
        (self.docs / "en").mkdir(parents=True)
        (self.docs / "es").mkdir(parents=True)

    def write(self, language: str, relative: str, content: str) -> Path:
        path = self.docs / language / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def pair(self, relative: str, en: str = "# English\n", es: str = "# Español\n") -> None:
        self.write("en", relative, en)
        self.write("es", relative, es)


class ValidatorTestCase(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.fixture = DocsFixture(Path(self.temporary.name))

    def issues(self, code: str):
        return [issue for issue in validator.validate(self.fixture.docs) if issue.code == code]

    def run_cli(self, *arguments: str):
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--docs-dir", str(self.fixture.docs), *arguments],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_parity_valid_and_missing(self):
        self.fixture.pair("index.md")
        self.assertEqual([], self.issues("PARITY"))

        self.fixture.write("en", "only-en.md", "# English only\n")
        issues = self.issues("PARITY")
        self.assertEqual(1, len(issues))
        self.assertEqual("BLOCKING", issues[0].severity)
        self.assertIn("missing es counterpart", issues[0].message)

    def test_h1_zero_one_two_and_fenced_h1(self):
        self.fixture.pair("zero.md", "No title\n", "Sin título\n")
        self.fixture.pair("one.md")
        self.fixture.pair("two.md", "# One\n# Two\n", "# Uno\n# Dos\n")
        self.fixture.pair("fenced.md", "# Real\n```md\n# Example\n```\n", "# Real\n~~~md\n# Ejemplo\n~~~\n")

        by_name = {}
        for issue in self.issues("H1"):
            by_name.setdefault(Path(issue.path).name, []).append(issue)
        self.assertEqual(2, len(by_name["zero.md"]))
        self.assertEqual(2, len(by_name["two.md"]))
        self.assertNotIn("one.md", by_name)
        self.assertNotIn("fenced.md", by_name)

    def test_images_valid_broken_and_spanish_fallback(self):
        self.fixture.pair(
            "guide.md",
            "# English\n![ok](assets/ok.png)\n![bad](assets/missing.png)\n",
            "# Español\n![fallback](assets/ok.png)\n",
        )
        image = self.fixture.docs / "en" / "assets" / "ok.png"
        image.parent.mkdir(parents=True)
        image.write_bytes(b"image")

        issues = self.issues("IMAGE")
        self.assertEqual(1, len(issues))
        self.assertIn("assets/missing.png", issues[0].message)

    def test_local_link_anchor_and_cross_language_reports(self):
        self.fixture.pair("target.md", "# Target\n## Existing anchor\n", "# Destino\n## Ancla existente\n")
        self.fixture.pair(
            "source.md",
            "# Source\n[valid](target.md#existing-anchor)\n[bad target](absent.md)\n[bad anchor](target.md#absent)\n[Spanish](../es/target.md)\n",
            "# Fuente\n",
        )
        issues = validator.validate(self.fixture.docs)
        self.assertEqual(1, sum(issue.code == "LOCAL_LINK" for issue in issues))
        self.assertEqual(1, sum(issue.code == "ANCHOR" for issue in issues))
        self.assertEqual(1, sum(issue.code == "CROSS_LANGUAGE" for issue in issues))

    def test_brand_only_in_rendered_prose(self):
        self.fixture.pair(
            "brand.md",
            "# Brand\nPandoraFMS is rendered.\n`PandoraFMS`\nhttps://example.test/PandoraFMS\nPandoraFMS/config\n```\nPandoraFMS\n```\n",
            "# Marca\n",
        )
        issues = self.issues("BRAND")
        self.assertEqual(1, len(issues))
        self.assertEqual(2, issues[0].line)

    def test_marker_in_comment_but_not_prose_or_inline_code(self):
        self.fixture.pair(
            "markers.md",
            "# Markers\n<!-- SCREENSHOT NEEDED: add dashboard -->\n`TODO` is a documented marker.\nTodo el contenido está listo.\n```\nTODO: example\n```\n",
            "# Marcadores\n",
        )
        issues = self.issues("MARKER")
        self.assertEqual(1, len(issues))
        self.assertIn("SCREENSHOT NEEDED", issues[0].message)

    def test_structured_secrets_and_safe_placeholders(self):
        self.fixture.pair(
            "secrets.md",
            "# Secrets\nAKIAIOSFODNN7EXAMPLE\npassword=12345 mypassword <API_TOKEN> 123e4567-e89b-12d3-a456-426614174000\n",
            "# Secretos\n",
        )
        issues = self.issues("SECRET")
        self.assertEqual(1, len(issues))
        self.assertIn("AWS access key", issues[0].message)

    def test_known_contamination_signatures(self):
        self.fixture.pair("integrations/teams.md", "# Teams\nSlack connector CLI\n", "# Teams\nSlack connector CLI\n")
        self.fixture.pair(
            "integrations/google-chat.md",
            "# Chat\nhttps://developers.google.com/hangouts/chat/how-tos/webhooks\n",
            "# Chat\n",
        )
        self.fixture.pair(
            "integrations/telegram.md",
            "# Telegram\n[manual](https://pandorafms.com/manual/es/documentation/topic)\n",
            "# Telegram\n",
        )
        self.fixture.pair(
            "discovery/apache-discovery.md",
            "# Apache\nhttp://192.0.2.1/server\n",
            "# Apache\n",
        )
        issues = self.issues("CONTAMINATION")
        self.assertEqual(5, len(issues))

    def test_fail_on_modes_and_exit_codes(self):
        self.fixture.pair("report.md", "# English\nPandoraFMS prose\n", "# Español\n")
        self.assertEqual(0, self.run_cli().returncode)
        self.assertEqual(1, self.run_cli("--fail-on", "all").returncode)
        self.assertEqual(0, self.run_cli("--fail-on", "none").returncode)

        self.fixture.write("en", "blocking.md", "No H1\n")
        self.fixture.write("es", "blocking.md", "Sin H1\n")
        self.assertEqual(1, self.run_cli().returncode)
        self.assertEqual(0, self.run_cli("--fail-on", "none").returncode)

        missing = subprocess.run(
            [sys.executable, str(SCRIPT), "--docs-dir", str(self.fixture.docs / "absent")],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(2, missing.returncode)
        self.assertTrue(missing.stderr.startswith("ERROR docs directory"))

    def test_json_output_is_stable(self):
        issue = validator.Issue("REPORT", "BRAND", "docs/en/a.md", 2, "message")
        expected = """{
  "issues": [
    {
      "code": "BRAND",
      "line": 2,
      "message": "message",
      "path": "docs/en/a.md",
      "severity": "REPORT"
    }
  ],
  "summary": {
    "blocking": 0,
    "report": 1,
    "total": 1
  }
}"""
        self.assertEqual(expected, validator.format_json([issue]))

        self.fixture.pair("index.md")
        result = self.run_cli("--format", "json")
        self.assertEqual(0, result.returncode)
        self.assertEqual({"issues": [], "summary": {"blocking": 0, "report": 0, "total": 0}}, json.loads(result.stdout))


if __name__ == "__main__":
    unittest.main()
