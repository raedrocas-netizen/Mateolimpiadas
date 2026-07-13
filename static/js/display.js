const displaySocket = io({transports: ["websocket"]});
const displayForm = document.getElementById("displayForm");
const displayJoinPanel = document.getElementById("displayJoinPanel");
const displayLivePanel = document.getElementById("displayLivePanel");
const displayJoinMessage = document.getElementById("displayJoinMessage");
let displayCode = "";
let displayTotalQuestions = null;
let displayCurrentQuestion = null;
let displayState = {};
let displayRequests = [];

function setDisplayMessage(message, success = true) {
    displayJoinMessage.textContent = message || "";
    displayJoinMessage.classList.toggle("text-danger", !success);
    displayJoinMessage.classList.toggle("text-success", success);
}

function showDisplayLive() {
    displayJoinPanel.classList.add("d-none");
    displayLivePanel.classList.remove("d-none");
}

function renderDisplayImage(url) {
    const image = document.getElementById("displayQuestionImage");

    if (url) {
        image.src = url;
        image.classList.remove("d-none");
        return;
    }

    image.removeAttribute("src");
    image.classList.add("d-none");
}

function renderDisplayQuestionCounter(question = displayCurrentQuestion) {
    const current = question?.numero_orden || displayState?.ranking?.current_question || "--";
    const total = displayTotalQuestions || displayState?.ranking?.total_questions || "--";
    document.getElementById("displayQuestionNumber").textContent = `Pregunta ${current || "--"} / ${total || "--"}`;
}

function renderDisplayQuestion(question, fallback = "Esperando que el juez inicie la competencia.") {
    displayCurrentQuestion = question || displayCurrentQuestion;
    document.getElementById("displayQuestionText").textContent = question?.enunciado || fallback;
    renderDisplayImage(question?.imagen);
    renderDisplayQuestionCounter(question);
}

function renderDisplayTimer(timer, duration = null) {
    renderTimer(
        document.getElementById("displayTimer"),
        {
            ...(timer || {}),
            duration
        },
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
        displayRequests[index] = {
            ...displayRequests[index],
            ...request
        };
    } else {
        displayRequests.push(request);
    }

    displayRequests = sortDisplayRequests(displayRequests);
}

function setDisplayQueue(requests) {
    displayRequests = sortDisplayRequests(requests || []);
    renderDisplayQueue();
}

function setWordWaiting(message = "Esperando que un equipo solicite la palabra...") {
    document.getElementById("displayWordStatus").textContent = message;
    document.getElementById("displayWordStatus").classList.remove("display-word-active");
}

function setWordActive(request) {
    document.getElementById("displayWordStatus").textContent = `Responde: ${teamLabel(request)}`;
    document.getElementById("displayWordStatus").classList.add("display-word-active");
}

function renderDisplayQueue() {
    const target = document.getElementById("displayWordQueue");
    const active = displayRequests.find(item => item.estado === "EN_TURNO");
    const waiting = displayRequests.filter(item => item.estado === "EN_COLA");

    if (!active && waiting.length === 0) {
        target.innerHTML = "<div class='text-secondary'>Sin solicitudes.</div>";
        return;
    }

    target.innerHTML = `
        ${active ? `
            <div class="queue-active">
                <small>Microfono abierto</small>
                <strong>${escapeHtml(teamLabel(active))}</strong>
            </div>
        ` : ""}
        <div class="queue-waiting">
            <small>En espera</small>
            ${
                waiting.length
                    ? waiting.map((item, index) => `<div>${index + 1}. ${escapeHtml(teamLabel(item))}</div>`).join("")
                    : "<div class='text-secondary'>Nadie en cola.</div>"
            }
        </div>
    `;
}

function renderDisplayStatus(status, message = "") {
    document.getElementById("displayStatus").textContent = status || "Sala abierta";

    if (message && !displayCurrentQuestion) {
        document.getElementById("displayQuestionText").textContent = message;
    }
}

function renderDisplayRanking(ranking) {
    displayTotalQuestions = ranking?.total_questions || displayTotalQuestions;
    renderRanking(document.getElementById("displayRanking"), ranking);
    renderDisplayQuestionCounter();
}

function showDisplayPodium(ranking) {
    displayCurrentQuestion = null;
    displayLivePanel.classList.add("podium-mode");
    document.getElementById("displayPodiumPanel").classList.remove("d-none");
    renderAnimatedPodium(document.getElementById("displayPodium"), ranking);
    renderDisplayStatus("Competencia finalizada", "La competencia ha terminado.");
    document.getElementById("displayQuestionText").textContent = "Competencia finalizada.";
    renderDisplayImage("");
    setWordWaiting("Podio final disponible.");
}

function applyDisplayState(state) {
    if (!state) {
        setDisplayMessage("No fue posible cargar la sala.", false);
        return;
    }

    displayState = state;
    displayTotalQuestions = state.ranking?.total_questions || displayTotalQuestions;
    showDisplayLive();
    document.getElementById("displayGameName").textContent = state.partida?.nombre || "Competencia";
    document.getElementById("displayRoomCode").textContent = state.partida?.codigo_partida || displayCode;
    renderDisplayStatus(state.estado_competencia, state.mensaje_estado);
    renderDisplayTimer(state.timer, state.partida?.tiempo_por_pregunta);
    renderDisplayRanking(state.ranking);

    if (state.pregunta) {
        renderDisplayQuestion(state.pregunta);
    } else {
        displayCurrentQuestion = null;
        renderDisplayQuestion(null, state.mensaje_estado || "Esperando que el juez inicie la competencia.");
    }

    const activeRequest = (state.solicitudes || []).find(item => item.estado === "EN_TURNO");
    setDisplayQueue(state.solicitudes || []);
    if (activeRequest) {
        setWordActive(activeRequest);
    } else if (state.partida?.estado === "FINALIZADA") {
        showDisplayPodium(state.ranking);
    } else {
        setWordWaiting();
    }
}

displayForm.addEventListener("submit", event => {
    event.preventDefault();
    enableLiveSounds();
    displayCode = String(displayForm.codigo_partida.value || "").trim().toUpperCase();

    if (!displayCode) {
        setDisplayMessage("Ingrese el codigo de sala.", false);
        return;
    }

    setDisplayMessage("Conectando pantalla...", true);
    displaySocket.emit("display_unirse", {codigo_partida: displayCode});
});

displaySocket.on("estado_sala", state => {
    applyDisplayState(state);
});

displaySocket.on("error_sala", payload => {
    setDisplayMessage(payload?.message || "No fue posible conectar la pantalla.", false);
});

displaySocket.on("estado_competencia", event => {
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
        displayCurrentQuestion = null;
        renderDisplayQuestion(null, event.mensaje);
        setWordWaiting("La pregunta esta por iniciar.");
    }
});

displaySocket.on("mostrar_pregunta", question => {
    if (Number(question?.numero_orden) === 1) {
        playSound("start");
    }
    resetTimerSound("display");
    displayLivePanel.classList.remove("podium-mode");
    setDisplayQueue([]);
    document.getElementById("displayPodiumPanel").classList.add("d-none");
    displayState = {
        ...displayState,
        estado_competencia: "Pregunta en curso",
        mensaje_estado: "Los equipos pueden pedir la palabra."
    };
    renderDisplayStatus("Pregunta en curso", "Los equipos pueden pedir la palabra.");
    renderDisplayQuestion(question);
    setWordWaiting();
});

displaySocket.on("actualizar_cronometro", timer => {
    renderDisplayTimer(timer);
});

displaySocket.on("actualizar_puntajes", ranking => {
    renderDisplayRanking(ranking);
});

displaySocket.on("solicitud_palabra_publica", payload => {
    playSound("request");
    if (Array.isArray(payload?.queue)) {
        setDisplayQueue(payload.queue);
    } else if (payload?.request) {
        upsertDisplayRequest(payload.request);
        renderDisplayQueue();
    }
});

displaySocket.on("estado_palabra", request => {
    playSound("turn");
    upsertDisplayRequest(request);
    renderDisplayQueue();
    setWordActive(request);
    renderDisplayStatus("Esperando respuesta", "Un equipo tiene la palabra.");
});

displaySocket.on("respuesta_publica", payload => {
    const correct = payload?.resultado === "CORRECTA";
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
    if (payload?.next_request) {
        setWordActive(payload.next_request);
    } else {
        setWordWaiting(correct ? "Esperando siguiente pregunta." : "Esperando que un equipo solicite la palabra...");
    }
});

displaySocket.on("mostrar_podio", ranking => {
    playSound("finish");
    renderDisplayRanking(ranking);
    showDisplayPodium(ranking);
});
