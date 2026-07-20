const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const assert = require("node:assert/strict");
const vm = require("node:vm");

const themeSource = fs.readFileSync(
    path.join(__dirname, "..", "static", "js", "theme.js"),
    "utf8"
);

function executeTheme({storedTheme = null, systemDark = false, darkLogo = null} = {}) {
    const rootAttributes = new Map();
    const toggleAttributes = new Map();
    const storedValues = new Map();
    const listeners = {};
    let systemListener = null;

    if (storedTheme !== null) {
        storedValues.set("mateolimpiadas-theme", storedTheme);
    }

    const root = {
        classList: {
            add(value) {
                root.themeReadyClass = value;
            }
        },
        getAttribute(name) {
            return rootAttributes.get(name) || null;
        },
        setAttribute(name, value) {
            rootAttributes.set(name, value);
        }
    };

    const toggle = {
        addEventListener(name, callback) {
            listeners[name] = callback;
        },
        setAttribute(name, value) {
            toggleAttributes.set(name, value);
        }
    };

    const logoAttributes = new Map();
    const logoSourceHistory = [];
    const logo = {
        dataset: {
            logoLight: "/static/img/logo-light.png",
            logoVariant: "pending",
            ...(darkLogo ? {logoDark: darkLogo} : {})
        },
        getAttribute(name) {
            return logoAttributes.get(name) || null;
        },
        setAttribute(name, value) {
            logoAttributes.set(name, value);
            if (name === "src") {
                logoSourceHistory.push(value);
            }
        }
    };

    const mediaQuery = {
        matches: systemDark,
        addEventListener(name, callback) {
            if (name === "change") {
                systemListener = callback;
            }
        }
    };

    const localStorage = {
        getItem(key) {
            return storedValues.has(key) ? storedValues.get(key) : null;
        },
        setItem(key, value) {
            storedValues.set(key, value);
        }
    };

    const document = {
        documentElement: root,
        readyState: "complete",
        getElementById(id) {
            return id === "themeToggle" ? toggle : null;
        },
        querySelectorAll(selector) {
            return selector === "img[data-logo-light]" ? [logo] : [];
        }
    };

    const window = {
        matchMedia() {
            return mediaQuery;
        },
        requestAnimationFrame(callback) {
            callback();
        }
    };

    vm.runInNewContext(themeSource, {document, localStorage, window});

    return {
        rootAttributes,
        toggleAttributes,
        storedValues,
        listeners,
        root,
        logo,
        logoAttributes,
        logoSourceHistory,
        emitSystemChange(matches) {
            systemListener({matches});
        }
    };
}

test("uses prefers-color-scheme when no choice was stored", () => {
    const environment = executeTheme({systemDark: true});

    assert.equal(environment.rootAttributes.get("data-theme"), "dark");
    assert.equal(environment.rootAttributes.get("data-bs-theme"), "dark");
    assert.equal(environment.toggleAttributes.get("aria-label"), "Activar modo claro");
    assert.equal(environment.root.themeReadyClass, "theme-ready");
});

test("stored choice overrides the system preference", () => {
    const environment = executeTheme({
        storedTheme: "light",
        systemDark: true,
        darkLogo: "/static/img/logo-dark.png"
    });

    assert.equal(environment.rootAttributes.get("data-theme"), "light");
    assert.equal(environment.toggleAttributes.get("aria-pressed"), "false");
    assert.deepEqual(environment.logoSourceHistory, ["/static/img/logo-light.png"]);
});

test("reload with a stored dark choice selects only the dark logo", () => {
    const environment = executeTheme({
        storedTheme: "dark",
        systemDark: false,
        darkLogo: "/static/img/logo-dark.png"
    });

    assert.equal(environment.rootAttributes.get("data-theme"), "dark");
    assert.equal(environment.logo.dataset.logoVariant, "dark");
    assert.deepEqual(environment.logoSourceHistory, ["/static/img/logo-dark.png"]);
});

test("toggle persists the explicit choice", () => {
    const environment = executeTheme({systemDark: false});

    environment.listeners.click();

    assert.equal(environment.rootAttributes.get("data-theme"), "dark");
    assert.equal(environment.storedValues.get("mateolimpiadas-theme"), "dark");
    assert.equal(environment.toggleAttributes.get("aria-pressed"), "true");
});

test("system changes are followed until the user chooses a theme", () => {
    const environment = executeTheme({systemDark: false});

    environment.emitSystemChange(true);
    assert.equal(environment.rootAttributes.get("data-theme"), "dark");

    environment.listeners.click();
    environment.emitSystemChange(true);
    assert.equal(environment.rootAttributes.get("data-theme"), "light");
});

test("uses a configured dark logo and restores the light source", () => {
    const environment = executeTheme({
        systemDark: true,
        darkLogo: "/static/img/logo-dark.png"
    });

    assert.equal(environment.logoAttributes.get("src"), "/static/img/logo-dark.png");
    assert.equal(environment.logo.dataset.logoVariant, "dark");
    assert.deepEqual(environment.logoSourceHistory, ["/static/img/logo-dark.png"]);

    environment.listeners.click();

    assert.equal(environment.logoAttributes.get("src"), "/static/img/logo-light.png");
    assert.equal(environment.logo.dataset.logoVariant, "light");
    assert.deepEqual(environment.logoSourceHistory, [
        "/static/img/logo-dark.png",
        "/static/img/logo-light.png"
    ]);
});

test("keeps the light logo as a clean fallback when no dark asset exists", () => {
    const environment = executeTheme({systemDark: true});

    assert.equal(environment.logoAttributes.get("src"), "/static/img/logo-light.png");
    assert.equal(environment.logo.dataset.logoVariant, "light");
    assert.deepEqual(environment.logoSourceHistory, ["/static/img/logo-light.png"]);
});
