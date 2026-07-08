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
    start: "/static/audio/start.wav",
    question: "/static/audio/question.wav",
    request: "/static/audio/request.wav",
    turn: "/static/audio/turn.wav",
    correct: "/static/audio/correct.wav",
    incorrect: "/static/audio/incorrect.wav",
    countdown: "/static/audio/countdown.wav",
    finish: "/static/audio/finish.wav",
    tick: "/static/audio/tick.wav",
    timeup: "/static/audio/timeup.wav"
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

function playSound(name) {
    if (!liveSoundsEnabled || !liveSoundPaths[name]) {
        return;
    }

    const audio = liveAudioCache[name] || new Audio(liveSoundPaths[name]);
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
    target.innerHTML = ranking.map((item, index) => `
        <div class="list-row podium-row">
            <div>
                <strong>${index + 1}. ${escapeHtml(item.sede || item.nombre)}</strong>
                <small>${escapeHtml(item.nombre || "")}</small>
            </div>
            <span class="badge text-bg-primary">${item.puntaje} pts</span>
        </div>
    `).join("") || "<div class='text-secondary'>Sin puntajes registrados.</div>";
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
    progressTarget.classList.toggle("timer-progress-warning", remaining !== null && remaining <= 5 && remaining > 0);
    progressTarget.classList.toggle("timer-progress-ended", remaining === 0);
}

function handleTimerSound(timer, key = "default") {
    const remaining = normalizedTimerValue(timer);

    if (remaining === null || liveTimerSoundState[key] === remaining) {
        return;
    }

    liveTimerSoundState[key] = remaining;

    if (remaining > 0 && remaining <= 5) {
        playSound("tick");
    } else if (remaining === 0) {
        playSound("timeup");
    }
}

function resetTimerSound(key = "default") {
    delete liveTimerSoundState[key];
}
