const judgeSocket = io({transports: ["websocket"]});
let catalogs = {};
let liveCode = "";
let liveParticipants = [];
let liveRequests = [];
let liveState = {};
let liveQuestionId = null;
let materias = [];
let cuestionarios = [];
let partidas = [];

const $ = selector => document.querySelector(selector);

function optionList(items, valueKey, textKey) {
    return items.map(item => {
        const value = valueKey ? item[valueKey] : item;
        const text = textKey ? item[textKey] : item;
        return `<option value="${escapeHtml(value)}">${escapeHtml(text)}</option>`;
    }).join("");
}

function row(title, subtitle, actions = "") {
    return `<div class="list-row"><div><strong>${escapeHtml(title)}</strong><small>${subtitle}</small></div><div>${actions}</div></div>`;
}

function setMessage(target, message, success = true) {
    if (!target) {
        return;
    }

    target.textContent = message || "";
    target.classList.toggle("text-danger", !success);
    target.classList.toggle("text-success", success);
}

function loadCatalogs() {
    return apiFetch("/api/catalogos").then(data => {
        catalogs = data;
        document.querySelectorAll('select[name="area"]').forEach(select => {
            select.innerHTML = optionList(data.areas);
        });
        document.querySelectorAll('select[name="estado"]').forEach(select => {
            select.innerHTML = optionList(data.estados_cuestionario);
        });
    });
}

function refreshAll() {
    return Promise.all([
        refreshMaterias(),
        refreshCuestionarios(),
        refreshPartidas()
    ]);
}

function refreshMaterias() {
    return apiFetch("/api/materias").then(items => {
        materias = items;
        renderMaterias();
    });
}

function renderMaterias() {
        $("#materiasList").innerHTML = materias.map(item => row(item.nombre, `ID ${item.id_materia}`, `
            <button class="btn btn-sm btn-outline-secondary" onclick="editMateria(${item.id_materia}, '${escapeHtml(item.nombre)}')">Editar</button>
            <button class="btn btn-sm btn-outline-danger" onclick="deleteItem('/api/materias/${item.id_materia}')">Eliminar</button>
        `)).join("");
        document.querySelectorAll('select[name="id_materia"]').forEach(select => {
            select.innerHTML = optionList(materias, "id_materia", "nombre");
        });
}

function refreshCuestionarios() {
    return apiFetch("/api/cuestionarios").then(items => {
        cuestionarios = items;
        renderCuestionarios();
    });
}

function renderCuestionarios() {
        $("#cuestionariosList").innerHTML = cuestionarios.map(item => row(
            item.nombre,
            `${escapeHtml(item.materia?.nombre || "")} - ${escapeHtml(item.area)} - ${escapeHtml(item.estado)}`,
            `<a class="btn btn-sm btn-primary" href="/juez/cuestionario/${item.id_cuestionario}/preguntas">Preguntas</a>
             <button class="btn btn-sm btn-outline-danger" onclick="deleteItem('/api/cuestionarios/${item.id_cuestionario}')">Eliminar</button>`
        )).join("");
        document.querySelectorAll('select[name="id_cuestionario"], select[name="id_cuestionarios"]').forEach(select => {
            select.innerHTML = optionList(cuestionarios, "id_cuestionario", "nombre");
        });
}

function upsertLocal(items, item, key) {
    if (!item || item[key] === undefined || item[key] === null) {
        return items;
    }

    return upsertBy(items, item, key);
}

function upsertPartida(item) {
    if (!item) {
        return;
    }

    const key = item.id_partida ? "id_partida" : "codigo_partida";
    partidas = upsertLocal(partidas, item, key);
}

function refreshPartidas() {
    return apiFetch("/api/partidas").then(items => {
        partidas = items;
        renderPartidas();
    });
}

function renderPartidas() {
        const markup = partidas.map(item => row(
            `${item.codigo_partida} - ${item.nombre}`,
            [
                `Cuestionario: ${escapeHtml(item.cuestionarios || "Sin cuestionario")}`,
                `Materia: ${escapeHtml(item.materias || "Sin materia")}`,
                `Nivel: ${escapeHtml(item.area || "")}`,
                `Estado: ${escapeHtml(item.estado || "")}`,
                `Participantes: ${item.participantes_conectados || 0}/${item.total_participantes || 0}`
            ].join("<br>"),
            `<button class="btn btn-sm btn-primary" onclick="openLive('${item.codigo_partida}')">Abrir</button>`
        )).join("");
        $("#partidasList").innerHTML = markup || "<div class='text-secondary'>No hay partidas creadas.</div>";
        $("#historyList").innerHTML = markup || "<div class='text-secondary'>No hay historial disponible.</div>";
}

function bindForm(selector, url, afterSave = refreshAll) {
    const form = $(selector);
    form.addEventListener("submit", event => {
        event.preventDefault();
        apiFetch(url, {
            method: "POST",
            body: JSON.stringify(formJson(form))
        }).then(() => {
            form.reset();
            afterSave();
        });
    });
}

function deleteItem(url) {
    apiFetch(url, {method: "DELETE"}).then(refreshAll);
}

function editMateria(id, nombre) {
    const form = $("#materiaForm");
    form.id_materia.value = id;
    form.nombre.value = nombre;
}

$("#materiaForm").addEventListener("submit", event => {
    event.preventDefault();
    const form = event.currentTarget;
    const id = form.id_materia.value;
    apiFetch(id ? `/api/materias/${id}` : "/api/materias", {
        method: id ? "PUT" : "POST",
        body: JSON.stringify(formJson(form))
    }).then(payload => {
        if (!payload.success) {
            return;
        }

        materias = upsertLocal(materias, payload.data, "id_materia");
        cuestionarios = cuestionarios.map(item => (
            item.materia?.id_materia === payload.data.id_materia
                ? {...item, materia: payload.data}
                : item
        ));
        renderMaterias();
        renderCuestionarios();
        form.reset();
    });
});

$("#cuestionarioForm").addEventListener("submit", event => {
    event.preventDefault();
    const form = event.currentTarget;

    apiFetch("/api/cuestionarios", {
        method: "POST",
        body: JSON.stringify(formJson(form))
    }).then(payload => {
        if (!payload.success) {
            return;
        }

        cuestionarios = upsertLocal(cuestionarios, payload.data, "id_cuestionario");
        renderCuestionarios();
        form.reset();
    });
});

$("#generateCode").addEventListener("click", () => {
    apiFetch("/api/partidas/generar-codigo").then(payload => {
        $("#partidaForm").codigo_partida.value = payload.data;
    });
});

$("#partidaForm").addEventListener("submit", event => {
    event.preventDefault();
    const data = formJson(event.currentTarget);
    const message = $("#partidaMessage");
    let createdSuccessfully = false;
    data.id_cuestionarios = Array.from(event.currentTarget.id_cuestionarios.selectedOptions).map(option => option.value);
    setMessage(message, "Creando sala...", true);
    apiFetch("/api/partidas", {
        method: "POST",
        body: JSON.stringify(data)
    }).then(payload => {
        if (!payload.success) {
            setMessage(message, payload.message || "No fue posible crear la sala.", false);
            return;
        }

        const createdGame = payload.data || {};
        const roomCode = createdGame.codigo_partida || data.codigo_partida;
        createdSuccessfully = true;

        if (!roomCode) {
            setMessage(message, "Sala creada correctamente. Actualiza el listado si no aparece.", true);
            return;
        }

        setMessage(message, `Sala ${roomCode} creada correctamente.`, true);
        const selectedQuestionnaires = Array.from(event.currentTarget.id_cuestionarios.selectedOptions)
            .map(option => option.textContent)
            .join(", ");
        upsertPartida(
            {
                ...createdGame,
                codigo_partida: roomCode,
                cuestionarios: selectedQuestionnaires,
                materias: createdGame.materias || "",
                participantes_conectados: createdGame.participantes_conectados || 0,
                total_participantes: createdGame.total_participantes || 0
            }
        );
        renderPartidas();
        openLive(roomCode);
        event.currentTarget.reset();
    }).catch(error => {
        if (createdSuccessfully) {
            console.warn("La sala fue creada, pero hubo un detalle al actualizar la interfaz.", error);
            setMessage(message, "Sala creada correctamente.", true);
            return;
        }

        setMessage(message, "No fue posible crear la sala. Revise la informacion ingresada.", false);
    });
});

function openLive(code) {
    liveCode = String(code || "").toUpperCase();
    $("#liveCode").value = liveCode;
    judgeSocket.emit("juez_unirse", {codigo_partida: liveCode});
    document.querySelector('[data-bs-target="#liveTab"]')?.click();
}

$("#connectLive").addEventListener("click", () => openLive($("#liveCode").value));
$("#startGame").addEventListener("click", () => judgeSocket.emit("iniciar_competencia", {codigo_partida: liveCode}));
$("#nextQuestion").addEventListener("click", () => judgeSocket.emit("siguiente_pregunta", {codigo_partida: liveCode}));
$("#finishGame").addEventListener("click", () => judgeSocket.emit("finalizar_competencia", {codigo_partida: liveCode}));

function renderRequests(requests, state = {}) {
    const orderedRequests = sortRequests(requests || []);
    const activeTurn = orderedRequests.some(item => item.estado === "EN_TURNO");
    const firstQueued = orderedRequests.find(item => item.estado === "EN_COLA");
    const closedQuestion = [
        "Respuesta correcta",
        "Competencia finalizada",
        "Cuenta regresiva"
    ].includes(state.estado_competencia);
    const canGiveWord = !activeTurn && !closedQuestion;
    const canGrade = state.estado_competencia === "Esperando respuesta" || activeTurn;

    const container = $("#wordRequests");

    if (orderedRequests.length === 0) {
        container.innerHTML = "<div class='text-secondary' data-empty-requests='1'>Sin solicitudes.</div>";
        return;
    }

    const emptyState = container.querySelector("[data-empty-requests]");

    if (emptyState) {
        emptyState.remove();
    }

    const visibleIds = new Set();

    orderedRequests.forEach(item => {
        const firstInQueue = firstQueued?.id_solicitud === item.id_solicitud;
        const status = requestStatusLabel(item, firstInQueue);
        const controls = item.estado === "EN_COLA" && firstInQueue && canGiveWord
            ? `<button class="btn btn-sm btn-primary" onclick="giveWord(${item.id_solicitud})">Dar palabra</button>`
            : item.estado === "EN_TURNO" && canGrade
                ? `<button class="btn btn-sm btn-success" onclick="markCorrect(${item.id_solicitud})">Correcta</button>
                   <button class="btn btn-sm btn-danger" onclick="markIncorrect(${item.id_solicitud})">Incorrecta</button>`
                : status.badge;
        const requestId = String(item.id_solicitud);
        let itemRow = container.querySelector(`[data-request-id="${requestId}"]`);

        if (!itemRow) {
            itemRow = document.createElement("div");
            itemRow.className = "list-row";
            itemRow.dataset.requestId = requestId;
        }

        itemRow.innerHTML = `
            <div>
                <strong>${escapeHtml(`${item.orden_solicitud}. ${item.sede}`)}</strong>
                <small>${escapeHtml(item.nombre || "")}<br>${status.text}</small>
            </div>
            <div>${controls}</div>
        `;
        container.appendChild(itemRow);
        visibleIds.add(requestId);
    });

    container.querySelectorAll("[data-request-id]").forEach(itemRow => {
        if (!visibleIds.has(itemRow.dataset.requestId)) {
            itemRow.remove();
        }
    });
}

function requestStatusLabel(item, firstInQueue = false) {
    if (item.estado === "EN_COLA" && firstInQueue) {
        return {
            text: `<span class="text-primary fw-semibold">Primero en la cola</span>`,
            badge: `<span class="badge text-bg-primary">Primero en cola</span>`
        };
    }

    if (item.estado === "EN_COLA") {
        return {
            text: `<span class="text-secondary">En espera</span>`,
            badge: `<span class="badge text-bg-secondary">En espera</span>`
        };
    }

    if (item.estado === "EN_TURNO") {
        return {
            text: `<span class="text-success fw-semibold">Tiene la palabra</span>`,
            badge: `<span class="badge text-bg-success">Tiene la palabra</span>`
        };
    }

    if (item.estado === "CORRECTA") {
        return {
            text: `<span class="text-success fw-semibold">Correcta</span>`,
            badge: `<span class="badge text-bg-success">Correcta</span>`
        };
    }

    if (item.estado === "INCORRECTA") {
        return {
            text: `<span class="text-danger fw-semibold">Incorrecta</span>`,
            badge: `<span class="badge text-bg-danger">Incorrecta</span>`
        };
    }

    if (item.estado === "CANCELADA") {
        return {
            text: `<span class="text-secondary">Ronda cerrada</span>`,
            badge: `<span class="badge text-bg-secondary">Ronda cerrada</span>`
        };
    }

    return {
        text: `<span class="text-secondary">${escapeHtml(item.estado || "")}</span>`,
        badge: `<span class="badge text-bg-secondary">${escapeHtml(item.estado || "")}</span>`
    };
}

function renderParticipants(participants) {
    const connected = (participants || []).filter(item => item.conectado === 1);

    $("#connectedParticipants").innerHTML = connected.map(item => row(
        item.sede || item.nombre,
        escapeHtml(item.nombre || "Equipo conectado"),
        `<span class="badge text-bg-success">Conectado</span>`
    )).join("") || "<div class='text-secondary'>Aun no hay equipos conectados.</div>";
}

function upsertBy(items, item, key) {
    const index = items.findIndex(existing => existing[key] === item[key]);

    if (index >= 0) {
        items[index] = {...items[index], ...item};
        return items;
    }

    return [...items, item];
}

function sortRequests(requests) {
    return (requests || []).sort((a, b) => (a.orden_solicitud || 0) - (b.orden_solicitud || 0));
}

function filterRequestsForQuestion(requests, questionId = liveQuestionId) {
    if (!questionId) {
        return [];
    }

    const normalizedQuestionId = String(questionId);

    return (requests || []).filter(item => (
        String(item.id_partida_pregunta) === normalizedQuestionId
    ));
}

function mergeRequests(current, incoming) {
    return sortRequests((incoming || []).reduce(
        (items, item) => upsertBy(items, item, "id_solicitud"),
        [...(current || [])]
    ));
}

function renderCompetitionStatus(stateOrEvent) {
    const status = stateOrEvent?.estado || stateOrEvent?.estado_competencia || "Sala abierta";
    const message = stateOrEvent?.mensaje || stateOrEvent?.mensaje_estado || "Esperando que el juez inicie la competencia.";

    $("#judgeCompetitionStatus").textContent = status;
    $("#judgeCompetitionMessage").textContent = message;
}

function renderImage(target, url) {
    if (url) {
        target.src = url;
        target.classList.remove("d-none");
    } else {
        target.removeAttribute("src");
        target.classList.add("d-none");
    }
}

function renderJudgeQuestion(question, fallback = "Esperando que el juez inicie la competencia.") {
    $("#judgeQuestion").textContent = question?.enunciado || fallback;
    $("#judgeAnswer").textContent = question?.respuesta_correcta || "Sin respuesta cargada.";
    renderImage($("#judgeQuestionImage"), question?.imagen);
    renderImage($("#judgeAnswerImage"), question?.imagen_respuesta);
}

function giveWord(id) {
    judgeSocket.emit("dar_palabra", {codigo_partida: liveCode, id_solicitud: id});
}

function markCorrect(id) {
    judgeSocket.emit("respuesta_correcta", {codigo_partida: liveCode, id_solicitud: id});
}

function markIncorrect(id) {
    judgeSocket.emit("respuesta_incorrecta", {codigo_partida: liveCode, id_solicitud: id});
}

judgeSocket.on("estado_sala", state => {
    const stateQuestionId = state.pregunta?.id_partida_pregunta || null;
    const sameQuestion = (
        liveQuestionId
        && stateQuestionId
        && String(liveQuestionId) === String(stateQuestionId)
    );
    const stateRequests = filterRequestsForQuestion(
        state.solicitudes || [],
        stateQuestionId
    );
    const shouldMergeRequests = sameQuestion || (
        liveRequests.length > 0
        && stateQuestionId
        && !liveQuestionId
    );

    liveState = state;
    liveQuestionId = stateQuestionId;
    liveParticipants = state.participantes || [];
    liveRequests = shouldMergeRequests
        ? mergeRequests(filterRequestsForQuestion(liveRequests, stateQuestionId), stateRequests)
        : sortRequests(stateRequests);
    renderCompetitionStatus(state);
    renderTimer($("#judgeTimer"), state.timer);
    renderRanking($("#judgeRanking"), state.ranking);
    renderRequests(liveRequests, state);
    renderParticipants(liveParticipants);

    if (state.partida?.estado === "EN_CURSO" && state.pregunta) {
        renderJudgeQuestion(state.pregunta, "Pregunta actual.");
    } else if (state.partida?.estado === "FINALIZADA") {
        renderJudgeQuestion(null, "Competencia finalizada.");
    } else {
        renderJudgeQuestion(null, "Esperando que el juez inicie la competencia.");
    }
});

judgeSocket.on("participante_conectado", payload => {
    const participant = payload?.participant || payload;

    liveParticipants = upsertBy(
        liveParticipants,
        {...participant, conectado: 1},
        "codigo_participante"
    );
    renderParticipants(liveParticipants);

    if (payload?.ranking) {
        renderRanking($("#judgeRanking"), payload.ranking);
    }
});

judgeSocket.on("participante_desconectado", payload => {
    liveParticipants = liveParticipants.map(participant => (
        participant.codigo_participante === payload?.codigo_participante
            ? {...participant, conectado: 0}
            : participant
    ));
    renderParticipants(liveParticipants);

    if (payload?.ranking) {
        renderRanking($("#judgeRanking"), payload.ranking);
    }
});

judgeSocket.on("solicitud_palabra", payload => {
    const request = payload?.request || payload;
    const queue = payload?.queue;
    const requestQuestionId = request?.id_partida_pregunta || liveQuestionId;

    if (
        requestQuestionId
        && liveQuestionId
        && String(requestQuestionId) !== String(liveQuestionId)
    ) {
        return;
    }

    if (requestQuestionId && !liveQuestionId) {
        liveQuestionId = requestQuestionId;
    }

    if (Array.isArray(queue)) {
        liveRequests = mergeRequests(
            filterRequestsForQuestion(liveRequests),
            filterRequestsForQuestion(queue)
        );
    } else if (request?.id_solicitud) {
        liveRequests = upsertBy(
            filterRequestsForQuestion(liveRequests),
            request,
            "id_solicitud"
        );
    }

    liveRequests = sortRequests(liveRequests);
    renderRequests(liveRequests, liveState);
});

judgeSocket.on("palabra_otorgada", request => {
    liveState = {
        ...liveState,
        estado_competencia: "Esperando respuesta",
        mensaje_estado: "Un equipo tiene la palabra."
    };
    liveRequests = upsertBy(
        filterRequestsForQuestion(liveRequests, request?.id_partida_pregunta || liveQuestionId),
        request,
        "id_solicitud"
    );
    liveRequests = sortRequests(liveRequests);
    renderCompetitionStatus(liveState);
    renderRequests(liveRequests, liveState);
});

judgeSocket.on("respuesta_calificada", payload => {
    const request = payload?.request;

    if (!request) {
        return;
    }

    const correct = request.estado === "CORRECTA";
    liveState = {
        ...liveState,
        estado_competencia: correct ? "Respuesta correcta" : "Respuesta incorrecta",
        mensaje_estado: correct
            ? "Respuesta correcta. Esperando siguiente pregunta."
            : "Respuesta incorrecta. Puede otorgar la palabra al siguiente equipo o esperar nuevas solicitudes."
    };
    if (!correct) {
        liveRequests = liveRequests.filter(
            item => item.id_solicitud !== request.id_solicitud
        );
    }

    (payload.affected_requests || [request]).forEach(item => {
        if (
            liveQuestionId
            && String(item.id_partida_pregunta) !== String(liveQuestionId)
        ) {
            return;
        }

        if (!correct && item.id_solicitud === request.id_solicitud) {
            return;
        }

        liveRequests = upsertBy(
            liveRequests,
            item,
            "id_solicitud"
        );
    });
    liveRequests = sortRequests(filterRequestsForQuestion(liveRequests));
    renderCompetitionStatus(liveState);
    renderRequests(liveRequests, liveState);
});

judgeSocket.on("actualizar_puntajes", ranking => {
    renderRanking($("#judgeRanking"), ranking);
});

judgeSocket.on("mostrar_podio", ranking => {
    liveState = {
        ...liveState,
        estado_competencia: "Competencia finalizada",
        mensaje_estado: "La competencia ha terminado."
    };
    renderCompetitionStatus(liveState);
    renderRanking($("#judgeRanking"), ranking);
    renderJudgeQuestion(null, "Competencia finalizada.");
});

judgeSocket.on("actualizar_cronometro", timer => renderTimer($("#judgeTimer"), timer));

judgeSocket.on("estado_competencia", event => {
    renderCompetitionStatus(event);
    renderJudgeQuestion(null, event.contador ? `${event.mensaje}` : event.mensaje);
});

judgeSocket.on("mostrar_pregunta", question => {
    liveQuestionId = question?.id_partida_pregunta || null;
    liveRequests = [];
    renderRequests(liveRequests, {
        ...liveState,
        estado_competencia: "Pregunta en curso"
    });
    renderJudgeQuestion(question, "Pregunta actual.");
});

loadCatalogs().then(refreshAll);


