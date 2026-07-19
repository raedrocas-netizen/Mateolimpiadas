import hashlib
import re
import unittest
from pathlib import Path

from flask import Flask, render_template


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TEMPLATES_DIR = PROJECT_ROOT / "templates"
STATIC_DIR = PROJECT_ROOT / "static"

VENDOR_ASSETS = {
    "vendor/bootstrap/css/bootstrap.min.css": (
        "3c8f27e6009ccfd710a905e6dcf12d0ee3c6f2ac7da05b0572d3e0d12e736fc8",
        b"Bootstrap  v5.3.3",
    ),
    "vendor/bootstrap/js/bootstrap.bundle.min.js": (
        "0833b2e9c3a26c258476c46266e6877fc75218625162e0460be9a3a098a61c6c",
        b"Bootstrap v5.3.3",
    ),
    "vendor/socket.io/socket.io.min.js": (
        "73eba16bc895fdfa454e27ecb80def31ede8d861f99e175ff93b110eabec044f",
        b"Socket.IO v4.7.5",
    ),
}

EXTERNAL_RUNTIME_REFERENCE = re.compile(
    r"(?:https?:)?//(?:cdn\.|[^/]*(?:jsdelivr|unpkg|cdnjs|googleapis|gstatic))",
    re.IGNORECASE,
)


class FrontendVendorAssetsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = Flask(
            __name__,
            template_folder=str(TEMPLATES_DIR),
            static_folder=str(STATIC_DIR),
            static_url_path="/static",
        )

    def test_authored_frontend_has_no_external_runtime_dependencies(self):
        source_locations = (TEMPLATES_DIR, STATIC_DIR / "js", STATIC_DIR / "css")

        for source_location in source_locations:
            for path in source_location.rglob("*"):
                if not path.is_file():
                    continue
                source = path.read_text(encoding="utf-8")
                self.assertIsNone(
                    EXTERNAL_RUNTIME_REFERENCE.search(source),
                    f"Referencia externa de runtime en {path.relative_to(PROJECT_ROOT)}",
                )

    def test_base_template_renders_local_vendor_urls(self):
        with self.app.test_request_context("/"):
            rendered = render_template("base.html")

        for relative_path in VENDOR_ASSETS:
            self.assertIn(f'/static/{relative_path}', rendered)
        self.assertNotRegex(rendered, r'(?:href|src)=["\'](?:https?:)?//')

    def test_vendor_assets_match_pinned_versions_and_hashes(self):
        for relative_path, (expected_hash, version_marker) in VENDOR_ASSETS.items():
            content = (STATIC_DIR / relative_path).read_bytes()
            self.assertEqual(hashlib.sha256(content).hexdigest(), expected_hash)
            self.assertIn(version_marker, content[:512])

    def test_flask_serves_vendor_assets_locally(self):
        client = self.app.test_client()

        for relative_path in VENDOR_ASSETS:
            with client.get(f"/static/{relative_path}") as response:
                self.assertEqual(response.status_code, 200, relative_path)

    def test_all_jinja_templates_parse(self):
        for path in TEMPLATES_DIR.rglob("*.html"):
            source = path.read_text(encoding="utf-8")
            try:
                self.app.jinja_env.parse(source)
            except Exception as exc:
                self.fail(f"No se pudo parsear {path.relative_to(PROJECT_ROOT)}: {exc}")


if __name__ == "__main__":
    unittest.main()
