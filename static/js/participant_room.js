const storedParticipantSession = localStorage.getItem("participantSession");
let participantSession = {};

try {
    participantSession = JSON.parse(storedParticipantSession || "{}");
} catch (error) {
    participantSession = {};
}

if (!participantSession.codigo_partida || !participantSession.codigo_participante) {
    localStorage.removeItem("participantSession");
    window.location.replace("/participante/");
} else {
    initializeParticipantRoom(participantSession);
}

function initializeParticipantRoom(sessionData) {
    const helpers = ParticipantRoomHelpers;
    const socket = io({transports: ["websocket"]});
    const requestButton = document.getElementById("requestWord");
    const statusEl = document.getElementById("participantStatus");
    const stateMessageEl = document.getElementById("participantStateMessage");
    const questionText = document.getElementById("questionText");
    const questionImage = document.getElementById("questionImage");
    const expandQuestionImage = document.getElementById("expandQuestionImage");
    const questionContent = document.getElementById("participantQuestionContent");
    const participantStatePanel = document.getElementById("participantStatePanel");
    const pausedPanel = document.getElementById("participantPausedPanel");
    const rankingEl = document.getElementById("ranking");
    const finalActions = document.getElementById("finalActions");
    const teamScore = document.getElementById("teamScore");
    const podiumTitle = document.getElementById("podiumTitle");
    const participantTimerStack = document.getElementById("participantTimerStack");
    const connectionStatusEl = document.getElementById("connectionStatus");
    const participantNotice = document.getElementById("participantNotice");
    const connectAnotherRoom = document.getElementById("connectAnotherRoom");
    const modalElement = document.getElementById("participantImageModal");
    const modalImage = document.getElementById("participantImageModalContent");
    const modalQuestionText = document.getElementById("participantImageModalLabel");
    const participantImageModal = bootstrap.Modal.getOrCreateInstance(modalElement);
    let hasRequestedForQuestion = false;
    let hasAnsweredForQuestion = false;
    let lastAnswerCorrect = null;
    let participantQuestionId = null;
    let participantPaused = false;
    let participantTransitionBlocked = true;
    let participantRequestStatus = "";
    let currentParticipantQuestion = null;
    let currentGameState = "";
    let currentCompetitionState = "Sala abierta";
    let currentCompetitionMessage = "Esperando que el juez inicie la competencia.";
    let currentTimerExhausted = false;
    let wordRequestInFlight = false;
    let requestStateRebuildPending = false;
    let currentPresentation = null;
    let noticeTimer = null;
    let participantPodiumState = {estado: "OCULTO", revision: 0};
    let participantPodiumHydrated = false;
    let participantFinalRanking = {ranking: []};
    let participantPodiumCelebrated = false;

    document.getElementById("teamName").textContent = sessionData.nombre_equipo || "Equipo";
    document.getElementById("roomCode").textContent = sessionData.codigo_partida || "";

    const connectionController = helpers.bindConnectionStatus(socket, {
        onStatus(message, tone) {
            connectionStatusEl.textContent = message;
            connectionStatusEl.classList.remove(
                "is-connected",
                "is-reconnecting",
                "is-recovered"
            );
            connectionStatusEl.classList.add(`is-${tone}`);
        }
    });

    const joinMessage = sessionStorage.getItem("participantJoinMessage");

    if (joinMessage) {
        participantNotice.textContent = joinMessage;
        participantNotice.classList.remove("d-none");
        sessionStorage.removeItem("participantJoinMessage");
        noticeTimer = window.setTimeout(() => {
            participantNotice.classList.add("d-none");
            noticeTimer = null;
        }, 4000);
    }

    socket.on("connect", () => {
        socket.emit("participante_reconectar", sessionData);
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

    function setParticipantState(status, message) {
        statusEl.textContent = status || "Sala abierta";
        stateMessageEl.textContent = message || "Esperando que el juez inicie la competencia.";
    }

    function ownWordRequest(requests = []) {
        return (requests || []).find(
            item => item.codigo_participante === sessionData.codigo_participante
        );
    }

    function closeParticipantQuestionModal() {
        participantImageModal.hide();
        modalImage.removeAttribute("src");
        modalQuestionText.textContent = "Pregunta actual";
    }

    function renderParticipantQuestion(question) {
        currentParticipantQuestion = question || null;

        if (!question) {
            questionText.textContent = "Esperando la siguiente pregunta.";
            questionImage.removeAttribute("src");
            expandQuestionImage.classList.add("d-none");
            return;
        }

        questionText.textContent = question.enunciado || "Pregunta actual";

        if (question.imagen) {
            questionImage.src = question.imagen;
            expandQuestionImage.classList.remove("d-none");
        } else {
            questionImage.removeAttribute("src");
            expandQuestionImage.classList.add("d-none");
        }
    }

    function syncParticipantQuestion(question, ownRequest = null) {
        const transition = helpers.participantQuestionTransition(
            participantQuestionId,
            question
        );

        if (transition.changed) {
            closeParticipantQuestionModal();
        }

        if (transition.isNewQuestion) {
            participantQuestionId = transition.nextQuestionId;
            hasRequestedForQuestion = false;
            hasAnsweredForQuestion = false;
            lastAnswerCorrect = null;
            participantRequestStatus = "";
            wordRequestInFlight = false;
        }

        if (question) {
            renderParticipantQuestion(question);
        }

        if (ownRequest) {
            participantRequestStatus = ownRequest.estado || "";
            hasRequestedForQuestion = true;
            hasAnsweredForQuestion = ["CORRECTA", "INCORRECTA"].includes(
                participantRequestStatus
            );

            if (hasAnsweredForQuestion) {
                lastAnswerCorrect = participantRequestStatus === "CORRECTA";
            }
        }
    }

    function updateParticipantPresentation() {
        currentPresentation = helpers.participantPresentation({
            question: currentParticipantQuestion,
            gameState: currentGameState,
            competitionState: currentCompetitionState,
            competitionMessage: currentCompetitionMessage,
            ownRequestStatus: participantRequestStatus,
            hasRequested: hasRequestedForQuestion,
            hasAnswered: hasAnsweredForQuestion,
            lastAnswerCorrect,
            timerExhausted: currentTimerExhausted,
            transitionBlocked: participantTransitionBlocked,
            paused: participantPaused
        });

        questionContent.classList.toggle("d-none", !currentPresentation.showQuestion);
        requestButton.disabled = !currentPresentation.requestEnabled;
        setParticipantState(currentPresentation.status, currentPresentation.message);
        return currentPresentation;
    }

    function showParticipantPaused() {
        participantPaused = true;
        participantTransitionBlocked = true;
        document.querySelector(".participant-view")?.classList.add("is-paused");
        pausedPanel.classList.remove("d-none");
        questionContent.classList.add("d-none");
        participantStatePanel.classList.add("d-none");
        requestButton.disabled = true;
        requestButton.classList.add("d-none");
        finalActions.classList.add("d-none");
        podiumTitle.classList.add("d-none");
        closeParticipantQuestionModal();
        questionImage.removeAttribute("src");
    }

    function leaveParticipantPaused() {
        participantPaused = false;
        document.querySelector(".participant-view")?.classList.remove("is-paused");
        pausedPanel.classList.add("d-none");
        participantStatePanel.classList.remove("d-none");
        requestButton.classList.remove("d-none");
    }

    function showFinalPodium(rankingData) {
        const ranking = rankingData?.ranking || [];
        const own = ranking.find(
            item => item.participant_code === sessionData.codigo_participante
        );

        closeParticipantQuestionModal();
        leaveParticipantPaused();
        currentGameState = "FINALIZADA";
        participantTransitionBlocked = true;
        document.querySelector(".participant-view")?.classList.add("podium-mode");
        participantTimerStack.setAttribute("aria-hidden", "true");
        requestButton.classList.add("d-none");
        requestButton.disabled = true;
        finalActions.classList.remove("d-none");
        podiumTitle.classList.remove("d-none");
        participantFinalRanking = rankingData || participantFinalRanking;
        teamScore.textContent = own
            ? `Puntaje de tu equipo: ${own.puntaje} pts`
            : "Puntaje final disponible en el marcador.";
        renderSynchronizedPodium(
            rankingEl,
            participantFinalRanking,
            participantPodiumState,
            {animate: false}
        );
    }

    function applyParticipantPodiumState(payload) {
        if (!payload || !PODIUM_STATE_ORDER.includes(payload.estado)) {
            return;
        }

        if (
                payload.codigo_partida
                && payload.codigo_partida !== sessionData.codigo_partida
        ) {
            return;
        }

        const previous = participantPodiumState;
        const changedRevision = (
            participantPodiumHydrated
            && Number(payload.revision) > Number(previous.revision)
        );
        const celebrate = (
            changedRevision
            && !participantPodiumCelebrated
            && ["PRIMER_LUGAR", "COMPLETO"].includes(payload.estado)
        );

        if (payload.estado === "OCULTO" && Number(payload.revision) === 0) {
            participantPodiumCelebrated = false;
        } else if (celebrate) {
            participantPodiumCelebrated = true;
        }

        participantPodiumState = payload;
        participantPodiumHydrated = true;

        if (currentGameState === "FINALIZADA") {
            renderSynchronizedPodium(
                rankingEl,
                participantFinalRanking,
                participantPodiumState,
                {animate: changedRevision, celebrate}
            );
        }
    }

    function resetFinalView() {
        document.querySelector(".participant-view")?.classList.remove("podium-mode");
        participantTimerStack.removeAttribute("aria-hidden");
        rankingEl.querySelector(".final-podium-view")?.classList.remove(
            "podium-celebrating"
        );
        finalActions.classList.add("d-none");
        podiumTitle.classList.add("d-none");
    }

    function sendWordRequest() {
        if (
                participantPaused
                || participantTransitionBlocked
                || wordRequestInFlight
                || hasRequestedForQuestion
                || hasAnsweredForQuestion
                || requestButton.disabled
                || currentPresentation?.requestEnabled !== true
        ) {
            return false;
        }

        playSound("request");
        wordRequestInFlight = true;
        hasRequestedForQuestion = true;
        participantRequestStatus = "";
        updateParticipantPresentation();
        socket.emit("pedir_palabra", sessionData);
        return true;
    }

    requestButton.addEventListener("click", sendWordRequest);

    document.addEventListener("keydown", event => {
        const modalOpen = Boolean(document.querySelector(".modal.show"));
        const useShortcut = helpers.shouldUseRequestShortcut(event, {
            requestAvailable: currentPresentation?.requestEnabled === true,
            requestDisabled: requestButton.disabled,
            paused: participantPaused,
            hasActiveRequest: (
                wordRequestInFlight
                || hasRequestedForQuestion
                || hasAnsweredForQuestion
                || Boolean(participantRequestStatus)
            ),
            transitionBlocked: participantTransitionBlocked,
            modalOpen
        });

        if (!useShortcut) {
            return;
        }

        if (event.key === " " || event.key === "Spacebar" || event.code === "Space") {
            event.preventDefault();
        }

        sendWordRequest();
    });

    expandQuestionImage.addEventListener("click", () => {
        const modalContent = helpers.participantQuestionModalContent(
            currentParticipantQuestion
        );

        if (participantPaused || !modalContent.image) {
            return;
        }

        modalQuestionText.textContent = modalContent.text;
        modalImage.src = modalContent.image;
        participantImageModal.show();
    });

    connectAnotherRoom.addEventListener("click", () => {
        connectionController.markLeaving();

        if (noticeTimer !== null) {
            window.clearTimeout(noticeTimer);
            noticeTimer = null;
        }

        helpers.clearParticipantBrowserState(localStorage, sessionStorage);
        socket.disconnect();
        window.location.replace("/participante/");
    });

    socket.on("estado_sala", state => {
        currentGameState = state.partida?.estado || "";
        currentCompetitionState = state.estado_competencia || "Sala abierta";
        currentCompetitionMessage = state.mensaje_estado || "";
        currentTimerExhausted = state.timer?.exhausted === true;
        renderParticipantTimer(state.timer, state.partida?.tiempo_por_pregunta);
        renderRanking(rankingEl, state.ranking);

        if (currentGameState === "PAUSADA") {
            showParticipantPaused();
            return;
        }

        leaveParticipantPaused();

        if (currentGameState === "FINALIZADA") {
            showFinalPodium(state.ranking);
            return;
        }

        resetFinalView();
        const ownRequest = ownWordRequest(state.solicitudes);
        syncParticipantQuestion(state.pregunta, ownRequest);

        if (requestStateRebuildPending) {
            requestStateRebuildPending = false;

            if (!ownRequest) {
                hasRequestedForQuestion = false;
                hasAnsweredForQuestion = false;
                participantRequestStatus = "";
            }
        }

        participantTransitionBlocked = !state.pregunta;
        updateParticipantPresentation();
    });

    socket.on("mostrar_pregunta", question => {
        if (participantPaused) {
            return;
        }

        if (Number(question?.numero_orden) === 1) {
            playSound("start");
        }

        resetTimerSound("participant");
        resetFinalView();
        currentGameState = "EN_CURSO";
        currentCompetitionState = "Pregunta en curso";
        currentCompetitionMessage = "Los equipos pueden pedir la palabra.";
        currentTimerExhausted = false;
        participantTransitionBlocked = false;
        syncParticipantQuestion(question);
        updateParticipantPresentation();
    });

    socket.on("estado_competencia", event => {
        if (participantPaused && event.estado !== "Competencia finalizada") {
            return;
        }

        if (event.contador === 5) {
            playSound("countdown");
        }

        currentCompetitionState = event.estado || currentCompetitionState;
        currentCompetitionMessage = event.mensaje || currentCompetitionMessage;
        participantTransitionBlocked = ![
            "Pregunta en curso",
            "Esperando respuesta"
        ].includes(currentCompetitionState);

        if (currentCompetitionState === "Competencia finalizada") {
            currentGameState = "FINALIZADA";
            requestButton.disabled = true;
            closeParticipantQuestionModal();
        }

        updateParticipantPresentation();
    });

    socket.on("actualizar_cronometro", timer => {
        if (participantPaused) {
            return;
        }

        renderParticipantTimer(timer);
        currentTimerExhausted = timer?.exhausted === true;
        updateParticipantPresentation();
    });

    socket.on("habilitar_respuesta", request => {
        if (
                participantPaused
                || request.codigo_participante !== sessionData.codigo_participante
        ) {
            return;
        }

        playSound("turn");
        participantRequestStatus = "EN_TURNO";
        hasRequestedForQuestion = true;
        wordRequestInFlight = false;
        updateParticipantPresentation();
    });

    socket.on("estado_palabra", request => {
        if (participantPaused) {
            return;
        }

        currentCompetitionState = "Esperando respuesta";
        currentCompetitionMessage = "Un equipo tiene la palabra.";
        participantTransitionBlocked = false;
        playSound("turn");

        if (request.codigo_participante === sessionData.codigo_participante) {
            participantRequestStatus = "EN_TURNO";
            hasRequestedForQuestion = true;
            wordRequestInFlight = false;
        }

        updateParticipantPresentation();
    });

    socket.on("resultado_respuesta", payload => {
        if (participantPaused) {
            return;
        }

        const request = payload?.request;

        if (!request || request.codigo_participante !== sessionData.codigo_participante) {
            return;
        }

        const correct = request.estado === "CORRECTA";
        playSound(correct ? "correct" : "incorrect");
        participantRequestStatus = correct ? "CORRECTA" : "INCORRECTA";
        hasRequestedForQuestion = true;
        hasAnsweredForQuestion = true;
        lastAnswerCorrect = correct;
        wordRequestInFlight = false;
        updateParticipantPresentation();
    });

    socket.on("resultado_accion", payload => {
        if (!wordRequestInFlight) {
            return;
        }

        wordRequestInFlight = false;

        if (payload?.success) {
            requestStateRebuildPending = false;
            participantRequestStatus = payload.data?.request?.estado || "EN_COLA";
            hasRequestedForQuestion = true;
            updateParticipantPresentation();
            return;
        }

        requestStateRebuildPending = true;
        participantTransitionBlocked = true;
        updateParticipantPresentation();
        setParticipantState(
            "No se pudo enviar la solicitud",
            payload?.message || "Inténtalo nuevamente cuando el botón esté disponible."
        );
        socket.emit("participante_reconectar", sessionData);
    });

    socket.on("actualizar_puntajes", ranking => {
        if (currentGameState === "FINALIZADA") {
            participantFinalRanking = ranking || participantFinalRanking;
            renderSynchronizedPodium(
                rankingEl,
                participantFinalRanking,
                participantPodiumState,
                {animate: false}
            );
            return;
        }

        renderRanking(rankingEl, ranking);
    });

    socket.on("mostrar_podio", ranking => {
        playSound("finish");
        showFinalPodium(ranking);
    });

    socket.on("estado_podio", payload => {
        applyParticipantPodiumState(payload);
    });

    socket.on("participante_eliminado", payload => {
        connectionController.markLeaving();
        helpers.clearParticipantBrowserState(localStorage, sessionStorage);
        const message = payload?.message || "El juez eliminó este equipo de la sala de espera.";
        sessionStorage.setItem("participantRemovalMessage", message);
        socket.disconnect();
        window.location.replace("/participante/?equipo_eliminado=1");
    });

}
