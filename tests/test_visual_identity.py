import unittest
from pathlib import Path

from flask import Flask, render_template


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TEMPLATES_DIR = PROJECT_ROOT / "templates"
STATIC_DIR = PROJECT_ROOT / "static"

APPROVED_LOGOS = {
    "img/logos/logo_colegio.png",
    "img/logos/logo_olimpiadas_matematica.png",
    "img/logos/logo_petapa.png",
}

APPROVED_DARK_LOGOS = {
    "img/logos/logo_colegio_dark.png",
    "img/logos/logo_olimpiadas_matematica_dark.png",
    "img/logos/logo_petapa_dark.png",
}


class VisualIdentityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = Flask(
            __name__,
            template_folder=str(TEMPLATES_DIR),
            static_folder=str(STATIC_DIR),
            static_url_path="/static",
        )

        routes = {
            "main.index": "/",
            "main.display": "/display",
            "judge.login": "/juez/login",
            "judge.name": "/juez/nombre",
            "judge.dashboard": "/juez/dashboard",
            "judge.logout": "/juez/logout",
            "participant.join": "/participante/",
            "participant.room": "/participante/sala",
        }
        for endpoint, rule in routes.items():
            cls.app.add_url_rule(rule, endpoint, lambda: "")

    def test_approved_brand_assets_are_local_png_files(self):
        for relative_path in APPROVED_LOGOS | APPROVED_DARK_LOGOS:
            path = STATIC_DIR / relative_path
            self.assertTrue(path.is_file(), relative_path)
            self.assertGreater(path.stat().st_size, 0, relative_path)
            self.assertEqual(path.read_bytes()[:8], b"\x89PNG\r\n\x1a\n", relative_path)

    def test_base_uses_local_favicon_and_early_theme_bootstrap(self):
        source = (TEMPLATES_DIR / "base.html").read_text(encoding="utf-8-sig")
        theme_bootstrap_position = source.index("mateolimpiadas-theme")
        stylesheet_position = source.index("vendor/bootstrap/css/bootstrap.min.css")

        self.assertLess(theme_bootstrap_position, stylesheet_position)
        self.assertIn('window.matchMedia("(prefers-color-scheme: dark)")', source)
        self.assertIn("img/logos/logo_olimpiadas_matematica.png", source)
        self.assertIn('rel="icon"', source)
        self.assertIn('id="themeToggle"', source)
        self.assertIn('aria-label="Activar modo oscuro"', source)
        self.assertIn("js/theme.js", source)

    def test_theme_control_persists_and_follows_system_preference(self):
        source = (STATIC_DIR / "js" / "theme.js").read_text(encoding="utf-8")

        self.assertIn('const STORAGE_KEY = "mateolimpiadas-theme"', source)
        self.assertIn("localStorage.getItem(STORAGE_KEY)", source)
        self.assertIn("localStorage.setItem(STORAGE_KEY, resolvedTheme)", source)
        self.assertIn('window.matchMedia("(prefers-color-scheme: dark)")', source)
        self.assertIn('systemTheme.addEventListener("change"', source)
        self.assertIn('root.setAttribute("data-bs-theme", resolvedTheme)', source)

    def test_templates_only_reference_approved_brand_logos(self):
        authored_templates = "\n".join(
            path.read_text(encoding="utf-8-sig")
            for path in TEMPLATES_DIR.rglob("*.html")
        )

        self.assertNotIn("mateolimpiadas_logo.png", authored_templates)
        self.assertNotIn("mateolimpiadas_icon.png", authored_templates)
        for relative_path in APPROVED_LOGOS | APPROVED_DARK_LOGOS:
            self.assertIn(relative_path, authored_templates)

    def test_footer_has_complete_credits_and_lazy_petapa_logo(self):
        footer_source = (TEMPLATES_DIR / "includes" / "footer.html").read_text(
            encoding="utf-8"
        )
        branding_source = (TEMPLATES_DIR / "includes" / "branding.html").read_text(
            encoding="utf-8"
        )

        for name in (
            "Matthew Carranza",
            "Rafael Rosado",
            "Alejandro Rousselin",
            "Brandon Figueroa",
            "Kevin Dávila",
        ):
            self.assertIn(name, footer_source)
        for legal_text in (
            "Proyecto desarrollado por estudiantes de",
            "Sede Petapa",
            "Todos los derechos reservados",
        ):
            self.assertIn(legal_text, footer_source)
        self.assertIn('petapa_logo("footer-logo", "lazy")', footer_source)
        self.assertIn("img/logos/logo_petapa.png", branding_source)

    def test_branding_supports_optional_dark_logos_with_a_clean_fallback(self):
        source = (TEMPLATES_DIR / "includes" / "branding.html").read_text(
            encoding="utf-8"
        )

        self.assertIn("dark_filename=None", source)
        self.assertIn("data-logo-light", source)
        self.assertIn("{% if dark_filename %}data-logo-dark=", source)
        self.assertIn('data-logo-variant="pending"', source)
        self.assertNotIn('src="{{ url_for(\'static\', filename=light_filename)', source)

        for relative_path in APPROVED_DARK_LOGOS:
            self.assertIn(relative_path, source)

    def test_question_images_use_the_shared_frame_media_structure(self):
        template_sources = {
            relative_path: (TEMPLATES_DIR / relative_path).read_text(encoding="utf-8")
            for relative_path in (
                "judge/dashboard.html",
                "judge/questionnaire_questions.html",
                "participant/room.html",
                "display.html",
            )
        }

        for relative_path, source in template_sources.items():
            self.assertIn("image-frame", source, relative_path)
            self.assertIn("image-media", source, relative_path)
            self.assertIn("image-content", source, relative_path)

        css_source = (STATIC_DIR / "css" / "app.css").read_text(encoding="utf-8")
        self.assertIn(".image-frame {", css_source)
        self.assertIn(".image-media {", css_source)
        self.assertIn(".image-content {", css_source)
        self.assertIn("width: fit-content;", css_source)
        self.assertIn("background: transparent;", css_source)
        self.assertNotIn("--image-stage", css_source)

        dark_theme = css_source.split('html[data-theme="dark"] {', 1)[1].split("}", 1)[0]
        self.assertIn("--image-frame-bg:", dark_theme)
        self.assertNotIn("--image-frame-bg: #ffffff", dark_theme)
        self.assertNotIn("--image-frame-bg: #fff", dark_theme)

    def test_dark_site_cards_derive_contrast_from_existing_site_variables(self):
        css_source = (STATIC_DIR / "css" / "app.css").read_text(encoding="utf-8")
        dashboard_source = (STATIC_DIR / "js" / "judge_dashboard.js").read_text(
            encoding="utf-8"
        )
        helpers_source = (STATIC_DIR / "js" / "judge_game_helpers.js").read_text(
            encoding="utf-8"
        )

        for variable in ("--site-accent", "--site-tint", "--site-detail"):
            self.assertIn(variable, dashboard_source)
        self.assertIn("--site-dark-accent: color-mix", css_source)
        self.assertIn("var(--site-accent", css_source)
        self.assertIn('key: "san-juan"', helpers_source)
        self.assertNotIn('[data-site-identity="san-juan"]', css_source)

    def test_primary_views_render_with_shared_visual_shell(self):
        templates = {
            "index.html": {},
            "judge/login.html": {"error": ""},
            "judge/name.html": {},
            "judge/dashboard.html": {"judge_name": "Juez de prueba"},
            "participant/join.html": {},
            "participant/room.html": {},
            "display.html": {},
        }

        with self.app.test_request_context("/"):
            for template_name, context in templates.items():
                rendered = render_template(template_name, **context)
                self.assertIn('id="themeToggle"', rendered, template_name)
                self.assertIn("/static/css/app.css", rendered, template_name)
                self.assertIn("IMB-PC", rendered, template_name)


if __name__ == "__main__":
    unittest.main()
