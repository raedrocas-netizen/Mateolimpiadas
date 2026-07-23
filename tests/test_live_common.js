const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const assert = require("node:assert/strict");
const vm = require("node:vm");

const source = fs.readFileSync(
    path.join(__dirname, "..", "static", "js", "live_common.js"),
    "utf8"
);

function registeredSoundListeners(hasLiveView) {
    const listeners = [];
    const context = {
        Audio: class {},
        FormData: class {},
        document: {
            querySelector() {
                return hasLiveView ? {} : null;
            }
        },
        window: {
            addEventListener(eventName) {
                listeners.push(eventName);
            }
        }
    };

    vm.runInNewContext(source, context);
    return listeners;
}

function liveCommonContext() {
    const context = {
        Audio: class {},
        FormData: class {},
        document: {
            querySelector() {
                return null;
            }
        },
        window: {
            addEventListener() {},
            matchMedia() {
                return {matches: false};
            }
        }
    };
    vm.runInNewContext(source, context);
    return context;
}

test("does not preload competition audio from non-live pages", () => {
    assert.deepEqual(registeredSoundListeners(false), []);
});

test("keeps audio activation on live competition views", () => {
    assert.deepEqual(
        registeredSoundListeners(true),
        ["pointerdown", "keydown", "touchstart"]
    );
});

test("calculates ranking bars without artificial minimums", () => {
    const context = liveCommonContext();

    assert.equal(context.rankingScoreWidth(100, 100), 100);
    assert.equal(context.rankingScoreWidth(50, 100), 50);
    assert.equal(context.rankingScoreWidth(0, 100), 0);
    assert.equal(context.rankingScoreWidth(-20, 100), 0);
    assert.equal(context.rankingScoreWidth(0, 0), 0);
    const tiedWidthA = context.rankingScoreWidth(40, 80);
    const tiedWidthB = context.rankingScoreWidth(40, 80);
    assert.equal(tiedWidthA, 50);
    assert.equal(tiedWidthA, tiedWidthB);
});

test("provides the approved identity for all eight sites", () => {
    const context = liveCommonContext();
    const sites = [
        "Petapa",
        "Villa Nueva",
        "San Cristóbal",
        "Antigua",
        "Naranjo",
        "Aguilar Batres",
        "San Juan",
        "Amatitlán"
    ];

    sites.forEach(site => {
        const identity = context.teamSiteIdentity(site);
        assert.notEqual(identity.key, "default", site);
        assert.match(identity.accent, /^#[0-9a-f]{6}$/i, site);
        assert.match(identity.detail, /^#[0-9a-f]{6}$/i, site);
    });
    assert.equal(context.teamSiteIdentity("San Juan").accent, "#3b82f6");
    assert.equal(context.teamSiteIdentity("Amatitlán").detail, "#8b2635");
});

test("parses team members without breaking compound names", () => {
    const context = liveCommonContext();

    assert.deepEqual(
        [...context.parseTeamMembers("Ana López\nLuis Pérez\nMaría del Carmen")],
        ["Ana López", "Luis Pérez", "María del Carmen"]
    );
    assert.deepEqual(
        [...context.parseTeamMembers("Matthew Carranza\r\nAlejandro Rousselin\r\nBrandon Figueroa\r\nKevin Dávila")],
        ["Matthew Carranza", "Alejandro Rousselin", "Brandon Figueroa", "Kevin Dávila"]
    );
    assert.deepEqual(
        [...context.parseTeamMembers("Ana María\r\rJosé de León\r")],
        ["Ana María", "José de León"]
    );
    assert.deepEqual(
        [...context.parseTeamMembers("  Ana López  \n\n Luis Pérez \n")],
        ["Ana López", "Luis Pérez"]
    );
    assert.deepEqual(
        [...context.parseTeamMembers("María de los Ángeles López")],
        ["María de los Ángeles López"]
    );
    assert.deepEqual(
        [...context.parseTeamMembers("Ana López, Luis Pérez")],
        ["Ana López, Luis Pérez"]
    );
    assert.deepEqual(
        [...context.parseTeamMembers("Ana López; Luis Pérez")],
        ["Ana López", "Luis Pérez"]
    );
});

test("escapes each member and provides compact separated text", () => {
    const context = liveCommonContext();
    const html = context.teamMembersListHtml("<Ana>\nLuis & José\nMaría del Carmen");

    assert.match(html, /<li>&lt;Ana&gt;<\/li>/);
    assert.match(html, /<li>Luis &amp; José<\/li>/);
    assert.doesNotMatch(html, /<li><Ana><\/li>/);
    assert.equal(
        context.teamMembersInlineText("Ana López\nLuis Pérez\nMaría del Carmen"),
        "Ana López • Luis Pérez • María del Carmen"
    );
    assert.match(source, /teamMembersInlineText\(item\.integrantes\)/);
    assert.match(source, /teamMembersListHtml\(item\.integrantes\)/);
});

test("treats zero-score teams as ranking entries", () => {
    const context = liveCommonContext();

    assert.equal(context.rankingHasEntries({ranking: []}), false);
    assert.equal(context.rankingHasEntries({ranking: [{sede: "Petapa", puntaje: 0}]}), true);
    assert.equal(context.rankingHasEntries({ranking: [{sede: "Petapa", puntaje: -10}]}), true);
    assert.match(source, /querySelector\("\.ranking-empty"\)\?\.remove\(\)/);
});

test("keeps the official podium sequence on server-driven controls", () => {
    const context = liveCommonContext();

    assert.equal(context.nextPodiumState("OCULTO", 1), "TERCER_LUGAR");
    assert.equal(context.nextPodiumState("TERCER_LUGAR", 1), "SEGUNDO_LUGAR");
    assert.equal(context.nextPodiumState("SEGUNDO_LUGAR", 1), "PRIMER_LUGAR");
    assert.equal(context.nextPodiumState("PRIMER_LUGAR", 1), "COMPLETO");
    assert.equal(context.nextPodiumState("COMPLETO", 1), "COMPLETO");
    assert.equal(context.nextPodiumState("OCULTO", -1), "OCULTO");
});

test("keeps celebration active only for first place and complete podium", () => {
    const context = liveCommonContext();

    assert.equal(context.podiumCelebrationActive("SEGUNDO_LUGAR", false), false);
    assert.equal(context.podiumCelebrationActive("PRIMER_LUGAR", false), true);
    assert.equal(context.podiumCelebrationActive("COMPLETO", false), true);
    assert.equal(context.podiumCelebrationActive("PRIMER_LUGAR", true), false);
    assert.match(source, /classList\.toggle\("podium-celebrating", celebrationActive\)/);
});

test("builds varied confetti pieces with randomized motion variables", () => {
    const context = liveCommonContext();
    const values = [
        0.01, 0.12, 0.23, 0.34, 0.45, 0.56, 0.67, 0.78,
        0.89, 0.91, 0.15, 0.26, 0.37, 0.48, 0.59, 0.7
    ];
    let index = 0;
    const markup = context.podiumConfettiMarkup(
        2,
        () => values[index++ % values.length]
    );

    assert.equal((markup.match(/<span /g) || []).length, 2);
    assert.match(markup, /--x:\d+\.\d+%/);
    assert.match(markup, /--delay:-\d+\.\d+s/);
    assert.match(markup, /--duration:\d+\.\d+s/);
    assert.match(markup, /--drift:-?\d+px/);
    assert.match(markup, /--rotation:\d+deg/);
    assert.match(markup, /--confetti-color:#[0-9a-f]{6}/i);
    const pieces = markup.match(/<span style="[^"]+"><\/span>/g);
    assert.equal(pieces.length, 2);
    assert.notEqual(pieces[0], pieces[1]);
    assert.match(source, /const confetti = podiumConfettiMarkup\(\)/);
});

test("removes local click and keyboard advancement from the podium", () => {
    assert.doesNotMatch(source, /advancePodium/);
    assert.doesNotMatch(source, /aria-label="Avanzar premiacion"/);
    assert.match(source, /function renderSynchronizedPodium/);
});
