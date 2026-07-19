function escapeHtml(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
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

function renderRanking(target, rankingData) {
    const ranking = rankingData?.ranking || [];
    const leaderScore = Math.max(
        0,
        ...ranking.map(item => Number(item.puntaje || 0))
    );
    const medals = ["&#129351;", "&#129352;", "&#129353;"];

    target.innerHTML = ranking.map((item, index) => `
        <div class="ranking-row podium-row" style="--score-width: ${
            leaderScore > 0
                ? Math.max(4, Math.round((Number(item.puntaje || 0) / leaderScore) * 100))
                : 0
        }%">
            <div class="ranking-row-head">
                <div>
                    <strong>${medals[index] || `${index + 1}.`} ${escapeHtml(item.sede || item.nombre)}</strong>
                    <small>${escapeHtml(item.nombre || "")}</small>
                </div>
                <span>${Number(item.puntaje || 0)} pts</span>
            </div>
            <div class="ranking-bar" aria-hidden="true"><span></span></div>
        </div>
    `).join("") || "<div class='text-secondary'>Sin puntajes registrados.</div>";
}

function renderAnimatedPodium(target, rankingData) {
    const ranking = (rankingData?.ranking || []).slice(0, 3);
    const medals = ["&#129351;", "&#129352;", "&#129353;"];
    const podiumItems = ranking.map((item, index) => ({
        ...item,
        place: index + 1,
        medal: medals[index]
    }));
    const confetti = Array.from({length: 16}, (_, index) => (
        `<span style="--x:${(index % 8) * 12 + 4}%;--delay:${(index % 6) * 0.18}s"></span>`
    )).join("");

    target.innerHTML = `
        <div class="final-podium-view" data-podium-step="0" role="button" tabindex="0" aria-label="Avanzar premiacion">
            <div class="css-confetti" aria-hidden="true">${confetti}</div>
            <div class="podium-intro">
                <span>Resultados finales</span>
                <strong>Haz clic para revelar el podio</strong>
            </div>
            <div class="podium-stage">
                ${podiumItems.map(item => `
                    <div class="podium-place podium-place-${item.place}" data-place="${item.place}">
                        <div class="podium-medal">${item.medal}</div>
                        <strong>${escapeHtml(item.sede || item.nombre || "Equipo")}</strong>
                        <small>${escapeHtml(item.nombre || "")}</small>
                        <span>${Number(item.puntaje || 0)} pts</span>
                        <div class="podium-block"></div>
                    </div>
                `).join("")}
            </div>
        </div>
    `;

    const view = target.querySelector(".final-podium-view");
    const revealOrder = [3, 2, 1].filter(place => view.querySelector(`[data-place="${place}"]`));

    function advancePodium() {
        const currentStep = Number(view.dataset.podiumStep || 0);

        if (currentStep >= revealOrder.length) {
            return;
        }

        const nextStep = currentStep + 1;
        const place = revealOrder[currentStep];
        const podiumPlace = view.querySelector(`[data-place="${place}"]`);
        view.dataset.podiumStep = String(nextStep);
        view.classList.toggle("podium-started", nextStep > 0);

        if (podiumPlace) {
            podiumPlace.classList.add("podium-revealed");
        }

        if (place === 1 && podiumPlace) {
            view.classList.add("podium-champion-shown");
            playSound("celebrate", {volume: 0.5});
        }
    }

    view.addEventListener("click", advancePodium);
    view.addEventListener("keydown", event => {
        if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            advancePodium();
        }
    });
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
