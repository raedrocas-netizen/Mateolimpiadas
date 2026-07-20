(function () {
    "use strict";

    const STORAGE_KEY = "mateolimpiadas-theme";
    const root = document.documentElement;
    const systemTheme = window.matchMedia("(prefers-color-scheme: dark)");

    function getStoredTheme() {
        try {
            const storedTheme = localStorage.getItem(STORAGE_KEY);
            return storedTheme === "light" || storedTheme === "dark"
                ? storedTheme
                : null;
        } catch (error) {
            return null;
        }
    }

    function getPreferredTheme() {
        return getStoredTheme() || (systemTheme.matches ? "dark" : "light");
    }

    function updateThemeLogos(theme) {
        if (typeof document.querySelectorAll !== "function") {
            return;
        }

        document.querySelectorAll("img[data-logo-light]").forEach(function (logo) {
            const useDarkVariant = theme === "dark" && Boolean(logo.dataset.logoDark);
            const nextSource = useDarkVariant ? logo.dataset.logoDark : logo.dataset.logoLight;

            if (nextSource && logo.getAttribute("src") !== nextSource) {
                logo.setAttribute("src", nextSource);
            }

            logo.dataset.logoVariant = useDarkVariant ? "dark" : "light";
        });
    }

    function updateToggle(theme) {
        const toggle = document.getElementById("themeToggle");
        if (!toggle) {
            return;
        }

        const isDark = theme === "dark";
        const actionLabel = isDark ? "Activar modo claro" : "Activar modo oscuro";
        toggle.setAttribute("aria-label", actionLabel);
        toggle.setAttribute("aria-pressed", String(isDark));
        toggle.setAttribute("title", actionLabel);
    }

    function applyTheme(theme, persist) {
        const resolvedTheme = theme === "dark" ? "dark" : "light";
        root.setAttribute("data-theme", resolvedTheme);
        root.setAttribute("data-bs-theme", resolvedTheme);
        updateThemeLogos(resolvedTheme);

        if (persist) {
            try {
                localStorage.setItem(STORAGE_KEY, resolvedTheme);
            } catch (error) {
                // El tema sigue funcionando aunque el almacenamiento esté bloqueado.
            }
        }

        updateToggle(resolvedTheme);
        return resolvedTheme;
    }

    function initializeThemeControl() {
        const initialTheme = root.getAttribute("data-theme") || getPreferredTheme();
        applyTheme(initialTheme, false);

        const toggle = document.getElementById("themeToggle");
        if (toggle) {
            toggle.addEventListener("click", function () {
                const nextTheme = root.getAttribute("data-theme") === "dark"
                    ? "light"
                    : "dark";
                applyTheme(nextTheme, true);
            });
        }

        const followSystemTheme = function (event) {
            if (!getStoredTheme()) {
                applyTheme(event.matches ? "dark" : "light", false);
            }
        };

        if (typeof systemTheme.addEventListener === "function") {
            systemTheme.addEventListener("change", followSystemTheme);
        } else if (typeof systemTheme.addListener === "function") {
            systemTheme.addListener(followSystemTheme);
        }

        window.requestAnimationFrame(function () {
            root.classList.add("theme-ready");
        });
    }

    window.MateOlimpiadasTheme = {
        STORAGE_KEY,
        applyTheme,
        getPreferredTheme
    };

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initializeThemeControl, {once: true});
    } else {
        initializeThemeControl();
    }
}());
