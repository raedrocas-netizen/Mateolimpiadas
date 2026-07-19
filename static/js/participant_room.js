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
let hasAnsweredForQuestion = false;
let participantQuestionId = null;
let participantPaused = false;

document.getElementById("teamName").textContent = participantSession.nombre_equipo || "Equipo";
document.getElementById("roomCode").textContent = participantSession.codigo_partida || "";

socket.on("connect", () => {
    if (participantSession.codigo_partida) {
        socket.emit("participante_reconectar", participantSession);
    }
});

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

function ownWordRequest(requests = []) {
    return (requests || []).find(
        item => item.codigo_participante === participantSession.codigo_participante
    );
}

function showFinalPodium(rankingData) {
    const ranking = rankingData?.ranking || [];
    const own = ranking.find(
        item => item.participant_code === participantSession.codigo_participante
    );

    leaveParticipantPaused();
    document.querySelector(".participant-view")?.classList.add("podium-mode");
    requestButton.classList.add("d-none");
    requestButton.disabled = true;
    finalActions.classList.remove("d-none");
    podiumTitle.classList.remove("d-none");
    teamScore.textContent = own
        ? `Puntaje de tu equipo: ${own.puntaje} pts`
        : "Puntaje final disponible en el marcador.";
    renderAnimatedPodium(rankingEl, rankingData);
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

function clearParticipantQuestion() {
    questionImage.removeAttribute("src");
    questionImage.classList.add("d-none");
}

function syncParticipantQuestion(question, ownRequest = null) {
    const questionId = question?.id_partida_pregunta || null;

    if (questionId && String(questionId) !== String(participantQuestionId || "")) {
        participantQuestionId = questionId;
        hasRequestedForQuestion = false;
        hasAnsweredForQuestion = false;
    }

    if (ownRequest) {
        hasRequestedForQuestion = true;
        hasAnsweredForQuestion = ["CORRECTA", "INCORRECTA"].includes(ownRequest.estado);
    }
}

function showParticipantPaused() {
    participantPaused = true;
    document.querySelector(".participant-view")?.classList.add("is-paused");
    requestButton.disabled = true;
    requestButton.classList.add("d-none");
    finalActions.classList.add("d-none");
    podiumTitle.classList.add("d-none");
    clearParticipantQuestion();
    setParticipantStatus(
        "PARTIDA PAUSADA",
        "Espera a que el juez reanude la partida."
    );
}

function leaveParticipantPaused() {
    participantPaused = false;
    document.querySelector(".participant-view")?.classList.remove("is-paused");
}

requestButton.addEventListener("click", () => {
    if (participantPaused) {
        return;
    }

    playSound("request");
    hasRequestedForQuestion = true;
    requestButton.disabled = true;
    statusEl.textContent = "Solicitud enviada";
    socket.emit("pedir_palabra", participantSession);
});

socket.on("estado_sala", state => {
    renderParticipantTimer(state.timer, state.partida?.tiempo_por_pregunta);
    renderRanking(rankingEl, state.ranking);
    const ownRequest = ownWordRequest(state.solicitudes);
    syncParticipantQuestion(state.pregunta, ownRequest);

    if (state.partida?.estado === "PAUSADA") {
        showParticipantPaused();
        return;
    }

    leaveParticipantPaused();
    requestButton.classList.remove("d-none");

    if (state.estado_competencia === "Esperando respuesta") {
        statusEl.textContent = state.estado_competencia;
        if (state.pregunta) {
            renderParticipantQuestion(state.pregunta);
        } else {
            setParticipantStatus(
                state.estado_competencia,
                state.mensaje_estado || "Un equipo tiene la palabra."
            );
        }

        if (ownRequest?.estado === "EN_TURNO") {
            hasRequestedForQuestion = true;
            showTurnMessage("Tienen la palabra", "USTEDES TIENEN LA PALABRA");
        } else if (ownRequest || hasRequestedForQuestion || hasAnsweredForQuestion) {
            requestButton.disabled = true;
            statusEl.textContent = "Esperando turno";
        } else {
            requestButton.disabled = false;
            statusEl.textContent = "Otro equipo esta respondiendo";
        }
    } else if (
        state.partida?.estado === "EN_CURSO"
        && state.pregunta
        && state.estado_competencia === "Pregunta en curso"
    ) {
        requestButton.disabled = hasRequestedForQuestion || hasAnsweredForQuestion;
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
    if (participantPaused) {
        return;
    }

    if (Number(question?.numero_orden) === 1) {
        playSound("start");
    }
    resetTimerSound("participant");
    document.querySelector(".participant-view")?.classList.remove("podium-mode");
    syncParticipantQuestion(question);
    renderParticipantQuestion(question);
    statusEl.textContent = "Pregunta en curso";
    requestButton.classList.remove("d-none");
    finalActions.classList.add("d-none");
    podiumTitle.classList.add("d-none");
    requestButton.disabled = false;
});

socket.on("estado_competencia", event => {
    if (participantPaused && event.estado !== "Competencia finalizada") {
        return;
    }

    if (event.contador === 5) {
        playSound("countdown");
    }

    if (event.estado === "Pregunta en curso") {
        requestButton.disabled = hasRequestedForQuestion || hasAnsweredForQuestion;
        statusEl.textContent = "Pregunta en curso";
        questionText.textContent = event.mensaje || "Los equipos pueden pedir la palabra.";
        return;
    }

    requestButton.disabled = true;
    setParticipantStatus(event.estado, event.mensaje);
});

socket.on("actualizar_cronometro", timer => {
    if (participantPaused) {
        return;
    }

    renderParticipantTimer(timer);
    if (timer?.exhausted) {
        requestButton.disabled = true;
        statusEl.textContent = "Tiempo agotado";
    }
});

socket.on("habilitar_respuesta", request => {
    if (participantPaused) {
        return;
    }

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
    if (participantPaused) {
        return;
    }

    playSound("turn");
    if (request.codigo_participante === participantSession.codigo_participante) {
        hasRequestedForQuestion = true;
        showTurnMessage(
            "Tienen la palabra",
            "USTEDES TIENEN LA PALABRA"
        );
        return;
    }

    statusEl.textContent = hasRequestedForQuestion
        ? "Esperando turno"
        : "Otro equipo esta respondiendo";
    questionText.textContent = hasAnsweredForQuestion
        ? questionText.textContent
        : "OTRO EQUIPO ESTA RESPONDIENDO. Puedes pedir la palabra si aun no estas en cola.";
    requestButton.disabled = hasRequestedForQuestion || hasAnsweredForQuestion;
});

socket.on("resultado_respuesta", payload => {
    if (participantPaused) {
        return;
    }

    const request = payload?.request;

    if (!request || request.codigo_participante !== participantSession.codigo_participante) {
        return;
    }

    const correct = request.estado === "CORRECTA";
    playSound(correct ? "correct" : "incorrect");
    hasRequestedForQuestion = true;
    hasAnsweredForQuestion = true;
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

socket.on("participante_eliminado", payload => {
    localStorage.removeItem("participantSession");
    const message = payload?.message || "El juez eliminó este equipo de la sala de espera.";
    sessionStorage.setItem("participantRemovalMessage", message);
    socket.disconnect();
    window.location.replace("/participante/?equipo_eliminado=1");
});
