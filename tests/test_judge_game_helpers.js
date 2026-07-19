const test = require("node:test");
const assert = require("node:assert/strict");

const {
    activeRoomCode,
    activeRoomName,
    activeQuestionnaires,
    activeWordRequests,
    competitionControlState,
    filterActiveQuestionnaires,
    gameActionLabel,
    nextQuestionAction,
    questionnaireSelectionState,
    teamSiteIdentity
} = require("../static/js/judge_game_helpers.js");

function request(id, status, order = id) {
    return {
        id_solicitud: id,
        id_partida_pregunta: 10,
        orden_solicitud: order,
        estado: status
    };
}

const questionnaires = [
    {
        id_cuestionario: 1,
        nombre: "Aritmética Primaria",
        materia: {nombre: "Matemática"},
        area: "Primaria",
        estado: "ACTIVO"
    },
    {
        id_cuestionario: 2,
        nombre: "Geometría Primaria",
        materia: {nombre: "Matemática"},
        area: "Primaria",
        estado: "ACTIVO"
    },
    {
        id_cuestionario: 3,
        nombre: "Álgebra Básicos",
        materia: {nombre: "Matemática"},
        area: "Básicos",
        estado: "ACTIVO"
    },
    {
        id_cuestionario: 4,
        nombre: "Borrador",
        materia: {nombre: "Ciencias"},
        area: "Primaria",
        estado: "BORRADOR"
    }
];

test("solo ofrece cuestionarios activos", () => {
    assert.deepEqual(
        activeQuestionnaires(questionnaires).map(item => item.id_cuestionario),
        [1, 2, 3]
    );
});

test("mantiene solo solicitudes activas, sin duplicados y en orden", () => {
    const active = activeWordRequests([
        request(3, "EN_COLA", 3),
        request(1, "INCORRECTA", 1),
        request(2, "EN_TURNO", 2),
        request(2, "EN_TURNO", 2),
        request(4, "CANCELADA", 4)
    ]);

    assert.deepEqual(active.map(item => item.id_solicitud), [2, 3]);
});

test("una secuencia A, B, C incorrecta nunca reincorpora solicitudes resueltas", () => {
    const initial = activeWordRequests([
        request(1, "EN_TURNO"),
        request(2, "EN_COLA"),
        request(3, "EN_COLA")
    ]);
    const afterA = activeWordRequests([
        request(1, "INCORRECTA"),
        request(2, "EN_TURNO"),
        request(3, "EN_COLA")
    ]);
    const afterB = activeWordRequests([
        request(1, "INCORRECTA"),
        request(2, "INCORRECTA"),
        request(3, "EN_TURNO")
    ]);
    const afterC = activeWordRequests([
        request(1, "INCORRECTA"),
        request(2, "INCORRECTA"),
        request(3, "INCORRECTA")
    ]);

    assert.deepEqual(initial.map(item => item.id_solicitud), [1, 2, 3]);
    assert.deepEqual(afterA.map(item => item.id_solicitud), [2, 3]);
    assert.equal(afterA[0].estado, "EN_TURNO");
    assert.deepEqual(afterB.map(item => item.id_solicitud), [3]);
    assert.equal(afterB[0].estado, "EN_TURNO");
    assert.deepEqual(afterC, []);
});

test("una respuesta correcta conserva el cierre de la cola activa", () => {
    const closed = activeWordRequests([
        request(1, "CORRECTA"),
        request(2, "CANCELADA"),
        request(3, "CANCELADA")
    ]);

    assert.deepEqual(closed, []);
});

test("mantiene una multiselección aunque el filtro oculte elementos", () => {
    const selected = new Set(["1", "3"]);
    const filtered = filterActiveQuestionnaires(questionnaires, "álgebra");
    const state = questionnaireSelectionState(questionnaires, selected);

    assert.deepEqual(filtered.map(item => item.id_cuestionario), [3]);
    assert.equal(state.selectedCount, 2);
    assert.deepEqual(state.selected.map(item => item.id_cuestionario), [1, 3]);
});

test("infiere el área cuando todos los cuestionarios coinciden", () => {
    const state = questionnaireSelectionState(questionnaires, new Set(["1", "2"]));

    assert.equal(state.area, "Primaria");
    assert.equal(state.inferred, true);
    assert.equal(state.requiresManualArea, false);
});

test("una selección mixta requiere área manual", () => {
    const state = questionnaireSelectionState(questionnaires, new Set(["1", "3"]));

    assert.equal(state.area, "");
    assert.equal(state.inferred, false);
    assert.equal(state.requiresManualArea, true);
});

test("un área manual no se sobrescribe al cambiar cuestionarios", () => {
    const state = questionnaireSelectionState(
        questionnaires,
        new Set(["1", "2"]),
        true,
        "Diversificado"
    );

    assert.equal(state.area, "Diversificado");
    assert.equal(state.inferred, false);
    assert.equal(state.requiresManualArea, false);
});

test("vuelve a inferir al regresar a un área única sin selección manual", () => {
    const state = questionnaireSelectionState(questionnaires, new Set(["3"]));

    assert.equal(state.area, "Básicos");
    assert.equal(state.inferred, true);
});

test("volver del área manual a vacío reactiva la inferencia", () => {
    const manual = questionnaireSelectionState(
        questionnaires,
        new Set(["1", "2"]),
        true,
        "Diversificado"
    );
    const automatic = questionnaireSelectionState(
        questionnaires,
        new Set(["1", "2"]),
        false,
        ""
    );

    assert.equal(manual.area, "Diversificado");
    assert.equal(automatic.area, "Primaria");
    assert.equal(automatic.inferred, true);
});

test("volver a automático conserva vacía una selección mixta o inexistente", () => {
    const mixed = questionnaireSelectionState(
        questionnaires,
        new Set(["1", "3"]),
        false,
        ""
    );
    const empty = questionnaireSelectionState(
        questionnaires,
        new Set(),
        false,
        ""
    );

    assert.equal(mixed.area, "");
    assert.equal(mixed.requiresManualArea, true);
    assert.equal(empty.area, "");
    assert.equal(empty.requiresManualArea, false);
    assert.equal(empty.inferred, false);
});

test("decide el flujo exacto de siguiente pregunta", () => {
    assert.equal(nextQuestionAction({
        gameState: "EN_CURSO",
        remaining: 12,
        currentQuestion: 1,
        totalQuestions: 3
    }), "finish_time");
    assert.equal(nextQuestionAction({
        gameState: "EN_CURSO",
        remaining: 0,
        currentQuestion: 1,
        totalQuestions: 3
    }), "advance");
    assert.equal(nextQuestionAction({
        gameState: "EN_CURSO",
        remaining: 0,
        currentQuestion: 3,
        totalQuestions: 3
    }), "finish_game");
    assert.equal(nextQuestionAction({
        gameState: "FINALIZADA",
        remaining: 0,
        currentQuestion: 3,
        totalQuestions: 3
    }), "blocked");
    assert.equal(nextQuestionAction({
        gameState: "EN_CURSO",
        remaining: 0,
        currentQuestion: 1,
        totalQuestions: 3,
        transitionActive: true
    }), "blocked");
});

test("solo permite pausar una pregunta activa fuera de la precuenta", () => {
    const active = competitionControlState({
        gameState: "EN_CURSO",
        hasQuestion: true,
        questionState: "ACTUAL",
        remaining: 16
    });
    const countdown = competitionControlState({
        gameState: "EN_CURSO",
        hasQuestion: true,
        questionState: "ACTUAL",
        remaining: 16,
        transitionActive: true
    });
    const exhausted = competitionControlState({
        gameState: "EN_CURSO",
        hasQuestion: true,
        questionState: "ACTUAL",
        remaining: 0
    });

    assert.equal(active.pauseResumeAction, "pause");
    assert.equal(active.showPauseResume, true);
    assert.equal(countdown.pauseResumeAction, "blocked");
    assert.equal(countdown.showPauseResume, false);
    assert.equal(exhausted.pauseResumeAction, "blocked");
    assert.equal(exhausted.showPauseResume, false);
});

test("durante PAUSADA solo conserva Reanudar y Finalizar como controles activos", () => {
    const paused = competitionControlState({
        gameState: "PAUSADA",
        hasQuestion: true,
        questionState: "ACTUAL",
        remaining: 18
    });

    assert.equal(paused.pauseResumeAction, "resume");
    assert.equal(paused.showPauseResume, true);
    assert.equal(paused.canFinish, true);
    assert.equal(paused.canNext, false);
    assert.equal(paused.canModifyQuestion, false);
});

test("el bloqueo pendiente evita doble Pausar o doble Reanudar", () => {
    const pausing = competitionControlState({
        gameState: "EN_CURSO",
        hasQuestion: true,
        questionState: "ACTUAL",
        remaining: 18,
        pendingAction: "pause"
    });
    const resuming = competitionControlState({
        gameState: "PAUSADA",
        hasQuestion: true,
        questionState: "ACTUAL",
        remaining: 18,
        pendingAction: "resume"
    });

    assert.equal(pausing.pauseResumeAction, "blocked");
    assert.equal(resuming.pauseResumeAction, "blocked");
    assert.equal(pausing.canModifyQuestion, false);
    assert.equal(resuming.canFinish, false);
});

test("presenta la acción principal según el estado", () => {
    assert.equal(gameActionLabel("ESPERANDO"), "Abrir sala");
    assert.equal(gameActionLabel("EN_CURSO"), "Volver a competencia");
    assert.equal(gameActionLabel("PAUSADA"), "Volver a competencia");
    assert.equal(gameActionLabel("FINALIZADA"), "Ver resultados");
});

test("obtiene el código visible únicamente de la sala activa", () => {
    for (const estado of ["ESPERANDO", "EN_CURSO", "PAUSADA"]) {
        assert.equal(activeRoomCode({codigo_partida: " abc123 ", estado}), "ABC123");
    }

    assert.equal(activeRoomCode({codigo_partida: "xyz789", estado: "EN_CURSO"}), "XYZ789");
    assert.equal(activeRoomCode({estado: "EN_CURSO"}), "");
    assert.equal(activeRoomCode(null), "");
});

test("obtiene y limpia el nombre visible de la sala activa", () => {
    assert.equal(activeRoomName({nombre: " Sala A "}), "Sala A");
    assert.equal(activeRoomName({nombre: "Sala B"}), "Sala B");
    assert.equal(activeRoomName({nombre: ""}), "Competencia");
    assert.equal(activeRoomName(null), "Competencia");
});

test("centraliza la identidad visual de todas las sedes", () => {
    assert.equal(teamSiteIdentity("Petapa").key, "petapa");
    assert.equal(teamSiteIdentity("Villa Nueva").key, "villa-nueva");
    assert.equal(teamSiteIdentity("San Cristóbal").key, "san-cristobal");
    assert.equal(teamSiteIdentity("Antigua").key, "antigua");
    assert.equal(teamSiteIdentity("Naranjo").key, "naranjo");
    assert.equal(teamSiteIdentity("Aguilar Batres").key, "aguilar-batres");
    assert.equal(teamSiteIdentity("San Juan").key, "san-juan");
    assert.equal(teamSiteIdentity("Amatitlán").key, "amatitlan");
    assert.equal(teamSiteIdentity("Sede futura").key, "default");
});
