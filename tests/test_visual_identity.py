import unittest
from pathlib import Path

from flask import Flask, render_template, session


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
        cls.app.secret_key = "visual-identity-test"

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

    def test_display_has_waiting_live_and_full_screen_podium_regions(self):
        source = (TEMPLATES_DIR / "display.html").read_text(encoding="utf-8")

        for element_id in (
            "displayWaitingPanel",
            "displayWaitingRoomCode",
            "displayConnectedCount",
            "displayWaitingTeams",
            "displayCompetitionPanel",
            "displayRanking",
            "displayWordQueue",
            "displayConnectionStatus",
            "displayPodiumPanel",
            "displayPodiumControls",
        ):
            self.assertIn(f'id="{element_id}"', source)

        ranking_position = source.index('id="displayRanking"')
        queue_position = source.index('id="displayWordQueue"')
        self.assertLess(ranking_position, queue_position)

    def test_display_question_visibility_is_local_default_on_and_display_only(self):
        display_template = (TEMPLATES_DIR / "display.html").read_text(
            encoding="utf-8"
        )
        participant_template = (
            TEMPLATES_DIR / "participant" / "room.html"
        ).read_text(encoding="utf-8")
        display_script = (STATIC_DIR / "js" / "display.js").read_text(
            encoding="utf-8"
        )
        css_source = (STATIC_DIR / "css" / "app.css").read_text(encoding="utf-8")

        self.assertIn('id="displayHideQuestion"', display_template)
        self.assertIn("Ocultar pregunta al público", display_template)
        self.assertIn('type="checkbox" checked', display_template)
        self.assertNotIn("displayHideQuestion", participant_template)
        self.assertIn(
            'const DISPLAY_HIDE_QUESTION_KEY = "mateolimpiadas-display-hide-question"',
            display_script,
        )
        self.assertIn("window.sessionStorage", display_script)
        self.assertIn("storedValue === null ? true", display_script)
        self.assertIn('classList.toggle("question-hidden"', display_script)
        self.assertIn("questionPanel.hidden = displayQuestionHidden", display_script)
        self.assertNotIn("visual-test", display_script)
        self.assertIn(".display-live.question-hidden .display-main", css_source)
        self.assertIn(".display-live.question-hidden .display-side-panel", css_source)
        self.assertIn('"ranking summary"', css_source)
        self.assertIn('"ranking queue"', css_source)

    def test_display_podium_controls_follow_the_authenticated_judge_session(self):
        with self.app.test_request_context("/display"):
            public_display = render_template("display.html")
            self.assertIn('data-can-control-podium="false"', public_display)

            session["judge_authenticated"] = True
            judge_display = render_template("display.html")
            self.assertIn('data-can-control-podium="true"', judge_display)

        display_script = (STATIC_DIR / "js" / "display.js").read_text(
            encoding="utf-8"
        )
        self.assertIn("const displayCanControlPodium", display_script)
        self.assertIn("final && displayCanControlPodium", display_script)
        self.assertIn("!displayCanControlPodium", display_script)

    def test_display_projector_layout_keeps_two_columns_until_phone_width(self):
        css_source = (STATIC_DIR / "css" / "app.css").read_text(encoding="utf-8")

        self.assertIn("height: 100vh;", css_source)
        self.assertIn("body.display-page:has(#displayLivePanel:not(.d-none))", css_source)
        self.assertIn("grid-template-columns: minmax(0, 55fr) minmax(0, 45fr);", css_source)
        self.assertIn("grid-template-columns: minmax(0, 47fr) minmax(0, 53fr);", css_source)
        self.assertIn("grid-template-columns: minmax(0, 46fr) minmax(0, 54fr);", css_source)
        self.assertIn("grid-template-columns: minmax(0, 50fr) minmax(0, 50fr);", css_source)
        self.assertIn("(max-aspect-ratio: 4/3)", css_source)
        self.assertIn("(max-aspect-ratio: 5/4)", css_source)
        self.assertIn("(max-aspect-ratio: 1/1)", css_source)
        phone_media = css_source.split("@media (max-width: 680px)", 1)[1]
        self.assertIn("grid-template-columns: 1fr;", phone_media)
        self.assertIn(".display-main.no-question-image", phone_media)
        self.assertIn("object-fit: contain;", css_source)
        self.assertIn("overflow: hidden;", css_source)
        self.assertNotIn("max-height: 4.3em;", css_source)
        self.assertNotIn("-webkit-line-clamp: 4;", css_source)
        self.assertNotIn("-webkit-line-clamp: 5;", css_source)
        self.assertNotIn("-webkit-line-clamp: 3;", css_source)
        self.assertIn(".display-question-panel.is-long h2", css_source)
        self.assertIn(".display-question-panel.is-very-long h2", css_source)
        self.assertIn(".display-main.no-question-image", css_source)
        self.assertIn(".display-status-compact", css_source)
        self.assertIn(".display-timer-copy", css_source)
        self.assertIn(".display-word-queue:has(.queue-active):has(.queue-waiting)", css_source)
        self.assertIn(".queue-next.is-next", css_source)
        self.assertIn("body.display-page:has(#displayLivePanel:not(.d-none)) .theme-toggle", css_source)
        self.assertIn(".display-podium .podium-stage::after", css_source)
        self.assertIn("align-self: end;", css_source)
        self.assertIn("grid-row: 1;", css_source)
        self.assertIn("padding-bottom: 0;", css_source)
        self.assertIn("animation-iteration-count: infinite;", css_source)
        reduced_motion = css_source.split("@media (prefers-reduced-motion: reduce)", 1)[1]
        self.assertIn(".podium-celebrating .css-confetti", reduced_motion)
        self.assertIn("display: none !important;", reduced_motion)

        display_script = (STATIC_DIR / "js" / "display.js").read_text(
            encoding="utf-8"
        )
        self.assertIn("const DISPLAY_QUEUE_LIMIT = 2;", display_script)
        self.assertIn("equipos en espera", display_script)
        self.assertIn("SIGUIENTE:", display_script)
        self.assertIn("EN ESPERA:", display_script)
        self.assertIn("Aún no hay solicitudes de palabra.", display_script)
        self.assertIn('displaySocket.on("connect"', display_script)
        self.assertIn('displaySocket.emit("display_unirse"', display_script)
        self.assertIn('classList.remove("is-long", "is-very-long")', display_script)
        self.assertIn('classList.remove("has-question-image", "no-question-image")', display_script)
        self.assertIn("teamMembersListHtml(participant.integrantes)", display_script)

    def test_authorized_display_podium_uses_server_event_for_click_and_keyboard(self):
        source = (STATIC_DIR / "js" / "display.js").read_text(encoding="utf-8")

        self.assertIn('displayPodiumStage.addEventListener("click"', source)
        self.assertIn('displayPodiumStage.addEventListener("keydown"', source)
        self.assertIn('["Enter", " "].includes(event.key)', source)
        self.assertIn("event.preventDefault();", source)
        self.assertIn("displayPodiumCanAdvance()", source)
        self.assertIn("displayCanControlPodium", source)
        self.assertIn('displaySocket.emit("cambiar_estado_podio"', source)
        self.assertIn('view.setAttribute("tabindex", "0")', source)
        self.assertIn('view.classList.toggle("podium-interactive", canAdvance)', source)

    def test_participant_has_no_podium_controls_or_control_event(self):
        template_source = (TEMPLATES_DIR / "participant" / "room.html").read_text(
            encoding="utf-8"
        )
        script_source = (STATIC_DIR / "js" / "participant_room.js").read_text(
            encoding="utf-8"
        )

        self.assertNotIn("podium-controls", template_source)
        self.assertNotIn("cambiar_estado_podio", template_source)
        self.assertNotIn('socket.emit("cambiar_estado_podio"', script_source)
        self.assertIn('socket.on("estado_podio"', script_source)

    def test_participant_podium_mode_uses_full_height_without_gaining_controls(self):
        template_source = (TEMPLATES_DIR / "participant" / "room.html").read_text(
            encoding="utf-8"
        )
        script_source = (STATIC_DIR / "js" / "participant_room.js").read_text(
            encoding="utf-8"
        )
        common_source = (STATIC_DIR / "js" / "live_common.js").read_text(
            encoding="utf-8"
        )
        css_source = (STATIC_DIR / "css" / "app.css").read_text(encoding="utf-8")

        self.assertIn('id="participantTimerStack"', template_source)
        self.assertIn("final-actions-buttons", template_source)
        self.assertIn('classList.add("podium-mode")', script_source)
        self.assertIn('participantTimerStack.setAttribute("aria-hidden", "true")', script_source)
        self.assertIn(
            'rankingEl.querySelector(".final-podium-view")?.classList.remove(',
            script_source,
        )
        self.assertNotIn('socket.emit("cambiar_estado_podio"', script_source)
        self.assertIn("teamMembersListHtml(item.integrantes)", common_source)
        self.assertIn("podiumConfettiMarkup()", common_source)
        self.assertIn(
            "body.participant-page:has(.participant-view.podium-mode)",
            css_source,
        )
        self.assertIn(
            ".participant-view.podium-mode .timer-stack",
            css_source,
        )
        self.assertIn(
            "body.participant-page:has(.participant-view.podium-mode) .app-footer",
            css_source,
        )
        self.assertIn(
            ".participant-view.podium-mode .final-actions",
            css_source,
        )
        self.assertIn(
            ".participant-view.podium-mode .team-members-list li",
            css_source,
        )
        self.assertIn(
            ".participant-view.podium-mode .podium-stage::after",
            css_source,
        )
        self.assertIn("calc(100vh + 140px)", css_source)
        self.assertNotIn("participantVisualTest", script_source)


if __name__ == "__main__":
    unittest.main()
