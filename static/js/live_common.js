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
    question: "/static/audio/question.mp3",
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

["pointerdown", "keydown", "touchstart"].forEach(eventName => {
    window.addEventListener(eventName, enableLiveSounds, {once: true, passive: true});
});

function playSound(name, options = {}) {
    if (!liveSoundsEnabled || !liveSoundPaths[name]) {
        return;
    }

    const audio = liveAudioCache[name] || new Audio(liveSoundPaths[name]);
    audio.volume = options.volume ?? audio.volume ?? 0.38;
    audio.playbackRate = options.rate || 1;
    audio.currentTime = 0;
    audio.play().catch(() => {});
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
    const medals = ["🥇", "🥈", "🥉"];

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
    const podiumItems = ranking.map((item, index) => ({
        ...item,
        place: index + 1,
        medal: ["🥇", "🥈", "🥉"][index],
        delay: [1.45, 0.75, 0.15][index]
    }));
    const confetti = Array.from({length: 16}, (_, index) => (
        `<span style="--x:${(index % 8) * 12 + 4}%;--delay:${(index % 6) * 0.18}s"></span>`
    )).join("");

    target.innerHTML = `
        <div class="final-podium-view">
            <div class="css-confetti" aria-hidden="true">${confetti}</div>
            <div class="podium-stage">
                ${podiumItems.map(item => `
                    <div class="podium-place podium-place-${item.place}" data-place="${item.place}" style="--podium-delay:${item.delay}s">
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

    const champion = target.querySelector('[data-place="1"]');

    if (champion) {
        champion.addEventListener("animationstart", () => {
            playSound("celebrate", {volume: 0.5});
        }, {once: true});
    }
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

    if (remaining === null || liveTimerSoundState[key] === remaining) {
        return;
    }

    liveTimerSoundState[key] = remaining;

    if (remaining > 0 && remaining <= 10) {
        const urgency = 11 - remaining;
        playSound("tick", {
            rate: 1 + urgency * 0.08,
            volume: Math.min(0.65, 0.28 + urgency * 0.035)
        });
    } else if (remaining === 0) {
        playSound("timeup");
    }
}

function resetTimerSound(key = "default") {
    delete liveTimerSoundState[key];
}
