const test = require("node:test");
const assert = require("node:assert/strict");

const {
    bindConnectionStatus,
    clearParticipantBrowserState,
    participantPresentation,
    participantQuestionModalContent,
    participantQuestionTransition,
    shouldUseRequestShortcut
} = require("../static/js/participant_room_helpers.js");

const question = {
    id_partida_pregunta: 10,
    estado: "ACTUAL",
    enunciado: "¿Cuál es el resultado?",
    imagen: "/static/img/pregunta.png"
};

function presentation(overrides = {}) {
    return participantPresentation({
        question,
        gameState: "EN_CURSO",
        competitionState: "Pregunta en curso",
        competitionMessage: "Los equipos pueden pedir la palabra.",
        ...overrides
    });
}

test("mantiene visible la misma pregunta durante todos los estados del participante", () => {
    const cases = [
        {hasRequested: true},
        {ownRequestStatus: "EN_COLA"},
        {ownRequestStatus: "EN_TURNO", competitionState: "Esperando respuesta"},
        {ownRequestStatus: "CORRECTA"},
        {ownRequestStatus: "INCORRECTA"},
        {timerExhausted: true}
    ];

    for (const state of cases) {
        assert.equal(presentation(state).showQuestion, true);
        assert.equal(question.enunciado, "¿Cuál es el resultado?");
        assert.equal(question.imagen, "/static/img/pregunta.png");
    }
});

test("PAUSADA oculta la pregunta y reanudar muestra la misma pregunta", () => {
    assert.equal(presentation({gameState: "PAUSADA"}).showQuestion, false);
    assert.equal(presentation({gameState: "PAUSADA"}).requestEnabled, false);
    assert.equal(presentation().showQuestion, true);
    assert.equal(presentation().requestEnabled, true);
});

test("cierra la imagen ampliada solo ante un cambio real de pregunta", () => {
    const firstQuestion = participantQuestionTransition(null, question);
    const sameQuestion = participantQuestionTransition(10, {
        ...question,
        estado_participante: "EN_COLA"
    });
    const sameQuestionInTurn = participantQuestionTransition(10, {
        ...question,
        estado_participante: "EN_TURNO"
    });
    const nextQuestion = participantQuestionTransition(10, {
        ...question,
        id_partida_pregunta: 11,
        enunciado: "Pregunta B"
    });

    assert.equal(firstQuestion.changed, false);
    assert.equal(firstQuestion.isNewQuestion, true);
    assert.equal(sameQuestion.changed, false);
    assert.equal(sameQuestionInTurn.changed, false);
    assert.equal(nextQuestion.changed, true);
    assert.equal(nextQuestion.nextQuestionId, 11);
});

test("el modal usa solo el texto y la imagen públicos de la pregunta actual", () => {
    const questionA = participantQuestionModalContent({
        ...question,
        respuesta_correcta: "Dato privado",
        imagen_respuesta: "/static/img/respuesta.png"
    });
    const questionB = participantQuestionModalContent({
        ...question,
        id_partida_pregunta: 11,
        enunciado: "Texto de la pregunta B",
        imagen: "/static/img/pregunta-b.png"
    });

    assert.deepEqual(questionA, {
        text: question.enunciado,
        image: question.imagen
    });
    assert.deepEqual(questionB, {
        text: "Texto de la pregunta B",
        image: "/static/img/pregunta-b.png"
    });
    assert.equal(JSON.stringify(questionA).includes("Dato privado"), false);
    assert.equal(JSON.stringify(questionA).includes("respuesta.png"), false);
});

test("presenta mensajes humanos para cola, turno, correcta e incorrecta", () => {
    assert.equal(presentation({ownRequestStatus: "EN_COLA"}).message, "Estás en la cola de solicitudes.");
    assert.equal(presentation({ownRequestStatus: "EN_TURNO"}).status, "¡Es tu turno!");
    assert.equal(presentation({ownRequestStatus: "CORRECTA"}).status, "Respuesta correcta");
    assert.equal(presentation({ownRequestStatus: "INCORRECTA"}).status, "Respuesta incorrecta");
});

function keyEvent(key, target = {tagName: "BODY"}, overrides = {}) {
    return {
        key,
        code: key === " " ? "Space" : "",
        repeat: false,
        target,
        ...overrides
    };
}

function shortcutOptions(overrides = {}) {
    return {
        requestAvailable: true,
        requestDisabled: false,
        paused: false,
        hasActiveRequest: false,
        transitionBlocked: false,
        modalOpen: false,
        ...overrides
    };
}

test("Espacio y Enter activan el mismo atajo solo cuando Pedir palabra está disponible", () => {
    assert.equal(shouldUseRequestShortcut(keyEvent(" "), shortcutOptions()), true);
    assert.equal(shouldUseRequestShortcut(keyEvent("Enter"), shortcutOptions()), true);
    assert.equal(
        shouldUseRequestShortcut(keyEvent(" ", {tagName: "BODY"}, {repeat: true}), shortcutOptions()),
        false
    );
    assert.equal(shouldUseRequestShortcut(keyEvent("Enter"), shortcutOptions({requestDisabled: true})), false);
    assert.equal(shouldUseRequestShortcut(keyEvent("Enter"), shortcutOptions({hasActiveRequest: true})), false);
    assert.equal(shouldUseRequestShortcut(keyEvent("Enter"), shortcutOptions({transitionBlocked: true})), false);
    assert.equal(shouldUseRequestShortcut(keyEvent(" "), shortcutOptions({paused: true})), false);
    assert.equal(shouldUseRequestShortcut(keyEvent("Enter"), shortcutOptions({modalOpen: true})), false);
});

test("Espacio y Enter respetan campos editables y contenteditable", () => {
    for (const tagName of ["INPUT", "TEXTAREA", "SELECT"]) {
        assert.equal(
            shouldUseRequestShortcut(keyEvent("Enter", {tagName}), shortcutOptions()),
            false
        );
    }

    assert.equal(
        shouldUseRequestShortcut(
            keyEvent(" ", {tagName: "DIV", isContentEditable: true}),
            shortcutOptions()
        ),
        false
    );
});

test("limpia solo la asociación local de la participación", () => {
    const localValues = new Map([
        ["participantSession", "sesión"],
        ["preferenciaVisual", "alto-contraste"]
    ]);
    const sessionValues = new Map([
        ["participantJoinMessage", "mensaje"],
        ["participantRemovalMessage", "mensaje"],
        ["otraClave", "conservar"]
    ]);
    const storage = values => ({
        removeItem(key) {
            values.delete(key);
        }
    });

    clearParticipantBrowserState(storage(localValues), storage(sessionValues));

    assert.equal(localValues.has("participantSession"), false);
    assert.equal(localValues.get("preferenciaVisual"), "alto-contraste");
    assert.equal(sessionValues.has("participantJoinMessage"), false);
    assert.equal(sessionValues.has("participantRemovalMessage"), false);
    assert.equal(sessionValues.get("otraClave"), "conservar");
});

test("los listeners de conexión se registran una sola vez", () => {
    const socketHandlers = new Map();
    const managerHandlers = new Map();
    const socket = {
        io: {
            on(event, handler) {
                const handlers = managerHandlers.get(event) || [];
                handlers.push(handler);
                managerHandlers.set(event, handlers);
            }
        },
        on(event, handler) {
            const handlers = socketHandlers.get(event) || [];
            handlers.push(handler);
            socketHandlers.set(event, handlers);
        }
    };
    const statuses = [];
    const scheduled = [];
    const options = {
        onStatus(message) {
            statuses.push(message);
        },
        schedule(callback) {
            scheduled.push(callback);
            return scheduled.length;
        },
        cancelSchedule() {}
    };

    const first = bindConnectionStatus(socket, options);
    const second = bindConnectionStatus(socket, options);

    assert.equal(first, second);
    assert.equal(socketHandlers.get("connect").length, 1);
    assert.equal(socketHandlers.get("disconnect").length, 1);
    assert.equal(socketHandlers.get("connect_error").length, 1);
    assert.equal(managerHandlers.get("reconnect_attempt").length, 1);

    socketHandlers.get("connect")[0]();
    socketHandlers.get("disconnect")[0]();
    socketHandlers.get("connect")[0]();
    scheduled[0]();

    assert.deepEqual(statuses, [
        "Conectado",
        "Reconectando...",
        "Conexión recuperada",
        "Conectado"
    ]);
});
