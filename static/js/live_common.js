function escapeHtml(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function parseTeamMembers(value) {
    const source = String(value ?? "").trim();

    if (!source) {
        return [];
    }

    const parts = /[\r\n]/.test(source)
        ? source.split(/\r\n|\n|\r/)
        : source.includes(";")
            ? source.split(";")
            : [source];

    return parts.map(member => member.trim()).filter(Boolean);
}

function teamMembersInlineText(value) {
    return parseTeamMembers(value).join(" • ");
}

function teamMembersListHtml(value) {
    const members = parseTeamMembers(value);

    if (!members.length) {
        return "";
    }

    const fullLabel = members.join(", ");
    return `
        <ul class="team-members-list" title="${escapeHtml(fullLabel)}" aria-label="Integrantes: ${escapeHtml(fullLabel)}">
            ${members.map(member => `<li>${escapeHtml(member)}</li>`).join("")}
        </ul>
    `;
}

function apiFetch(url, options = {}) {
    const finalOptions = {
        headers: {"Content-Type": "application/json"},
        ...options
    };
    return fetch(url, finalOptions).then(response => response.json());
}

const liveSoundPaths = {
    start: "/static/audio/start.mp3",
    request: "/static/audio/request.mp3",
    turn: "/static/audio/turn.mp3",
    correct: "/static/audio/correct.mp3",
    incorrect: "/static/audio/incorrect.mp3",
    countdown: "/static/audio/countdown.mp3",
    finish: "/static/audio/finish.mp3",
    celebrate: "/static/audio/celebrate.mp3",
    tick: "/static/audio/tick.mp3",
    timeup: "/static/audio/timeup.mp3"
};
const liveAudioCache = {};
const liveTimerSoundState = {};
const liveActiveTickKeys = new Set();
const liveSoundsAvailable = Boolean(document.querySelector(
    "#judgeCompetitionPanel, .participant-view, .display-screen"
));
const stopTickBeforeSound = new Set([
    "start",
    "question",
    "turn",
    "correct",
    "incorrect",
    "countdown",
    "finish",
    "timeup"
]);
let liveSoundsEnabled = false;

function enableLiveSounds() {
    if (liveSoundsEnabled) {
        return;
    }

    liveSoundsEnabled = true;
    Object.entries(liveSoundPaths).forEach(([key, path]) => {
        const audio = new Audio(path);
        audio.preload = "auto";
        audio.volume = 0.38;
        liveAudioCache[key] = audio;
    });
}

function stopSound(name) {
    const audio = liveAudioCache[name];

    if (!audio) {
        return;
    }

    audio.pause();
    audio.currentTime = 0;
}

function stopTickSound() {
    liveActiveTickKeys.clear();
    const audio = liveAudioCache.tick;

    if (!audio) {
        return;
    }

    audio.pause();
    audio.currentTime = 0;
    audio.loop = false;
}

if (liveSoundsAvailable) {
    ["pointerdown", "keydown", "touchstart"].forEach(eventName => {
        window.addEventListener(eventName, enableLiveSounds, {once: true, passive: true});
    });
}

function playSound(name, options = {}) {
    if (!liveSoundsEnabled || !liveSoundPaths[name]) {
        return;
    }

    if (stopTickBeforeSound.has(name)) {
        stopTickSound();
    }

    const audio = liveAudioCache[name] || new Audio(liveSoundPaths[name]);
    audio.volume = options.volume ?? audio.volume ?? 0.38;
    audio.playbackRate = options.rate || 1;
    audio.loop = options.loop || false;
    audio.currentTime = 0;
    audio.play().catch(() => {});
}

function startTickSound(key = "default") {
    if (!liveSoundsEnabled || !liveSoundPaths.tick) {
        return;
    }

    const audio = liveAudioCache.tick || new Audio(liveSoundPaths.tick);
    liveAudioCache.tick = audio;
    audio.volume = 0.38;
    audio.playbackRate = 1;
    audio.loop = true;
    liveActiveTickKeys.add(key);

    if (!audio.paused && !audio.ended) {
        return;
    }

    audio.currentTime = 0;
    audio.play().catch(() => {});
}

function stopTimerTickSound(key = "default") {
    liveActiveTickKeys.delete(key);

    if (liveActiveTickKeys.size === 0) {
        stopTickSound();
    }
}

function formJson(form) {
    const data = {};
    new FormData(form).forEach((value, key) => {
        if (value instanceof File) {
            return;
        }

        if (data[key]) {
            data[key] = Array.isArray(data[key]) ? data[key] : [data[key]];
            data[key].push(value);
        } else {
            data[key] = value;
        }
    });
    return data;
}

function normalizedTimerValue(timer) {
    const remaining = Number(timer?.remaining);
    return Number.isFinite(remaining) ? remaining : null;
}

const LIVE_SITE_IDENTITIES = Object.freeze({
    petapa: Object.freeze({accent: "#d4a900", tint: "#fff5bf", detail: "#705700"}),
    "villa nueva": Object.freeze({accent: "#23834b", tint: "#e5f7ec", detail: "#14532d"}),
    "san cristobal": Object.freeze({accent: "#c83e48", tint: "#ffe8ea", detail: "#7f1d2d"}),
    antigua: Object.freeze({accent: "#7c3fb4", tint: "#f4e8ff", detail: "#581c87"}),
    naranjo: Object.freeze({accent: "#e87920", tint: "#ffead7", detail: "#9a3412"}),
    "aguilar batres": Object.freeze({accent: "#2d9fc5", tint: "#e1f6fd", detail: "#075985"}),
    "san juan": Object.freeze({accent: "#3b82f6", tint: "#e5edf8", detail: "#173f73"}),
    amatitlan: Object.freeze({accent: "#f0d9ad", tint: "#fff7e7", detail: "#8b2635"})
});
const DEFAULT_LIVE_SITE_IDENTITY = Object.freeze({
    accent: "#2563eb",
    tint: "#eef4ff",
    detail: "#1e3a5f"
});
const PODIUM_STATE_ORDER = Object.freeze([
    "OCULTO",
    "TERCER_LUGAR",
    "SEGUNDO_LUGAR",
    "PRIMER_LUGAR",
    "COMPLETO"
]);

function normalizedSiteName(site) {
    return String(site || "")
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .trim()
        .toLowerCase();
}

function teamSiteIdentity(site) {
    const normalized = normalizedSiteName(site);
    return {
        key: normalized.replaceAll(" ", "-") || "default",
        ...(LIVE_SITE_IDENTITIES[normalized] || DEFAULT_LIVE_SITE_IDENTITY)
    };
}

function rankingScoreWidth(score, leaderScore) {
    const numericScore = Number(score || 0);
    const numericLeader = Number(leaderScore || 0);

    if (numericLeader <= 0 || numericScore <= 0) {
        return 0;
    }

    return Math.max(0, Math.min(100, (numericScore / numericLeader) * 100));
}

function rankingRowKey(item, index = 0) {
    return String(
        item?.participant_code
        || item?.codigo_participante
        || item?.id_participante
        || item?.sede
        || item?.nombre
        || index
    );
}

function prefersReducedMotion() {
    return Boolean(
        window.matchMedia
        && window.matchMedia("(prefers-reduced-motion: reduce)").matches
    );
}

function rankingHasEntries(rankingData) {
    return Array.isArray(rankingData?.ranking) && rankingData.ranking.length > 0;
}

function podiumCelebrationActive(state, reducedMotion = prefersReducedMotion()) {
    return !reducedMotion && ["PRIMER_LUGAR", "COMPLETO"].includes(state);
}

function podiumConfettiMarkup(count = 36, random = Math.random) {
    const colors = [
        "#fbbf24",
        "#22c55e",
        "#38bdf8",
        "#ef4444",
        "#a855f7",
        "#f97316"
    ];

    return Array.from({length: count}, () => {
        const x = (2 + random() * 96).toFixed(2);
        const delay = (-random() * 7).toFixed(2);
        const duration = (4.8 + random() * 3.6).toFixed(2);
        const drift = Math.round(-180 + random() * 360);
        const rotation = Math.round(420 + random() * 960);
        const size = Math.round(6 + random() * 7);
        const color = colors[Math.floor(random() * colors.length) % colors.length];
        const radius = random() > 0.5 ? "50%" : "2px";
        return (
            `<span style="--x:${x}%;--delay:${delay}s;--duration:${duration}s;`
            + `--drift:${drift}px;--rotation:${rotation}deg;--size:${size}px;`
            + `--confetti-color:${color};--confetti-radius:${radius}"></span>`
        );
    }).join("");
}

function renderRanking(target, rankingData) {
    const ranking = Array.isArray(rankingData?.ranking) ? rankingData.ranking : [];
    const leaderScore = Math.max(0, ...ranking.map(item => Number(item.puntaje || 0)));
    const medals = ["🥇", "🥈", "🥉"];
    target.dataset.rankingSize = String(ranking.length);
    target.classList.toggle("ranking-is-dense", ranking.length >= 5);

    if (!rankingHasEntries(rankingData)) {
        target.innerHTML = "<div class='text-secondary ranking-empty'>Sin puntajes registrados.</div>";
        return;
    }

    target.querySelector(".ranking-empty")?.remove();

    const previousRows = new Map(
        [...target.querySelectorAll("[data-ranking-key]")].map(row => [
            row.dataset.rankingKey,
            {row, top: row.getBoundingClientRect().top}
        ])
    );
    const activeKeys = new Set();

    ranking.forEach((item, index) => {
        const key = rankingRowKey(item, index);
        const existing = previousRows.get(key);
        const row = existing?.row || document.createElement("div");
        const identity = teamSiteIdentity(item.sede);
        const score = Number(item.puntaje || 0);
        const scoreWidth = rankingScoreWidth(score, leaderScore);
        const members = teamMembersInlineText(item.integrantes);
        activeKeys.add(key);
        row.className = "ranking-row podium-row";
        row.dataset.rankingKey = key;
        row.dataset.siteIdentity = identity.key;
        row.style.setProperty("--score-width", `${scoreWidth}%`);
        row.style.setProperty("--site-accent", identity.accent);
        row.style.setProperty("--site-tint", identity.tint);
        row.style.setProperty("--site-detail", identity.detail);

        if (!existing) {
            row.innerHTML = `
                <div class="ranking-row-head">
                    <div class="ranking-team-copy">
                        <strong class="ranking-site"></strong>
                        <small class="ranking-name"></small>
                        <small class="ranking-members"></small>
                    </div>
                    <span class="ranking-score"></span>
                </div>
                <div class="ranking-bar"><span></span></div>
            `;
        }

        row.querySelector(".ranking-site").textContent = (
            `${medals[index] || `${index + 1}.`} ${item.sede || item.nombre || "Equipo"}`
        );
        row.querySelector(".ranking-name").textContent = item.nombre || "";
        row.querySelector(".ranking-members").textContent = members;
        row.querySelector(".ranking-members").classList.toggle("d-none", !members);
        if (members) {
            row.querySelector(".ranking-members").title = members;
            row.querySelector(".ranking-members").setAttribute(
                "aria-label",
                `Integrantes: ${members}`
            );
        } else {
            row.querySelector(".ranking-members").removeAttribute("title");
            row.querySelector(".ranking-members").removeAttribute("aria-label");
        }
        row.querySelector(".ranking-score").textContent = `${score} pts`;
        row.querySelector(".ranking-bar").setAttribute(
            "aria-label",
            `Progreso relativo: ${Math.round(scoreWidth)} %`
        );
        target.appendChild(row);

        if (existing && !prefersReducedMotion() && typeof row.animate === "function") {
            const delta = existing.top - row.getBoundingClientRect().top;

            if (Math.abs(delta) > 1) {
                row.animate(
                    [
                        {transform: `translateY(${delta}px)`},
                        {transform: "translateY(0)"}
                    ],
                    {duration: 420, easing: "cubic-bezier(0.2, 0.8, 0.2, 1)"}
                );
            }
        } else if (!existing) {
            row.classList.add("ranking-row-entering");
        }
    });

    previousRows.forEach(({row}, key) => {
        if (!activeKeys.has(key)) {
            row.remove();
        }
    });
}

function nextPodiumState(currentState, direction = 1) {
    const currentIndex = Math.max(0, PODIUM_STATE_ORDER.indexOf(currentState));
    const nextIndex = Math.max(
        0,
        Math.min(PODIUM_STATE_ORDER.length - 1, currentIndex + direction)
    );
    return PODIUM_STATE_ORDER[nextIndex];
}

function renderSynchronizedPodium(
        target,
        rankingData,
        podiumState = {estado: "OCULTO", revision: 0},
        options = {}
) {
    const ranking = (rankingData?.ranking || []).slice(0, 3);
    const medals = ["&#129351;", "&#129352;", "&#129353;"];
    const signature = ranking.map((item, index) => (
        [
            rankingRowKey(item, index),
            item.sede || "",
            item.nombre || "",
            item.integrantes || "",
            Number(item.puntaje || 0)
        ].join(":")
    )).join("|");
    let view = target.querySelector(".final-podium-view");

    if (!view || view.dataset.rankingSignature !== signature) {
        const podiumItems = ranking.map((item, index) => ({
            ...item,
            place: index + 1,
            medal: medals[index],
            identity: teamSiteIdentity(item.sede)
        }));
        const confetti = podiumConfettiMarkup();

        target.innerHTML = `
            <div class="final-podium-view" data-ranking-signature="${escapeHtml(signature)}" aria-live="polite">
                <div class="css-confetti" aria-hidden="true">${confetti}</div>
                <div class="podium-intro">
                    <span>Resultados finales</span>
                    <strong>El podio está listo</strong>
                </div>
                <div class="podium-stage">
                    ${podiumItems.map(item => `
                        <div class="podium-place podium-place-${item.place}" data-place="${item.place}" data-site-identity="${item.identity.key}" style="--site-accent:${item.identity.accent};--site-detail:${item.identity.detail}">
                            <div class="podium-medal">${item.medal}</div>
                            <strong>${escapeHtml(item.sede || item.nombre || "Equipo")}</strong>
                            <small>${escapeHtml(item.nombre || "")}</small>
                            ${teamMembersListHtml(item.integrantes)}
                            <span>${Number(item.puntaje || 0)} pts</span>
                            <div class="podium-block"></div>
                        </div>
                    `).join("")}
                </div>
            </div>
        `;
        view = target.querySelector(".final-podium-view");
    }

    const state = PODIUM_STATE_ORDER.includes(podiumState?.estado)
        ? podiumState.estado
        : "OCULTO";
    const revealThrough = {
        OCULTO: 0,
        TERCER_LUGAR: 3,
        SEGUNDO_LUGAR: 2,
        PRIMER_LUGAR: 1,
        COMPLETO: 1
    }[state];
    view.dataset.podiumState = state;
    view.dataset.podiumRevision = String(podiumState?.revision || 0);
    view.classList.toggle("podium-started", state !== "OCULTO");
    view.classList.toggle(
        "podium-instant",
        state === "COMPLETO" || options.animate === false || prefersReducedMotion()
    );
    const celebrationActive = podiumCelebrationActive(state);
    view.classList.toggle("podium-celebrating", celebrationActive);
    view.querySelectorAll("[data-place]").forEach(place => {
        place.classList.toggle(
            "podium-revealed",
            revealThrough > 0 && Number(place.dataset.place) >= revealThrough
        );
    });

    if (options.celebrate && celebrationActive) {
        playSound("celebrate", {volume: 0.5});
    }
}

function renderAnimatedPodium(target, rankingData) {
    renderSynchronizedPodium(
        target,
        rankingData,
        {estado: "OCULTO", revision: 0},
        {animate: false}
    );
}

function renderTimer(target, timer, progressTarget = null) {
    const remaining = normalizedTimerValue(timer);
    target.textContent = remaining ?? "--";

    if (!progressTarget) {
        return;
    }

    const explicitDuration = Number(
        timer?.duration
        || timer?.total
        || timer?.tiempo_por_pregunta
        || 0
    );
    const currentTotal = Number(progressTarget.dataset.timerTotal || 0);
    let total = explicitDuration || currentTotal;

    if (remaining !== null && (!total || remaining > total || timer?.resetProgress)) {
        total = remaining;
    }

    progressTarget.dataset.timerTotal = String(total || 0);
    const percent = total ? Math.max(0, Math.min(100, (remaining / total) * 100)) : 0;
    progressTarget.style.width = `${percent}%`;
    progressTarget.classList.toggle("timer-progress-warning", remaining !== null && remaining <= 10 && remaining > 0);
    progressTarget.classList.toggle("timer-progress-ended", remaining === 0);
}

function handleTimerSound(timer, key = "default") {
    const remaining = normalizedTimerValue(timer);
    const timerActive = Boolean(timer?.active_since) && !timer?.exhausted && remaining > 0;
    const stateSignature = `${remaining ?? "none"}:${timerActive ? "active" : "inactive"}:${timer?.exhausted ? "ended" : "open"}`;

    if (remaining === null) {
        stopTimerTickSound(key);
        delete liveTimerSoundState[key];
        return;
    }

    if (liveTimerSoundState[key] === stateSignature) {
        return;
    }

    liveTimerSoundState[key] = stateSignature;

    if (timerActive) {
        startTickSound(key);
    } else if (remaining === 0 || timer?.exhausted) {
        stopTimerTickSound(key);
        playSound("timeup");
    } else {
        stopTimerTickSound(key);
    }
}

function resetTimerSound(key = "default") {
    stopTimerTickSound(key);
    delete liveTimerSoundState[key];
}
