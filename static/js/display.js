const displaySocket = io({transports: ["websocket"]});
const displayForm = document.getElementById("displayForm");
const displayJoinPanel = document.getElementById("displayJoinPanel");
const displayLivePanel = document.getElementById("displayLivePanel");
const displayWaitingPanel = document.getElementById("displayWaitingPanel");
const displayCompetitionPanel = document.getElementById("displayCompetitionPanel");
const displayPodiumPanel = document.getElementById("displayPodiumPanel");
const displayPodiumStage = document.getElementById("displayPodium");
const displayJoinMessage = document.getElementById("displayJoinMessage");
const displayConnectionStatus = document.getElementById("displayConnectionStatus");
const displayHideQuestionInput = document.getElementById("displayHideQuestion");
const displayCanControlPodium = displayLivePanel.dataset.canControlPodium === "true";
const displayParticipants = new Map();
const DISPLAY_QUEUE_LIMIT = 2;
const DISPLAY_HIDE_QUESTION_KEY = "mateolimpiadas-display-hide-question";
let displayCode = "";
let displayTotalQuestions = null;
let displayCurrentQuestion = null;
let displayState = {};
let displayRankingData = {ranking: []};
let displayRequests = [];
let displayPaused = false;
let suppressDisplayTimeupUntil = 0;
let displayPodiumState = {estado: "OCULTO", revision: 0};
let displayPodiumHydrated = false;
let displayPodiumCelebrated = false;
let displayQuestionHidden = readDisplayQuestionPreference();

function readDisplayQuestionPreference(storage = null) {
    try {
        const resolvedStorage = storage || window.sessionStorage;
        const storedValue = resolvedStorage.getItem(DISPLAY_HIDE_QUESTION_KEY);
        return storedValue === null ? true : storedValue !== "false";
    } catch (error) {
        return true;
    }
}

function saveDisplayQuestionPreference(hidden, storage = null) {
    try {
        const resolvedStorage = storage || window.sessionStorage;
        resolvedStorage.setItem(
            DISPLAY_HIDE_QUESTION_KEY,
            hidden ? "true" : "false"
        );
    } catch (error) {
        // El display puede continuar aunque el navegador bloquee el almacenamiento.
    }
}

function applyDisplayQuestionPreference(hidden = displayQuestionHidden) {
    displayQuestionHidden = Boolean(hidden);
    displayHideQuestionInput.checked = displayQuestionHidden;
    displayLivePanel.classList.toggle("question-hidden", displayQuestionHidden);
    displayCompetitionPanel.classList.toggle("question-hidden", displayQuestionHidden);
    const questionPanel = document.querySelector(".display-question-panel");
    questionPanel.hidden = displayQuestionHidden;
    questionPanel.setAttribute("aria-hidden", String(displayQuestionHidden));
}

function setDisplayMessage(message, success = true) {
    displayJoinMessage.textContent = message || "";
    displayJoinMessage.classList.toggle("text-danger", !success);
    displayJoinMessage.classList.toggle("text-success", success);
}

function setDisplayConnection(message, tone) {
    displayConnectionStatus.textContent = message;
    displayConnectionStatus.classList.remove(
        "is-connected",
        "is-reconnecting",
        "is-disconnected"
    );
    displayConnectionStatus.classList.add(`is-${tone}`);
}

function showDisplayLive() {
    displayJoinPanel.classList.add("d-none");
    displayLivePanel.classList.remove("d-none");
}

function setDisplayMode(mode) {
    showDisplayLive();
    const waiting = mode === "waiting";
    const competition = mode === "competition";
    const podium = mode === "podium";
    displayWaitingPanel.classList.toggle("d-none", !waiting);
    displayCompetitionPanel.classList.toggle("d-none", !competition);
    displayPodiumPanel.classList.toggle("d-none", !podium);
    displayLivePanel.classList.toggle("waiting-mode", waiting);
    displayLivePanel.classList.toggle("competition-mode", competition);
    displayLivePanel.classList.toggle("podium-mode", podium);

    if (!podium) {
        displayPodiumStage.querySelector(".final-podium-view")?.classList.remove(
            "podium-celebrating"
        );
    }
}

function renderDisplayImage(url) {
    const image = document.getElementById("displayQuestionImage");
    const questionPanel = document.querySelector(".display-question-panel");
    const hasImage = Boolean(url);
    [displayCompetitionPanel, questionPanel].forEach(target => {
        target?.classList.remove("has-question-image", "no-question-image");
        target?.classList.add(hasImage ? "has-question-image" : "no-question-image");
    });

    if (hasImage) {
        image.src = url;
        image.classList.remove("d-none");
        return;
    }

    image.removeAttribute("src");
    image.classList.add("d-none");
}

function renderDisplayQuestionCounter(question = displayCurrentQuestion) {
    const current = question?.numero_orden || displayRankingData?.current_question || "--";
    const total = displayTotalQuestions || displayRankingData?.total_questions || "--";
    document.getElementById("displayQuestionNumber").textContent = (
        `Pregunta ${current || "--"} / ${total || "--"}`
    );
}

function renderDisplayQuestion(question, fallback = "Esperando que el juez inicie la competencia.") {
    const panel = document.querySelector(".display-question-panel");
    const text = String(question?.enunciado || fallback || "");
    const explicitLines = text.split(/\r?\n/).length;
    displayCurrentQuestion = question || null;
    panel?.classList.remove("is-long", "is-very-long");

    if (text.trim().length >= 320 || explicitLines >= 5) {
        panel?.classList.add("is-very-long");
    } else if (text.trim().length >= 180 || explicitLines >= 3) {
        panel?.classList.add("is-long");
    }

    document.getElementById("displayQuestionText").textContent = text;
    renderDisplayImage(question?.imagen);
    renderDisplayQuestionCounter(question);
}

function showDisplayPaused() {
    displayPaused = true;
    displayCurrentQuestion = null;
    document.querySelector(".display-question-panel")?.classList.add("is-paused");
    renderDisplayStatus("PARTIDA PAUSADA");
    document.getElementById("displayQuestionText").textContent = (
        "Espera a que el juez reanude la partida."
    );
    renderDisplayImage("");
    renderDisplayQuestionCounter(null);
    setWordWaiting("La competencia está pausada.");
}

function leaveDisplayPaused() {
    displayPaused = false;
    document.querySelector(".display-question-panel")?.classList.remove("is-paused");
}

function renderDisplayTimer(timer, duration = null) {
    renderTimer(
        document.getElementById("displayTimer"),
        {...(timer || {}), duration},
        document.getElementById("displayTimerProgress")
    );
    handleTimerSound(timer, "display");
}

function teamLabel(request) {
    return request?.sede || request?.nombre || "Equipo";
}

function sortDisplayRequests(requests) {
    return [...(requests || [])].sort(
        (a, b) => Number(a.orden_solicitud || 0) - Number(b.orden_solicitud || 0)
    );
}

function upsertDisplayRequest(request) {
    if (!request?.id_solicitud) {
        return;
    }

    const index = displayRequests.findIndex(
        item => item.id_solicitud === request.id_solicitud
    );

    if (index >= 0) {
        displayRequests[index] = {...displayRequests[index], ...request};
    } else {
        displayRequests.push(request);
    }

    displayRequests = sortDisplayRequests(displayRequests);
}

function setDisplayQueue(requests) {
    displayRequests = sortDisplayRequests(requests || []);
    renderDisplayQueue();
}

function setWordWaiting(message = "Esperando solicitudes...") {
    document.getElementById("displayWordStatus").textContent = message;
    document.getElementById("displayWordStatus").classList.remove("display-word-active");
}

function setWordActive(request) {
    document.getElementById("displayWordStatus").textContent = "Turno asignado";
    document.getElementById("displayWordStatus").classList.add("display-word-active");
}

function renderDisplayQueue() {
    const target = document.getElementById("displayWordQueue");
    const active = displayRequests.find(item => item.estado === "EN_TURNO");
    const waiting = displayRequests.filter(item => item.estado === "EN_COLA");
    const visibleWaiting = waiting.slice(0, DISPLAY_QUEUE_LIMIT);
    const hiddenCount = Math.max(0, waiting.length - visibleWaiting.length);

    if (!active && waiting.length === 0) {
        target.innerHTML = (
            "<div class='text-secondary queue-empty'>"
            + "Aún no hay solicitudes de palabra."
            + "</div>"
        );
        return;
    }

    target.innerHTML = `
        ${active ? `
            <div class="queue-active">
                <span class="queue-label">EN TURNO:</span>
                <strong class="queue-team">${escapeHtml(teamLabel(active))}</strong>
            </div>
        ` : ""}
        ${visibleWaiting.length ? `
            <div class="queue-waiting">
                ${visibleWaiting.map((item, index) => (
                    `<div class="queue-next ${index === 0 ? "is-next" : "is-waiting"}">
                        <span class="queue-label">${index === 0 ? "SIGUIENTE:" : "EN ESPERA:"}</span>
                        <strong class="queue-team">${escapeHtml(teamLabel(item))}</strong>
                    </div>`
                )).join("")}
                ${hiddenCount ? `<strong class="queue-more">+${hiddenCount} equipos en espera</strong>` : ""}
            </div>
        ` : ""}
    `;
}

function renderDisplayStatus(status, message = "") {
    document.getElementById("displayStatus").textContent = status || "Sala abierta";

    if (message && !displayCurrentQuestion) {
        document.getElementById("displayQuestionText").textContent = message;
    }
}

function participantSiteKey(site) {
    return normalizedSiteName(site);
}

function registeredParticipantsFromState(participants) {
    return (participants || []).filter(item => (
        item?.id_participante || item?.codigo_participante || item?.nombre
    )).map(item => ({
        sede: item.sede || "",
        nombre: item.nombre || "",
        integrantes: item.integrantes || "",
        conectado: Number(item.conectado) === 1 ? 1 : 0
    }));
}

function applyDisplayParticipants(payload) {
    const mode = payload?.modo || "ACTUALIZAR";
    const participants = payload?.participantes || [];

    if (mode === "REEMPLAZAR") {
        displayParticipants.clear();
    }

    participants.forEach(participant => {
        const key = participantSiteKey(participant.sede);

        if (!key) {
            return;
        }

        if (mode === "ELIMINAR") {
            displayParticipants.delete(key);
            return;
        }

        const previous = displayParticipants.get(key) || {};
        displayParticipants.set(key, {
            ...previous,
            ...participant,
            integrantes: Object.hasOwn(participant, "integrantes")
                ? participant.integrantes
                : previous.integrantes || ""
        });
    });

    renderDisplayWaitingTeams();
    renderDisplayRanking(displayRankingData);
}

function renderDisplayWaitingTeams() {
    const target = document.getElementById("displayWaitingTeams");
    const empty = document.getElementById("displayWaitingEmpty");
    const participants = [...displayParticipants.values()];
    const previousCards = new Map(
        [...target.querySelectorAll("[data-waiting-site]")].map(card => [
            card.dataset.waitingSite,
            card
        ])
    );
    const activeKeys = new Set();
    const connectedCount = participants.filter(item => Number(item.conectado) === 1).length;
    document.getElementById("displayConnectedCount").textContent = String(connectedCount);
    empty.classList.toggle("d-none", participants.length > 0);
    target.classList.toggle("d-none", participants.length === 0);
    target.dataset.teamCount = String(participants.length);
    displayWaitingPanel.classList.toggle(
        "is-sparse",
        participants.length > 0 && participants.length <= 4
    );

    participants.forEach(participant => {
        const key = participantSiteKey(participant.sede);
        const identity = teamSiteIdentity(participant.sede);
        const connected = Number(participant.conectado) === 1;
        const members = parseTeamMembers(participant.integrantes);
        const card = previousCards.get(key) || document.createElement("article");
        activeKeys.add(key);
        card.className = `display-team-card${connected ? " is-connected" : " is-disconnected"}`;
        card.dataset.waitingSite = key;
        card.dataset.siteIdentity = identity.key;
        card.dataset.memberCount = String(members.length);
        card.style.setProperty("--site-accent", identity.accent);
        card.style.setProperty("--site-tint", identity.tint);
        card.style.setProperty("--site-detail", identity.detail);
        card.innerHTML = `
            <div class="display-team-card-head">
                <div>
                    <span class="site-identity-dot" aria-hidden="true"></span>
                    <strong>${escapeHtml(participant.sede || "Sede")}</strong>
                </div>
                <span class="team-connection-label">${connected ? "Conectado" : "Desconectado"}</span>
            </div>
            <h3>${escapeHtml(participant.nombre || "Equipo registrado")}</h3>
            ${teamMembersListHtml(participant.integrantes)}
        `;
        target.appendChild(card);

        if (!previousCards.has(key)) {
            card.classList.add("display-team-entering");
        }
    });

    previousCards.forEach((card, key) => {
        if (activeKeys.has(key)) {
            return;
        }

        if (prefersReducedMotion()) {
            card.remove();
            return;
        }

        card.classList.add("display-team-leaving");
        window.setTimeout(() => card.remove(), 260);
    });
}

function enrichedDisplayRanking(ranking) {
    return {
        ...(ranking || {}),
        ranking: (ranking?.ranking || []).map(item => {
            const participant = displayParticipants.get(participantSiteKey(item.sede));
            return {
                ...item,
                integrantes: participant?.integrantes || item.integrantes || ""
            };
        })
    };
}

function renderDisplayRanking(ranking) {
    displayRankingData = ranking || displayRankingData;
    displayTotalQuestions = displayRankingData?.total_questions || displayTotalQuestions;
    renderRanking(
        document.getElementById("displayRanking"),
        enrichedDisplayRanking(displayRankingData)
    );
    renderDisplayQuestionCounter();
}

function displayPodiumCanAdvance() {
    return (
        displayCanControlPodium
        && displayState?.partida?.estado === "FINALIZADA"
        && displayPodiumState.estado !== "COMPLETO"
    );
}

function updateDisplayPodiumInteraction() {
    const view = displayPodiumStage.querySelector(".final-podium-view");

    if (!view) {
        return;
    }

    const canAdvance = displayPodiumCanAdvance();
    const nextState = nextPodiumState(displayPodiumState.estado, 1).replaceAll("_", " ");
    view.classList.toggle("podium-interactive", canAdvance);

    if (canAdvance) {
        view.setAttribute("role", "button");
        view.setAttribute("tabindex", "0");
        view.setAttribute("aria-label", `Avanzar podio a ${nextState}`);
    } else {
        view.removeAttribute("role");
        view.removeAttribute("tabindex");
        view.removeAttribute("aria-label");
    }
}

function updateDisplayPodiumControls() {
    const final = displayState?.partida?.estado === "FINALIZADA";
    const controls = document.getElementById("displayPodiumControls");
    const previousButton = document.getElementById("displayPodiumPrevious");
    const nextButton = document.getElementById("displayPodiumNext");
    const stateLabel = document.getElementById("displayPodiumState");
    const stateIndex = PODIUM_STATE_ORDER.indexOf(displayPodiumState.estado);
    const controlsAvailable = final && displayCanControlPodium;
    controls?.classList.toggle("d-none", !controlsAvailable);

    if (stateLabel) {
        stateLabel.textContent = displayPodiumState.estado.replaceAll("_", " ");
    }

    if (previousButton) {
        previousButton.disabled = !controlsAvailable || stateIndex <= 0;
    }

    if (nextButton) {
        nextButton.disabled = (
            !controlsAvailable || stateIndex >= PODIUM_STATE_ORDER.length - 1
        );
    }

    updateDisplayPodiumInteraction();
}

function renderDisplayPodium(options = {}) {
    renderSynchronizedPodium(
        document.getElementById("displayPodium"),
        enrichedDisplayRanking(displayRankingData),
        displayPodiumState,
        options
    );
    updateDisplayPodiumControls();
}

function showDisplayPodium(ranking = displayRankingData) {
    leaveDisplayPaused();
    displayCurrentQuestion = null;
    displayRankingData = ranking || displayRankingData;
    setDisplayMode("podium");
    renderDisplayPodium({animate: false});
    renderDisplayStatus("Competencia finalizada", "La competencia ha terminado.");
    renderDisplayImage("");
    setWordWaiting("Podio final disponible.");
}

function applyDisplayPodiumState(payload) {
    if (!payload || !PODIUM_STATE_ORDER.includes(payload.estado)) {
        return;
    }

    if (
            payload.codigo_partida
            && displayCode
            && payload.codigo_partida !== displayCode
    ) {
        return;
    }

    const previous = displayPodiumState;
    const hydrated = displayPodiumHydrated;
    const changedRevision = hydrated && Number(payload.revision) > Number(previous.revision);
    const celebrate = (
        changedRevision
        && !displayPodiumCelebrated
        && ["PRIMER_LUGAR", "COMPLETO"].includes(payload.estado)
    );

    if (payload.estado === "OCULTO" && Number(payload.revision) === 0) {
        displayPodiumCelebrated = false;
    } else if (celebrate) {
        displayPodiumCelebrated = true;
    }

    displayPodiumState = payload;
    displayPodiumHydrated = true;

    if (displayState?.partida?.estado === "FINALIZADA") {
        renderDisplayPodium({
            animate: changedRevision,
            celebrate
        });
    }
}

function applyDisplayState(state) {
    if (!state) {
        setDisplayMessage("No fue posible cargar la sala.", false);
        return;
    }

    displayState = state;
    displayCode = String(state.partida?.codigo_partida || displayCode).toUpperCase();
    displayTotalQuestions = state.ranking?.total_questions || displayTotalQuestions;
    document.getElementById("displayGameName").textContent = state.partida?.nombre || "Competencia";
    document.getElementById("displayWaitingGameName").textContent = state.partida?.nombre || "Competencia";
    document.getElementById("displayRoomCode").textContent = displayCode || "--";
    document.getElementById("displayWaitingRoomCode").textContent = displayCode || "--";
    renderDisplayStatus(state.estado_competencia, state.mensaje_estado);
    renderDisplayTimer(state.timer, state.partida?.tiempo_por_pregunta);
    renderDisplayRanking(state.ranking);
    setDisplayQueue(state.solicitudes || []);

    if (Array.isArray(state.participantes)) {
        applyDisplayParticipants({
            modo: "REEMPLAZAR",
            participantes: registeredParticipantsFromState(state.participantes)
        });
    }

    if (["BORRADOR", "ESPERANDO"].includes(state.partida?.estado)) {
        leaveDisplayPaused();
        setDisplayMode("waiting");
        return;
    }

    if (state.partida?.estado === "FINALIZADA") {
        showDisplayPodium(state.ranking);
        return;
    }

    setDisplayMode("competition");

    if (state.partida?.estado === "PAUSADA") {
        showDisplayPaused();
        return;
    }

    leaveDisplayPaused();

    if (state.pregunta) {
        renderDisplayQuestion(state.pregunta);
    } else {
        renderDisplayQuestion(null, state.mensaje_estado || "Esperando que el juez inicie la competencia.");
    }

    const activeRequest = (state.solicitudes || []).find(item => item.estado === "EN_TURNO");
    activeRequest ? setWordActive(activeRequest) : setWordWaiting();
}

function requestDisplayPodiumState(direction) {
    const state = nextPodiumState(displayPodiumState.estado, direction);

    if (
            !displayCanControlPodium
            || state === displayPodiumState.estado
            || displayState?.partida?.estado !== "FINALIZADA"
    ) {
        return;
    }

    displaySocket.emit("cambiar_estado_podio", {
        codigo_partida: displayCode,
        estado: state
    });
}

function joinDisplayRoom() {
    if (!displayCode || !displaySocket.connected) {
        return;
    }

    displaySocket.emit("display_unirse", {codigo_partida: displayCode});
}

function connectDisplayToAnotherRoom() {
    displayCode = "";
    displayTotalQuestions = null;
    displayCurrentQuestion = null;
    displayState = {};
    displayRankingData = {ranking: []};
    displayRequests = [];
    displayPaused = false;
    suppressDisplayTimeupUntil = 0;
    displayPodiumState = {estado: "OCULTO", revision: 0};
    displayPodiumHydrated = false;
    displayPodiumCelebrated = false;
    displayParticipants.clear();
    displayForm.elements.codigo_partida.value = "";

    displaySocket.removeAllListeners();
    displaySocket.disconnect();
    displayLivePanel.classList.add("d-none");
    displayJoinPanel.classList.remove("d-none");
    window.location.assign("/display");
}

document.getElementById("displayPodiumPrevious")?.addEventListener("click", () => {
    requestDisplayPodiumState(-1);
});
document.getElementById("displayPodiumNext")?.addEventListener("click", () => {
    requestDisplayPodiumState(1);
});
document.getElementById("displayConnectAnotherRoom")?.addEventListener(
    "click",
    connectDisplayToAnotherRoom
);
displayPodiumStage.addEventListener("click", event => {
    if (event.target.closest("button")) {
        return;
    }

    requestDisplayPodiumState(1);
});
displayPodiumStage.addEventListener("keydown", event => {
    if (
            !event.target.closest(".final-podium-view")
            || !["Enter", " "].includes(event.key)
    ) {
        return;
    }

    event.preventDefault();
    requestDisplayPodiumState(1);
});

displayForm.addEventListener("submit", event => {
    event.preventDefault();
    enableLiveSounds();
    displayCode = String(displayForm.codigo_partida.value || "").trim().toUpperCase();
    displayQuestionHidden = displayHideQuestionInput.checked;
    saveDisplayQuestionPreference(displayQuestionHidden);
    applyDisplayQuestionPreference();

    if (!displayCode) {
        setDisplayMessage("Ingrese el código de sala.", false);
        return;
    }

    setDisplayMessage("Conectando pantalla...", true);
    joinDisplayRoom();
});

displayHideQuestionInput.addEventListener("change", () => {
    displayQuestionHidden = displayHideQuestionInput.checked;
    saveDisplayQuestionPreference(displayQuestionHidden);
    applyDisplayQuestionPreference();
});

displaySocket.on("connect", () => {
    setDisplayConnection("Conectado", "connected");
    joinDisplayRoom();
});

displaySocket.on("disconnect", () => {
    setDisplayConnection("Reconectando", "reconnecting");
});

displaySocket.on("connect_error", () => {
    setDisplayConnection("Sin conexión", "disconnected");
});

displaySocket.on("estado_sala", state => {
    applyDisplayState(state);
});

displaySocket.on("actualizar_participantes_display", payload => {
    applyDisplayParticipants(payload);
});

displaySocket.on("estado_podio", payload => {
    applyDisplayPodiumState(payload);
});

displaySocket.on("error_sala", payload => {
    setDisplayMessage(payload?.message || "No fue posible conectar la pantalla.", false);
});

displaySocket.on("resultado_accion", payload => {
    if (!payload?.success && displayState?.partida?.estado === "FINALIZADA") {
        document.getElementById("displayPodiumState").title = payload.message || "No fue posible actualizar el podio.";
    }
});

displaySocket.on("estado_competencia", event => {
    if (displayPaused && event.estado !== "Competencia finalizada") {
        return;
    }

    if (event.contador === 5) {
        playSound("countdown");
    }

    displayState = {
        ...displayState,
        estado_competencia: event.estado,
        mensaje_estado: event.mensaje
    };
    renderDisplayStatus(event.estado, event.mensaje);

    if (event.contador) {
        setDisplayMode("competition");
        displayCurrentQuestion = null;
        renderDisplayQuestion(null, event.mensaje);
        setWordWaiting("La pregunta está por iniciar.");
    }
});

displaySocket.on("mostrar_pregunta", question => {
    if (displayPaused) {
        return;
    }

    if (Number(question?.numero_orden) === 1) {
        playSound("start");
    }
    resetTimerSound("display");
    setDisplayMode("competition");
    setDisplayQueue([]);
    displayState = {
        ...displayState,
        partida: {...(displayState.partida || {}), estado: "EN_CURSO"},
        estado_competencia: "Pregunta en curso",
        mensaje_estado: "Los equipos pueden pedir la palabra."
    };
    renderDisplayStatus("Pregunta en curso", "Los equipos pueden pedir la palabra.");
    renderDisplayQuestion(question);
    setWordWaiting();
});

displaySocket.on("actualizar_cronometro", timer => {
    if (displayPaused) {
        return;
    }

    const remaining = normalizedTimerValue(timer);
    const suppressTimeupSound = (
        Date.now() <= suppressDisplayTimeupUntil
        && (remaining === 0 || timer?.exhausted)
    );

    if (suppressTimeupSound) {
        renderTimer(
            document.getElementById("displayTimer"),
            timer,
            document.getElementById("displayTimerProgress")
        );
        stopTimerTickSound("display");
        suppressDisplayTimeupUntil = 0;
        return;
    }

    renderDisplayTimer(timer);
});

displaySocket.on("actualizar_puntajes", ranking => {
    renderDisplayRanking(ranking);

    if (displayState?.partida?.estado === "FINALIZADA") {
        renderDisplayPodium({animate: false});
    }
});

displaySocket.on("solicitud_palabra_publica", payload => {
    if (displayPaused) {
        return;
    }

    playSound("request");
    if (Array.isArray(payload?.queue)) {
        setDisplayQueue(payload.queue);
    } else if (payload?.request) {
        upsertDisplayRequest(payload.request);
        renderDisplayQueue();
    }
});

displaySocket.on("estado_palabra", request => {
    if (displayPaused) {
        return;
    }

    playSound("turn");
    upsertDisplayRequest(request);
    renderDisplayQueue();
    setWordActive(request);
    renderDisplayStatus("Esperando respuesta", "Un equipo tiene la palabra.");
});

displaySocket.on("respuesta_publica", payload => {
    if (displayPaused) {
        return;
    }

    const correct = payload?.resultado === "CORRECTA";

    if (correct) {
        suppressDisplayTimeupUntil = Date.now() + 3000;
        stopSound("timeup");
    }

    playSound(correct ? "correct" : "incorrect");

    if (Array.isArray(payload?.affected_requests)) {
        setDisplayQueue(
            payload.affected_requests.filter(
                item => item.estado === "EN_COLA" || item.estado === "EN_TURNO"
            )
        );
    }
    if (payload?.next_request) {
        upsertDisplayRequest(payload.next_request);
        renderDisplayQueue();
    }
    renderDisplayStatus(
        correct ? "Esperando siguiente pregunta" : "Pregunta en curso",
        correct ? "Esperando siguiente pregunta." : "Los equipos pueden pedir la palabra."
    );
    payload?.next_request
        ? setWordActive(payload.next_request)
        : setWordWaiting(correct ? "Esperando siguiente pregunta." : "Esperando solicitudes...");
});

displaySocket.on("mostrar_podio", ranking => {
    playSound("finish");
    displayState = {
        ...displayState,
        partida: {...(displayState.partida || {}), estado: "FINALIZADA"}
    };
    renderDisplayRanking(ranking);
    showDisplayPodium(ranking);
});

applyDisplayQuestionPreference();
