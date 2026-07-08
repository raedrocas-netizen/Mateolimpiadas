const participantSession = JSON.parse(localStorage.getItem("participantSession") || "{}");
const socket = io({transports: ["websocket"]});
const requestButton = document.getElementById("requestWord");
const statusEl = document.getElementById("participantStatus");
const questionText = document.getElementById("questionText");
const questionImage = document.getElementById("questionImage");
const rankingEl = document.getElementById("ranking");
const finalActions = document.getElementById("finalActions");
const teamScore = document.getElementById("teamScore");
const podiumTitle = document.getElementById("podiumTitle");
let hasRequestedForQuestion = false;

document.getElementById("teamName").textContent = participantSession.nombre_equipo || "Equipo";
document.getElementById("roomCode").textContent = participantSession.codigo_partida || "";

if (participantSession.codigo_partida) {
    socket.emit("participante_reconectar", participantSession);
}

function renderParticipantTimer(timer, duration = null) {
    renderTimer(
        document.getElementById("timer"),
        {
            ...(timer || {}),
            duration
        },
        document.getElementById("participantTimerProgress")
    );
    handleTimerSound(timer, "participant");
}

function setParticipantStatus(status, message) {
    statusEl.textContent = status || "Sala abierta";
    questionText.textContent = message || "Esperando que el juez inicie la competencia.";
}

function showTurnMessage(title, message) {
    statusEl.textContent = title;
    questionText.textContent = message;
    requestButton.disabled = true;
}

function showFinalPodium(rankingData) {
    const ranking = rankingData?.ranking || [];
    const own = ranking.find(
        item => item.participant_code === participantSession.codigo_participante
    );

    requestButton.classList.add("d-none");
    requestButton.disabled = true;
    finalActions.classList.remove("d-none");
    podiumTitle.classList.remove("d-none");
    teamScore.textContent = own
        ? `Puntaje de tu equipo: ${own.puntaje} pts`
        : "Puntaje final disponible en el marcador.";
    renderRanking(rankingEl, rankingData);
}

function renderParticipantQuestion(question) {
    questionText.textContent = question?.enunciado || "Pregunta actual";

    if (question?.imagen) {
        questionImage.src = question.imagen;
        questionImage.classList.remove("d-none");
    } else {
        questionImage.removeAttribute("src");
        questionImage.classList.add("d-none");
    }
}

requestButton.addEventListener("click", () => {
    playSound("request");
    hasRequestedForQuestion = true;
    requestButton.disabled = true;
    statusEl.textContent = "Solicitud enviada";
    socket.emit("pedir_palabra", participantSession);
});

socket.on("estado_sala", state => {
    renderParticipantTimer(state.timer, state.partida?.tiempo_por_pregunta);
    renderRanking(rankingEl, state.ranking);

    if (state.estado_competencia === "Esperando respuesta") {
        requestButton.disabled = true;
        statusEl.textContent = state.estado_competencia;
        if (state.pregunta) {
            renderParticipantQuestion(state.pregunta);
        } else {
            setParticipantStatus(
                state.estado_competencia,
                state.mensaje_estado || "Un equipo tiene la palabra."
            );
        }
    } else if (
        state.partida?.estado === "EN_CURSO"
        && state.pregunta
        && state.estado_competencia === "Pregunta en curso"
    ) {
        requestButton.disabled = hasRequestedForQuestion;
        statusEl.textContent = "Pregunta en curso";
        renderParticipantQuestion(state.pregunta);
    } else if (state.partida?.estado === "EN_CURSO") {
        requestButton.disabled = true;
        statusEl.textContent = state.estado_competencia || "Esperando siguiente pregunta";
        if (state.pregunta) {
            renderParticipantQuestion(state.pregunta);
        } else {
            questionImage.classList.add("d-none");
            setParticipantStatus(
                state.estado_competencia,
                state.mensaje_estado || "Esperando siguiente pregunta."
            );
        }
    } else if (state.partida?.estado === "FINALIZADA") {
        setParticipantStatus("Competencia finalizada", "La competencia ha terminado.");
        showFinalPodium(state.ranking);
    } else {
        requestButton.disabled = true;
        requestButton.classList.remove("d-none");
        finalActions.classList.add("d-none");
        podiumTitle.classList.add("d-none");
        questionImage.classList.add("d-none");
        setParticipantStatus(
            state.estado_competencia,
            state.mensaje_estado || "Esperando que el juez inicie la competencia."
        );
    }
});

socket.on("mostrar_pregunta", question => {
    playSound(Number(question?.numero_orden) === 1 ? "start" : "question");
    resetTimerSound("participant");
    hasRequestedForQuestion = false;
    renderParticipantQuestion(question);
    statusEl.textContent = "Pregunta en curso";
    requestButton.classList.remove("d-none");
    finalActions.classList.add("d-none");
    podiumTitle.classList.add("d-none");
    requestButton.disabled = false;
});

socket.on("estado_competencia", event => {
    if (event.contador === 5) {
        playSound("countdown");
    }

    if (event.estado === "Pregunta en curso") {
        requestButton.disabled = hasRequestedForQuestion;
        statusEl.textContent = "Pregunta en curso";
        questionText.textContent = event.mensaje || "Los equipos pueden pedir la palabra.";
        return;
    }

    requestButton.disabled = true;
    setParticipantStatus(event.estado, event.mensaje);
});

socket.on("actualizar_cronometro", timer => {
    renderParticipantTimer(timer);
    if (timer?.exhausted) {
        requestButton.disabled = true;
        statusEl.textContent = "Tiempo agotado";
    }
});

socket.on("habilitar_respuesta", request => {
    if (request.codigo_participante === participantSession.codigo_participante) {
        playSound("turn");
        hasRequestedForQuestion = true;
        showTurnMessage(
            "Tienen la palabra",
            "USTEDES TIENEN LA PALABRA"
        );
    }
});

socket.on("estado_palabra", request => {
    playSound("turn");
    if (request.codigo_participante === participantSession.codigo_participante) {
        hasRequestedForQuestion = true;
        showTurnMessage(
            "Tienen la palabra",
            "USTEDES TIENEN LA PALABRA"
        );
        return;
    }

    showTurnMessage(
        "Espere su turno",
        "OTRO EQUIPO ESTA RESPONDIENDO."
    );
});

socket.on("resultado_respuesta", payload => {
    const request = payload?.request;

    if (!request || request.codigo_participante !== participantSession.codigo_participante) {
        return;
    }

    const correct = request.estado === "CORRECTA";
    playSound(correct ? "correct" : "incorrect");
    hasRequestedForQuestion = true;
    statusEl.textContent = correct ? "Respuesta correcta" : "Respuesta incorrecta";
    questionText.textContent = correct
        ? "Puntaje actualizado. Esperando siguiente pregunta."
        : "Esperando siguiente pregunta.";
    requestButton.disabled = true;
});

socket.on("actualizar_puntajes", ranking => {
    renderRanking(rankingEl, ranking);
});

socket.on("mostrar_podio", ranking => {
    playSound("finish");
    questionText.textContent = "Competencia finalizada";
    statusEl.textContent = "Podio final";
    showFinalPodium(ranking);
});
