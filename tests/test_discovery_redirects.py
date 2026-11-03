import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from urllib.parse import urljoin, urlsplit

import yaml


ROOT = Path(__file__).resolve().parents[1]


class DiscoveryRedirectsTest(unittest.TestCase):
    def test_all_discovery_redirects_resolve_to_the_documented_pages(self):
        config = yaml.safe_load((ROOT / "mkdocs.yml").read_text())
        redirects = next(p["redirects"]["redirect_maps"] for p in config["plugins"] if isinstance(p, dict) and "redirects" in p)
        with tempfile.TemporaryDirectory() as directory:
            site = Path(directory)
            subprocess.run(["mkdocs", "build", "--strict", "--site-dir", str(site)], cwd=ROOT, check=True, capture_output=True)
            for source, target in redirects.items():
                with self.subTest(source=source):
                    page = site / source.removesuffix(".md") / "index.html"
                    html = page.read_text()
                    href = re.search(r'<link rel="canonical" href="([^"]+)"', html).group(1)
                    actual = urlsplit(urljoin("/" + str(page.parent.relative_to(site)) + "/", href)).path.lstrip("/")
                    expected = target.removesuffix(".md").removeprefix("en/") + "/"
                    self.assertEqual(actual, expected)
                    self.assertTrue((site / actual / "index.html").is_file())
                    prefix = "https://example.org/docs/integrations/latest/"
                    self.assertEqual(urljoin(prefix + source.removesuffix(".md") + "/", href), prefix + expected)


if __name__ == "__main__":
    unittest.main()
