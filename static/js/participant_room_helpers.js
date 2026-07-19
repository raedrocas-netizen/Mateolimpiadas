(function (root, factory) {
    const helpers = factory(root);

    if (typeof module === "object" && module.exports) {
        module.exports = helpers;
    }

    root.ParticipantRoomHelpers = helpers;
}(typeof globalThis !== "undefined" ? globalThis : this, function (root) {
    const ANSWERED_REQUEST_STATES = new Set(["CORRECTA", "INCORRECTA"]);
    const connectionBindings = new WeakMap();

    function participantQuestionTransition(currentQuestionId, nextQuestion) {
        const nextQuestionId = nextQuestion?.id_partida_pregunta ?? null;
        const hasCurrentQuestion = currentQuestionId !== null
            && currentQuestionId !== undefined
            && String(currentQuestionId) !== "";
        const hasNextQuestion = nextQuestionId !== null
            && nextQuestionId !== undefined
            && String(nextQuestionId) !== "";
        const differentQuestion = hasCurrentQuestion
            && hasNextQuestion
            && String(currentQuestionId) !== String(nextQuestionId);

        return {
            changed: differentQuestion,
            isNewQuestion: hasNextQuestion && (!hasCurrentQuestion || differentQuestion),
            nextQuestionId
        };
    }

    function participantQuestionModalContent(question) {
        return {
            text: String(question?.enunciado || "Pregunta actual"),
            image: String(question?.imagen || "")
        };
    }

    function participantPresentation(options = {}) {
        const gameState = options.gameState || "";
        const competitionState = options.competitionState || "";
        const competitionMessage = options.competitionMessage || "";
        const ownRequestStatus = options.ownRequestStatus || "";
        const paused = gameState === "PAUSADA" || options.paused === true;
        const finished = gameState === "FINALIZADA";
        const hasQuestion = Boolean(options.question);
        const hasRequested = options.hasRequested === true || Boolean(ownRequestStatus);
        const hasAnswered = options.hasAnswered === true
            || ANSWERED_REQUEST_STATES.has(ownRequestStatus);
        const timerExhausted = options.timerExhausted === true;
        const transitionBlocked = options.transitionBlocked === true;
        const showQuestion = hasQuestion && !paused && !finished;
        const questionState = options.question?.estado
            || options.question?.estado_partida_pregunta
            || "";
        const questionIsActive = questionState === "ACTUAL";
        let status = competitionState || "Sala abierta";
        let message = competitionMessage || "Esperando que el juez inicie la competencia.";

        if (paused) {
            return {
                showQuestion: false,
                requestEnabled: false,
                status: "PARTIDA PAUSADA",
                message: "Espera a que el juez reanude la partida."
            };
        }

        if (finished) {
            return {
                showQuestion: false,
                requestEnabled: false,
                status: "Competencia finalizada",
                message: "La competencia ha terminado."
            };
        }

        if (ownRequestStatus === "EN_TURNO") {
            status = "¡Es tu turno!";
            message = "Tu equipo tiene la palabra.";
        } else if (ownRequestStatus === "EN_COLA") {
            status = "Solicitud enviada";
            message = "Estás en la cola de solicitudes.";
        } else if (ownRequestStatus === "CORRECTA") {
            status = "Respuesta correcta";
            message = "Puntaje actualizado. Esperando la siguiente pregunta.";
        } else if (ownRequestStatus === "INCORRECTA") {
            status = "Respuesta incorrecta";
            message = "Esperando la siguiente pregunta.";
        } else if (ownRequestStatus === "CANCELADA") {
            status = "Pregunta resuelta";
            message = "Esperando la siguiente pregunta.";
        } else if (hasAnswered) {
            status = options.lastAnswerCorrect === true
                ? "Respuesta correcta"
                : "Respuesta incorrecta";
            message = "Esperando la siguiente pregunta.";
        } else if (hasRequested) {
            status = "Solicitud enviada";
            message = "Solicitud enviada. Esperando turno.";
        } else if (timerExhausted) {
            status = "Tiempo agotado";
            message = "Esperando la siguiente pregunta.";
        } else if (competitionState === "Esperando respuesta") {
            status = "Otro equipo está respondiendo";
            message = "Puedes pedir la palabra si aún no estás en la cola.";
        } else if (questionIsActive && !transitionBlocked) {
            status = "Disponible";
            message = "Pide la palabra cuando estés listo.";
        }

        return {
            showQuestion,
            requestEnabled: (
                gameState === "EN_CURSO"
                && showQuestion
                && questionIsActive
                && !hasRequested
                && !hasAnswered
                && !timerExhausted
                && !transitionBlocked
            ),
            status,
            message
        };
    }

    function isEditableTarget(target) {
        if (!target) {
            return false;
        }

        const tagName = String(target.tagName || "").toLowerCase();

        if (["input", "textarea", "select"].includes(tagName) || target.isContentEditable) {
            return true;
        }

        return Boolean(
            typeof target.closest === "function"
            && target.closest("[contenteditable=''], [contenteditable='true']")
        );
    }

    function isRequestShortcut(event) {
        return event?.key === "Enter"
            || event?.key === " "
            || event?.key === "Spacebar"
            || event?.code === "Space";
    }

    function shouldUseRequestShortcut(event, options = {}) {
        return Boolean(
            isRequestShortcut(event)
            && event.repeat !== true
            && options.requestAvailable === true
            && options.requestDisabled !== true
            && options.paused !== true
            && options.hasActiveRequest !== true
            && options.transitionBlocked !== true
            && options.modalOpen !== true
            && !isEditableTarget(event.target)
        );
    }

    function clearParticipantBrowserState(localStore, sessionStore) {
        localStore?.removeItem("participantSession");
        sessionStore?.removeItem("participantJoinMessage");
        sessionStore?.removeItem("participantRemovalMessage");
    }

    function bindConnectionStatus(socket, options = {}) {
        if (connectionBindings.has(socket)) {
            return connectionBindings.get(socket);
        }

        const onStatus = options.onStatus || function () {};
        const schedule = options.schedule || function (callback, milliseconds) {
            return root.setTimeout(callback, milliseconds);
        };
        const cancelSchedule = options.cancelSchedule || function (timer) {
            root.clearTimeout(timer);
        };
        let connectedOnce = false;
        let leaving = false;
        let recoveryTimer = null;

        function clearRecoveryTimer() {
            if (recoveryTimer !== null) {
                cancelSchedule(recoveryTimer);
                recoveryTimer = null;
            }
        }

        function showConnected() {
            clearRecoveryTimer();

            if (!connectedOnce) {
                connectedOnce = true;
                onStatus("Conectado", "connected");
                return;
            }

            onStatus("Conexión recuperada", "recovered");
            recoveryTimer = schedule(function () {
                recoveryTimer = null;
                onStatus("Conectado", "connected");
            }, 2500);
        }

        function showReconnecting() {
            if (leaving) {
                return;
            }

            clearRecoveryTimer();
            onStatus("Reconectando...", "reconnecting");
        }

        socket.on("connect", showConnected);
        socket.on("disconnect", showReconnecting);
        socket.on("connect_error", showReconnecting);
        socket.io?.on("reconnect_attempt", showReconnecting);

        const controller = {
            markLeaving() {
                leaving = true;
                clearRecoveryTimer();
            }
        };
        connectionBindings.set(socket, controller);
        return controller;
    }

    return {
        bindConnectionStatus,
        clearParticipantBrowserState,
        isEditableTarget,
        participantPresentation,
        participantQuestionModalContent,
        participantQuestionTransition,
        shouldUseRequestShortcut
    };
}));
