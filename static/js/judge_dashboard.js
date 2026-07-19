const judgeSocket = io({transports: ["websocket"]});
let catalogs = {};
let liveCode = "";
let liveParticipants = [];
let liveRequests = [];
let liveState = {};
let liveQuestionId = null;
let liveTotalQuestions = null;
let materias = [];
let cuestionarios = [];
let partidas = [];
let selectedQuestionnaireIds = new Set();
let gameAreaSelectedManually = false;
let gameCreationPending = false;
let codeGenerationPending = false;
let pendingLiveAction = "";
let liveTransitionActive = false;
let liveTimerRemaining = null;
let pendingParticipantDeletions = new Set();
const QUESTIONNAIRE_ACTIVE_STATUS = "ACTIVO";
const GAME_STATUS_WAITING = "ESPERANDO";
const GAME_STATUS_IN_PROGRESS = "EN_CURSO";
const GAME_STATUS_PAUSED = "PAUSADA";
const GAME_STATUS_FINISHED = "FINALIZADA";

const $ = selector => document.querySelector(selector);
const judgeImageModal = bootstrap.Modal.getOrCreateInstance($("#judgeImageModal"));

function optionList(items, valueKey, textKey) {
    return items.map(item => {
        const value = valueKey ? item[valueKey] : item;
        const text = textKey ? item[textKey] : item;
        return `<option value="${escapeHtml(value)}">${escapeHtml(text)}</option>`;
    }).join("");
}

function row(title, subtitle, actions = "") {
    return `<div class="list-row"><div><strong>${escapeHtml(title)}</strong><small>${subtitle}</small></div><div class="list-row-actions">${actions}</div></div>`;
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
        $("#cuestionarioForm").area.innerHTML = optionList(data.areas);
        $("#gameArea").innerHTML = (
            '<option value="">Seleccionar área</option>'
            + optionList(data.areas)
        );
        document.querySelectorAll('select[name="estado"]').forEach(select => {
            select.innerHTML = optionList(data.estados_cuestionario);
        });
        resetQuestionnaireForm(false);
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
            <button class="btn btn-sm btn-outline-danger" onclick="deleteMateria(${item.id_materia})">Eliminar</button>
        `)).join("");
        document.querySelectorAll('select[name="id_materia"]').forEach(select => {
            select.innerHTML = optionList(materias, "id_materia", "nombre");
        });
}

function refreshCuestionarios() {
    return apiFetch("/api/cuestionarios").then(items => {
        if (!Array.isArray(items)) {
            throw new Error(items?.message || "No fue posible cargar los cuestionarios.");
        }

        cuestionarios = items;
        renderCuestionarios();
        return items;
    });
}

function renderCuestionarios(updateSelectors = true) {
        const search = $("#questionnaireSearch")?.value || "";
        const filtered = ContentFilters.filterQuestionnaires(cuestionarios, search);
        const hasSearch = Boolean(ContentFilters.normalizeSearch(search));
        $("#cuestionariosList").innerHTML = filtered.map(item => row(
            item.nombre,
            `${escapeHtml(item.materia?.nombre || "")} - ${escapeHtml(item.area)} - ${escapeHtml(item.estado)}`,
            `<a class="btn btn-sm btn-primary" href="/juez/cuestionario/${item.id_cuestionario}/preguntas">Preguntas</a>
             <button class="btn btn-sm btn-outline-secondary" onclick="editCuestionario(${item.id_cuestionario})">Editar</button>
             <button class="btn btn-sm btn-outline-danger" onclick="deleteCuestionario(${item.id_cuestionario})">Eliminar</button>`
        )).join("") || (
            hasSearch
                ? "<div class='text-secondary'>No hay cuestionarios que coincidan con la búsqueda.</div>"
                : "<div class='text-secondary'>No hay cuestionarios creados.</div>"
        );
        $("#questionnaireFilterSummary").textContent = hasSearch
            ? `${filtered.length} de ${cuestionarios.length} cuestionarios`
            : `${cuestionarios.length} cuestionarios`;
        $("#clearQuestionnaireSearch").disabled = !hasSearch;
        if (updateSelectors) {
            document.querySelectorAll('select[name="id_cuestionario"]').forEach(select => {
                select.innerHTML = optionList(cuestionarios, "id_cuestionario", "nombre");
            });
        }
        renderGameQuestionnaires();
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
        const partidaDetails = item => [
            `Cuestionarios: ${escapeHtml(item.cuestionarios || "Sin cuestionario")}`,
            `Materia: ${escapeHtml(item.materias || "Sin materia")}`,
            `Área: ${escapeHtml(item.area || "")}`,
            `<span class="badge text-bg-light border">${escapeHtml(item.estado || "Sin estado")}</span>`,
            `Participantes: ${Number(item.participantes_conectados || 0)} conectados de ${Number(item.total_participantes || 0)}`
        ].join("<br>");
        const historyDetails = item => [
            `Cuestionario: ${escapeHtml(item.cuestionarios || "Sin cuestionario")}`,
            `Materia: ${escapeHtml(item.materias || "Sin materia")}`,
            `Nivel: ${escapeHtml(item.area || "")}`,
            `Estado: ${escapeHtml(item.estado || "")}`,
            `Participantes: ${item.participantes_conectados || 0}/${item.total_participantes || 0}`
        ].join("<br>");
        const openButton = item => `<button class="btn btn-sm btn-primary" onclick="openLive('${item.codigo_partida}')">${JudgeGameHelpers.gameActionLabel(item.estado)}</button>`;
        const historyOpenButton = item => `<button class="btn btn-sm btn-primary" onclick="openLive('${item.codigo_partida}')">Abrir</button>`;
        const copyButton = item => `<button class="btn btn-sm btn-outline-primary" onclick="copyGameCode('${item.codigo_partida}')">Copiar código</button>`;
        const markup = partidas.map(item => row(
            `${item.nombre} · ${item.codigo_partida}`,
            partidaDetails(item),
            `${openButton(item)} ${copyButton(item)}
             <button class="btn btn-sm btn-outline-danger" onclick="deletePartida(${item.id_partida})">Eliminar</button>`
        )).join("");
        const historyMarkup = partidas.map(item => row(
            `${item.codigo_partida} - ${item.nombre}`,
            historyDetails(item),
            historyOpenButton(item)
        )).join("");
        $("#partidasList").innerHTML = markup || "<div class='text-secondary'>No hay partidas creadas.</div>";
        $("#historyList").innerHTML = historyMarkup || "<div class='text-secondary'>No hay historial disponible.</div>";
}

function showDashboardTab(tabName, updateHash = true) {
    const trigger = document.querySelector(`[data-dashboard-tab="${tabName}"]`);

    if (!trigger) {
        return;
    }

    bootstrap.Tab.getOrCreateInstance(trigger).show();

    if (updateHash && window.location.hash !== `#${tabName}`) {
        history.replaceState(null, "", `#${tabName}`);
    }
}

function syncGameArea() {
    const areaSelect = $("#gameArea");
    const areaHelp = $("#gameAreaHelp");
    const selection = JudgeGameHelpers.questionnaireSelectionState(
        cuestionarios,
        selectedQuestionnaireIds,
        gameAreaSelectedManually,
        areaSelect.value
    );

    if (!gameAreaSelectedManually) {
        areaSelect.value = selection.area;
    }

    if (selection.requiresManualArea) {
        areaHelp.textContent = "Los cuestionarios seleccionados pertenecen a distintas áreas. Selecciona manualmente el área que se utilizará para la partida.";
        areaHelp.classList.add("text-danger");
        areaSelect.setAttribute("aria-invalid", "true");
    } else if (gameAreaSelectedManually) {
        areaHelp.textContent = areaSelect.value
            ? "Área seleccionada manualmente; no se cambiará al modificar los cuestionarios."
            : "Selecciona manualmente el área que se utilizará para la partida.";
        areaHelp.classList.toggle("text-danger", !areaSelect.value);
        areaSelect.setAttribute("aria-invalid", String(!areaSelect.value));
    } else if (selection.inferred) {
        areaHelp.textContent = `Área inferida automáticamente: ${selection.area}.`;
        areaHelp.classList.remove("text-danger");
        areaSelect.removeAttribute("aria-invalid");
    } else {
        areaHelp.textContent = "Selecciona cuestionarios para inferir el área o elígela manualmente.";
        areaHelp.classList.remove("text-danger");
        areaSelect.removeAttribute("aria-invalid");
    }

    return selection;
}

function renderGameQuestionnaires() {
    const search = $("#gameQuestionnaireSearch")?.value || "";
    const active = JudgeGameHelpers.activeQuestionnaires(cuestionarios);
    const activeIds = new Set(active.map(item => String(item.id_cuestionario)));
    selectedQuestionnaireIds = new Set(
        [...selectedQuestionnaireIds].filter(id => activeIds.has(String(id)))
    );
    const filtered = JudgeGameHelpers.filterActiveQuestionnaires(cuestionarios, search);
    const hasSearch = Boolean(ContentFilters.normalizeSearch(search));
    const list = $("#gameQuestionnaireList");

    list.innerHTML = filtered.map(item => {
        const id = String(item.id_cuestionario);
        const checked = selectedQuestionnaireIds.has(id) ? " checked" : "";
        const details = [item.materia?.nombre, item.area].filter(Boolean).join(" · ");

        return `
            <label class="questionnaire-check-option">
                <input class="form-check-input" type="checkbox" name="id_cuestionarios" value="${escapeHtml(id)}"${checked}>
                <span>
                    <strong>${escapeHtml(item.nombre)}</strong>
                    <small>${escapeHtml(details || "Cuestionario activo")}</small>
                </span>
            </label>
        `;
    }).join("") || (
        active.length === 0
            ? "<div class='text-secondary'>No hay cuestionarios activos disponibles. Administra tus cuestionarios para activar al menos uno.</div>"
            : "<div class='text-secondary'>No hay cuestionarios activos que coincidan con el filtro.</div>"
    );

    const selection = syncGameArea();
    $("#gameQuestionnaireSummary").textContent = (
        `${selection.selectedCount} cuestionario${selection.selectedCount === 1 ? "" : "s"} seleccionado${selection.selectedCount === 1 ? "" : "s"}`
        + (hasSearch ? ` · ${filtered.length} visibles de ${active.length}` : "")
    );
    $("#clearGameQuestionnaireSearch").disabled = !hasSearch;
    $("#clearGameQuestionnaireSelection").disabled = selection.selectedCount === 0;
}

function generateGameCode() {
    const button = $("#generateCode");

    if (codeGenerationPending) {
        return Promise.resolve("");
    }

    codeGenerationPending = true;
    button.disabled = true;
    button.textContent = "Generando...";

    return apiFetch("/api/partidas/generar-codigo").then(payload => {
        if (!payload.success || !payload.data) {
            throw new Error(payload.message || "No fue posible generar un código de sala.");
        }

        $("#gameCode").value = payload.data;
        return payload.data;
    }).catch(error => {
        setMessage($("#partidaMessage"), error.message || "No fue posible generar un código de sala.", false);
        return "";
    }).finally(() => {
        codeGenerationPending = false;
        button.disabled = false;
        button.textContent = "Generar nuevo";
    });
}

function resetGameForm({clearMessage = true, generateCode = true} = {}) {
    const form = $("#partidaForm");
    form.reset();
    selectedQuestionnaireIds = new Set();
    gameAreaSelectedManually = false;
    $("#gameQuestionnaireSearch").value = "";
    $("#gameArea").value = "";
    renderGameQuestionnaires();

    if (clearMessage) {
        setMessage($("#partidaMessage"), "", true);
    }

    if (generateCode) {
        generateGameCode();
    }
}

function fallbackCopyText(text) {
    const textarea = document.createElement("textarea");
    textarea.value = text;
    textarea.setAttribute("readonly", "");
    textarea.style.position = "fixed";
    textarea.style.opacity = "0";
    document.body.appendChild(textarea);
    textarea.select();
    const copied = document.execCommand("copy");
    textarea.remove();
    return copied;
}

async function copyText(text) {
    if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(text);
        return true;
    }

    return fallbackCopyText(text);
}

async function copyGameCode(code) {
    const normalizedCode = String(code || "").trim().toUpperCase();

    if (!normalizedCode) {
        return;
    }

    try {
        const copied = await copyText(normalizedCode);
        if (liveCode === normalizedCode) {
            setLiveMessage(copied ? `Código ${normalizedCode} copiado.` : "No fue posible copiar el código.", copied);
        } else {
            setMessage($("#partidasMessage"), copied ? `Código ${normalizedCode} copiado.` : "No fue posible copiar el código.", copied);
        }
    } catch (error) {
        console.warn("No fue posible copiar el código de sala.", error);
        setMessage($("#partidasMessage"), "No fue posible copiar el código. Selecciónalo manualmente.", false);
    }
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

function deleteMateria(id) {
    const message = $("#materiaMessage");
    setMessage(message, "Eliminando materia...", true);
    apiFetch(`/api/materias/${id}`, {method: "DELETE"}).then(payload => {
        if (!payload.success) {
            setMessage(message, payload.message || "No fue posible eliminar la materia.", false);
            return;
        }

        materias = materias.filter(item => item.id_materia !== id);
        renderMaterias();
        setMessage(message, payload.message || "Materia eliminada correctamente.", true);
    }).catch(() => {
        setMessage(message, "No fue posible eliminar la materia.", false);
    });
}

function deleteCuestionario(id) {
    const message = $("#cuestionarioMessage");
    setMessage(message, "Eliminando cuestionario...", true);
    apiFetch(`/api/cuestionarios/${id}`, {method: "DELETE"}).then(payload => {
        if (!payload.success) {
            setMessage(message, payload.message || "No fue posible eliminar el cuestionario.", false);
            return;
        }

        cuestionarios = cuestionarios.filter(item => item.id_cuestionario !== id);
        if (Number($("#cuestionarioForm").id_cuestionario.value) === Number(id)) {
            resetQuestionnaireForm(false);
        }
        renderCuestionarios();
        setMessage(message, payload.message || "Cuestionario eliminado correctamente.", true);
    }).catch(() => {
        setMessage(message, "No fue posible eliminar el cuestionario.", false);
    });
}

function deletePartida(id) {
    const message = $("#partidasMessage");
    setMessage(message, "Eliminando partida...", true);
    apiFetch(`/api/partidas/${id}`, {method: "DELETE"}).then(payload => {
        if (!payload.success) {
            setMessage(message, payload.message || "No fue posible eliminar la partida.", false);
            return;
        }

        partidas = partidas.filter(item => Number(item.id_partida) !== Number(id));
        renderPartidas();
        setMessage(message, payload.message || "Partida eliminada correctamente.", true);
    }).catch(() => {
        setMessage(message, "No fue posible eliminar la partida.", false);
    });
}

function editMateria(id, nombre) {
    const form = $("#materiaForm");
    form.id_materia.value = id;
    form.nombre.value = nombre;
}

function resetQuestionnaireForm(clearMessage = true) {
    const form = $("#cuestionarioForm");
    form.reset();
    form.id_cuestionario.value = "";
    if (form.id_materia.options.length) {
        form.id_materia.selectedIndex = 0;
    }
    if (form.area.options.length) {
        form.area.selectedIndex = 0;
    }
    form.estado.value = QUESTIONNAIRE_ACTIVE_STATUS;
    $("#questionnaireSubmit").textContent = "Guardar cuestionario";
    $("#cancelQuestionnaireEdit").classList.add("d-none");
    $("#clearQuestionnaireFields").classList.remove("d-none");

    if (clearMessage) {
        setMessage($("#cuestionarioMessage"), "", true);
    }
}

function editCuestionario(id) {
    const cuestionario = cuestionarios.find(
        item => Number(item.id_cuestionario) === Number(id)
    );

    if (!cuestionario) {
        setMessage($("#cuestionarioMessage"), "No fue posible cargar el cuestionario seleccionado.", false);
        return;
    }

    resetQuestionnaireForm(false);
    const form = $("#cuestionarioForm");
    form.id_cuestionario.value = cuestionario.id_cuestionario;
    form.nombre.value = cuestionario.nombre || "";
    form.id_materia.value = cuestionario.materia?.id_materia || "";
    form.area.value = cuestionario.area || "";
    form.estado.value = cuestionario.estado || "";
    $("#questionnaireSubmit").textContent = "Actualizar cuestionario";
    $("#cancelQuestionnaireEdit").classList.remove("d-none");
    $("#clearQuestionnaireFields").classList.add("d-none");
    setMessage($("#cuestionarioMessage"), `Editando: ${cuestionario.nombre}`, true);
    form.nombre.focus();
}

$("#cancelQuestionnaireEdit").addEventListener("click", () => {
    resetQuestionnaireForm(false);
    setMessage($("#cuestionarioMessage"), "Edición cancelada. Formulario listo para crear.", true);
});

$("#clearQuestionnaireFields").addEventListener("click", () => {
    resetQuestionnaireForm(false);
    setMessage($("#cuestionarioMessage"), "Campos limpiados.", true);
    $("#cuestionarioForm").nombre.focus();
});

$("#questionnaireSearch").addEventListener("input", () => renderCuestionarios(false));

$("#clearQuestionnaireSearch").addEventListener("click", () => {
    $("#questionnaireSearch").value = "";
    renderCuestionarios(false);
    $("#questionnaireSearch").focus();
});

document.querySelectorAll("[data-go-to-tab]").forEach(button => {
    button.addEventListener("click", () => showDashboardTab(button.dataset.goToTab));
});

document.querySelectorAll("[data-dashboard-tab]").forEach(button => {
    button.addEventListener("shown.bs.tab", () => {
        const tabName = button.dataset.dashboardTab;
        history.replaceState(null, "", `#${tabName}`);

        if (tabName === "partidas" && !$("#gameCode").value) {
            generateGameCode();
        }
    });
});

$("#gameQuestionnaireSearch").addEventListener("input", renderGameQuestionnaires);

$("#clearGameQuestionnaireSearch").addEventListener("click", () => {
    $("#gameQuestionnaireSearch").value = "";
    renderGameQuestionnaires();
    $("#gameQuestionnaireSearch").focus();
});

$("#gameQuestionnaireList").addEventListener("change", event => {
    const checkbox = event.target.closest('input[name="id_cuestionarios"]');

    if (!checkbox) {
        return;
    }

    const id = String(checkbox.value);

    if (checkbox.checked) {
        selectedQuestionnaireIds.add(id);
    } else {
        selectedQuestionnaireIds.delete(id);
    }

    renderGameQuestionnaires();
});

$("#clearGameQuestionnaireSelection").addEventListener("click", () => {
    selectedQuestionnaireIds = new Set();
    renderGameQuestionnaires();
});

$("#gameArea").addEventListener("change", event => {
    gameAreaSelectedManually = Boolean(event.currentTarget.value);
    syncGameArea();
});

$("#refreshQuestionnaires").addEventListener("click", async event => {
    const button = event.currentTarget;
    button.disabled = true;
    button.textContent = "Actualizando...";
    setMessage($("#cuestionarioMessage"), "Actualizando lista de cuestionarios...", true);

    try {
        await refreshCuestionarios();
        setMessage($("#cuestionarioMessage"), "Lista de cuestionarios actualizada.", true);
    } catch (error) {
        setMessage(
            $("#cuestionarioMessage"),
            error.message || "No fue posible actualizar los cuestionarios.",
            false
        );
    } finally {
        button.disabled = false;
        button.textContent = "Actualizar";
    }
});

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
    const id = form.id_cuestionario.value;
    const submitButton = $("#questionnaireSubmit");
    const action = id ? "actualizar" : "guardar";

    submitButton.disabled = true;
    setMessage($("#cuestionarioMessage"), `${id ? "Actualizando" : "Guardando"} cuestionario...`, true);

    apiFetch(id ? `/api/cuestionarios/${id}` : "/api/cuestionarios", {
        method: id ? "PUT" : "POST",
        body: JSON.stringify(formJson(form))
    }).then(payload => {
        if (!payload.success) {
            setMessage(
                $("#cuestionarioMessage"),
                payload.message || `No fue posible ${action} el cuestionario.`,
                false
            );
            return;
        }

        cuestionarios = upsertLocal(cuestionarios, payload.data, "id_cuestionario");
        renderCuestionarios();
        resetQuestionnaireForm(false);
        setMessage(
            $("#cuestionarioMessage"),
            payload.message || `Cuestionario ${id ? "actualizado" : "guardado"} correctamente.`,
            true
        );
    }).catch(() => {
        setMessage(
            $("#cuestionarioMessage"),
            `No fue posible comunicarse con el servidor para ${action} el cuestionario.`,
            false
        );
    }).finally(() => {
        submitButton.disabled = false;
    });
});

$("#generateCode").addEventListener("click", generateGameCode);

$("#partidaForm").addEventListener("submit", async event => {
    event.preventDefault();

    if (gameCreationPending) {
        return;
    }

    const form = event.currentTarget;
    const selection = syncGameArea();
    const submitButton = $("#createGame");
    const message = $("#partidaMessage");

    if (selection.selectedCount === 0) {
        setMessage(message, "Selecciona al menos un cuestionario activo.", false);
        $("#gameQuestionnaireList").focus();
        return;
    }

    if (!form.area.value) {
        setMessage(message, selection.requiresManualArea
            ? "Los cuestionarios pertenecen a distintas áreas. Selecciona manualmente el área de la partida."
            : "Selecciona el área de la partida.", false);
        form.area.focus();
        return;
    }

    if (!form.reportValidity()) {
        return;
    }

    const data = formJson(event.currentTarget);
    const selectedQuestionnaires = selection.selected.map(item => item.nombre).join(", ");
    data.id_cuestionarios = [...selectedQuestionnaireIds];
    gameCreationPending = true;
    submitButton.disabled = true;
    submitButton.textContent = "Creando sala...";
    setMessage(message, "Creando sala...", true);

    try {
        const payload = await apiFetch("/api/partidas", {
            method: "POST",
            body: JSON.stringify(data)
        });

        if (!payload.success) {
            setMessage(message, payload.message || "No fue posible crear la sala.", false);
            return;
        }

        const createdGame = payload.data || {};
        const roomCode = createdGame.codigo_partida || data.codigo_partida;

        if (!roomCode) {
            setMessage(message, "Sala creada correctamente. Actualiza el listado si no aparece.", true);
            return;
        }

        setMessage(message, `Sala ${roomCode} creada correctamente.`, true);
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
        resetGameForm({clearMessage: false, generateCode: true});
    } catch (error) {
        console.warn("No fue posible crear la sala.", error);
        setMessage(message, "No fue posible crear la sala. Revisa la información ingresada e inténtalo de nuevo.", false);
    } finally {
        gameCreationPending = false;
        submitButton.disabled = false;
        submitButton.textContent = "Crear sala";
    }
});

function openLive(code) {
    const normalizedCode = String(code || "").trim().toUpperCase();

    if (!normalizedCode) {
        setMessage($("#liveOpenMessage"), "Ingresa un código de sala válido.", false);
        showDashboardTab("competencia");
        $("#liveCode").focus();
        return;
    }

    if (liveCode !== normalizedCode) {
        liveState = {};
        liveParticipants = [];
        liveRequests = [];
        liveQuestionId = null;
        liveTotalQuestions = null;
        liveTimerRemaining = null;
        liveTransitionActive = false;
        pendingParticipantDeletions = new Set();
        clearPendingLiveAction();
        renderJudgeLayout();
    }

    liveCode = normalizedCode;
    $("#liveCode").value = liveCode;
    setMessage($("#liveOpenMessage"), `Abriendo sala ${liveCode}...`, true);
    $("#connectLive").disabled = true;
    $("#connectLive").textContent = "Abriendo...";
    judgeSocket.emit("juez_unirse", {codigo_partida: liveCode});
    showDashboardTab("competencia");
}

$("#connectLive").addEventListener("click", () => openLive($("#liveCode").value));
$("#liveCode").addEventListener("keydown", event => {
    if (event.key === "Enter") {
        event.preventDefault();
        openLive(event.currentTarget.value);
    }
});

function currentGameState() {
    return liveState?.partida?.estado || "";
}

function currentCompetitionControls() {
    return JudgeGameHelpers.competitionControlState({
        gameState: currentGameState(),
        hasQuestion: Boolean(liveState?.pregunta),
        questionState: (
            liveState?.pregunta?.estado_partida_pregunta
            || liveState?.pregunta?.estado
            || ""
        ),
        remaining: liveTimerRemaining,
        transitionActive: liveTransitionActive,
        pendingAction: pendingLiveAction
    });
}

function updateLiveActionButtons() {
    const state = currentGameState();
    const controls = currentCompetitionControls();
    const startButton = $("#startGame");
    const pauseResumeButton = $("#pauseResumeGame");
    const nextButton = $("#nextQuestion");
    const finishButton = $("#finishGame");

    startButton.classList.toggle("d-none", state !== GAME_STATUS_WAITING);
    startButton.disabled = (
        state !== GAME_STATUS_WAITING
        || Boolean(pendingLiveAction)
        || liveTransitionActive
    );
    startButton.textContent = pendingLiveAction === "start" ? "Iniciando..." : "Iniciar competencia";

    pauseResumeButton.classList.toggle("d-none", !controls.showPauseResume);
    pauseResumeButton.disabled = controls.pauseResumeAction === "blocked";
    pauseResumeButton.classList.toggle("btn-warning", !controls.paused);
    pauseResumeButton.classList.toggle("btn-success", controls.paused);
    pauseResumeButton.textContent = pendingLiveAction === "pause"
        ? "Pausando..."
        : pendingLiveAction === "resume"
            ? "Reanudando..."
            : controls.paused
                ? "Reanudar"
                : "Pausar";

    nextButton.disabled = !controls.canNext;
    nextButton.textContent = pendingLiveAction === "finish-time"
        ? "Finalizando tiempo..."
        : pendingLiveAction === "next"
            ? "Preparando siguiente..."
            : "Siguiente pregunta";

    finishButton.classList.toggle(
        "d-none",
        ![GAME_STATUS_IN_PROGRESS, GAME_STATUS_PAUSED].includes(state)
    );
    finishButton.disabled = !controls.canFinish;
    finishButton.textContent = pendingLiveAction === "finish" ? "Finalizando..." : "Finalizar";
}

function setPendingLiveAction(action) {
    if (pendingLiveAction) {
        return false;
    }

    pendingLiveAction = action;
    updateLiveActionButtons();
    return true;
}

function clearPendingLiveAction() {
    pendingLiveAction = "";
    updateLiveActionButtons();
}

function setLiveMessage(message, success = true) {
    setMessage($("#judgeCompetitionMessage"), message, success);
    setMessage($("#waitingRoomMessage"), message, success);
}

function registeredParticipants(participants = liveParticipants) {
    return (participants || []).filter(item => (
        item.id_participante || item.codigo_participante || item.nombre
    ));
}

function renderWaitingRoom() {
    const participants = registeredParticipants();
    const connectedCount = participants.filter(item => Number(item.conectado) === 1).length;
    const waiting = currentGameState() === GAME_STATUS_WAITING;
    $("#waitingGameName").textContent = liveState?.partida?.nombre || "Partida";
    $("#waitingGameCode").textContent = liveCode || liveState?.partida?.codigo_partida || "------";
    $("#waitingConnectedCount").textContent = String(connectedCount);
    $("#waitingParticipants").innerHTML = participants.map(item => {
        const id = Number(item.id_participante);
        const pending = pendingParticipantDeletions.has(id);
        const connected = Number(item.conectado) === 1;
        const memberText = String(item.integrantes || "").trim();
        const siteIdentity = JudgeGameHelpers.teamSiteIdentity(item.sede);
        const siteStyle = [
            `--site-accent:${siteIdentity.accent}`,
            `--site-tint:${siteIdentity.tint}`,
            `--site-detail:${siteIdentity.detail}`
        ].join(";");

        return `
            <article class="waiting-participant-card" data-site-identity="${siteIdentity.key}" style="${siteStyle}">
                <div class="waiting-participant-head">
                    <div>
                        <div class="waiting-participant-site">
                            <span class="site-identity-dot" aria-hidden="true"></span>
                            <strong>${escapeHtml(item.sede || item.nombre || "Equipo")}</strong>
                        </div>
                        <small>${escapeHtml(item.nombre || "Equipo registrado")}</small>
                    </div>
                    <span class="badge ${connected ? "text-bg-success" : "text-bg-secondary"}">${connected ? "Conectado" : "Desconectado"}</span>
                </div>
                ${memberText ? `<small><strong>Integrantes:</strong> ${escapeHtml(memberText)}</small>` : ""}
                ${waiting && id ? `<button class="btn btn-sm btn-outline-danger" type="button" onclick="deleteWaitingParticipant(${id})"${pending ? " disabled" : ""}>${pending ? "Eliminando..." : "Eliminar equipo"}</button>` : ""}
            </article>
        `;
    }).join("") || "<div class='text-secondary'>Aún no hay equipos registrados en esta sala.</div>";
    updateLiveActionButtons();
}

function syncActiveGameSummary() {
    const game = liveState?.partida;

    if (!game?.codigo_partida) {
        return;
    }

    const participants = registeredParticipants();
    const connectedCount = participants.filter(item => Number(item.conectado) === 1).length;
    const existing = partidas.find(item => (
        String(item.codigo_partida).toUpperCase() === String(game.codigo_partida).toUpperCase()
    ));
    upsertPartida({
        ...(existing || {}),
        ...game,
        total_participantes: participants.length,
        participantes_conectados: connectedCount
    });
    renderPartidas();
}

function renderJudgeLayout() {
    const state = currentGameState();
    const waiting = state === GAME_STATUS_WAITING || state === "BORRADOR";
    const competition = [
        GAME_STATUS_IN_PROGRESS,
        GAME_STATUS_PAUSED,
        GAME_STATUS_FINISHED
    ].includes(state) || liveTransitionActive;
    const hasRoom = Boolean(liveState?.partida);

    $("#liveConnectPanel").classList.toggle("d-none", hasRoom);
    $("#judgeWaitingRoom").classList.toggle("d-none", !waiting || liveTransitionActive);
    $("#judgeCompetitionPanel").classList.toggle("d-none", !competition);
    renderWaitingRoom();
    updateLiveActionButtons();
}

function requestFinishGame(fromLastQuestion = false) {
    if (pendingLiveAction || liveTransitionActive) {
        return;
    }

    const confirmed = window.confirm(fromLastQuestion
        ? "No hay más preguntas restantes.\nLa partida se finalizará."
        : "¿Deseas finalizar la competencia? Esta acción mostrará el resultado final.");

    if (!confirmed || !setPendingLiveAction("finish")) {
        return;
    }

    setLiveMessage("Finalizando competencia...", true);
    judgeSocket.emit("finalizar_competencia", {codigo_partida: liveCode});
}

$("#startGame").addEventListener("click", () => {
    if (currentGameState() !== GAME_STATUS_WAITING || !setPendingLiveAction("start")) {
        return;
    }

    setLiveMessage("Iniciando competencia...", true);
    judgeSocket.emit("iniciar_competencia", {codigo_partida: liveCode});
});

$("#pauseResumeGame").addEventListener("click", () => {
    const action = currentCompetitionControls().pauseResumeAction;

    if (action === "blocked" || !setPendingLiveAction(action)) {
        return;
    }

    if (action === "resume") {
        setLiveMessage("Reanudando competencia...", true);
        judgeSocket.emit("reanudar_competencia", {codigo_partida: liveCode});
        return;
    }

    setLiveMessage("Pausando competencia...", true);
    judgeSocket.emit("pausar_competencia", {codigo_partida: liveCode});
});

$("#nextQuestion").addEventListener("click", () => {
    const action = JudgeGameHelpers.nextQuestionAction({
        gameState: currentGameState(),
        remaining: liveTimerRemaining,
        currentQuestion: liveState?.partida?.pregunta_actual,
        totalQuestions: liveTotalQuestions,
        transitionActive: liveTransitionActive || Boolean(pendingLiveAction)
    });

    if (action === "finish_time") {
        const confirmed = window.confirm(
            "El tiempo de la pregunta todavía no ha finalizado.\n¿Deseas finalizar el tiempo actual?"
        );

        if (!confirmed || !setPendingLiveAction("finish-time")) {
            return;
        }

        judgeSocket.emit("siguiente_pregunta", {
            codigo_partida: liveCode,
            finalizar_tiempo_actual: true
        });
        return;
    }

    if (action === "finish_game") {
        requestFinishGame(true);
        return;
    }

    if (action !== "advance" || !setPendingLiveAction("next")) {
        return;
    }

    setLiveMessage("Preparando la siguiente pregunta...", true);
    judgeSocket.emit("siguiente_pregunta", {codigo_partida: liveCode});
});

$("#finishGame").addEventListener("click", () => requestFinishGame(false));

$("#copyWaitingCode").addEventListener("click", () => copyGameCode(liveCode));

function deleteWaitingParticipant(id) {
    const participantId = Number(id);

    if (
        !participantId
        || pendingParticipantDeletions.has(participantId)
        || currentGameState() !== GAME_STATUS_WAITING
    ) {
        return;
    }

    const participant = liveParticipants.find(item => Number(item.id_participante) === participantId);
    const confirmed = window.confirm(
        `¿Eliminar a ${participant?.sede || participant?.nombre || "este equipo"} de la sala de espera?`
    );

    if (!confirmed) {
        return;
    }

    pendingParticipantDeletions.add(participantId);
    renderWaitingRoom();
    setLiveMessage("Eliminando equipo de la sala de espera...", true);
    judgeSocket.emit("eliminar_participante_espera", {
        codigo_partida: liveCode,
        id_participante: participantId
    });
}

function openJudgeImage(url, label) {
    if (!url) {
        return;
    }

    $("#judgeImageModalLabel").textContent = label;
    $("#judgeImageModalContent").src = url;
    $("#judgeImageModalContent").alt = label;
    judgeImageModal.show();
}

$("#expandQuestionImage").addEventListener("click", () => {
    openJudgeImage($("#judgeQuestionImage").src, "Imagen de la pregunta ampliada");
});

$("#expandAnswerImage").addEventListener("click", () => {
    openJudgeImage($("#judgeAnswerImage").src, "Imagen de la respuesta esperada ampliada");
});

function renderRequests(requests, state = {}) {
    const orderedRequests = JudgeGameHelpers.activeWordRequests(requests);
    const competitionControls = currentCompetitionControls();
    const activeTurn = orderedRequests.some(item => item.estado === "EN_TURNO");
    const firstQueued = orderedRequests.find(item => item.estado === "EN_COLA");
    const closedQuestion = [
        "Respuesta correcta",
        "Competencia finalizada",
        "Cuenta regresiva"
    ].includes(state.estado_competencia);
    const canGiveWord = (
        competitionControls.canModifyQuestion
        && !activeTurn
        && !closedQuestion
    );
    const canGrade = (
        competitionControls.canModifyQuestion
        && (state.estado_competencia === "Esperando respuesta" || activeTurn)
    );

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
        const controls = item.estado === "EN_COLA" && firstInQueue
            ? `<button class="btn btn-sm btn-primary" onclick="giveWord(${item.id_solicitud})"${canGiveWord ? "" : " disabled aria-disabled=\"true\""}>Dar palabra</button>`
            : item.estado === "EN_TURNO"
                ? `<button class="btn btn-sm btn-success" onclick="markCorrect(${item.id_solicitud})"${canGrade ? "" : " disabled aria-disabled=\"true\""}>Correcta</button>
                   <button class="btn btn-sm btn-danger" onclick="markIncorrect(${item.id_solicitud})"${canGrade ? "" : " disabled aria-disabled=\"true\""}>Incorrecta</button>`
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

function activeRequests(requests) {
    return JudgeGameHelpers.activeWordRequests(requests);
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
    return activeRequests((incoming || []).reduce(
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

function renderImage(target, url, expandButton = null) {
    if (url) {
        target.src = url;
        target.classList.remove("d-none");
        expandButton?.classList.remove("d-none");
    } else {
        target.removeAttribute("src");
        target.classList.add("d-none");
        expandButton?.classList.add("d-none");
    }
}

function updateQuestionCounter(target, question = null, total = liveTotalQuestions) {
    const current = question?.numero_orden || liveState?.ranking?.current_question || "--";
    const max = total || liveState?.ranking?.total_questions || "--";
    target.textContent = `Pregunta ${current || "--"} / ${max || "--"}`;
}

function renderJudgeQuestion(question, fallback = "Esperando que el juez inicie la competencia.") {
    $("#judgeQuestion").textContent = question?.enunciado || fallback;
    $("#judgeAnswer").textContent = question?.respuesta_correcta || "Sin respuesta cargada.";
    renderImage($("#judgeQuestionImage"), question?.imagen, $("#expandQuestionImage"));
    renderImage($("#judgeAnswerImage"), question?.imagen_respuesta, $("#expandAnswerImage"));
    updateQuestionCounter($("#judgeQuestionNumber"), question);
}

function giveWord(id) {
    if (!currentCompetitionControls().canModifyQuestion) {
        return;
    }

    judgeSocket.emit("dar_palabra", {codigo_partida: liveCode, id_solicitud: id});
}

function markCorrect(id) {
    if (!currentCompetitionControls().canModifyQuestion) {
        return;
    }

    judgeSocket.emit("respuesta_correcta", {codigo_partida: liveCode, id_solicitud: id});
}

function markIncorrect(id) {
    if (!currentCompetitionControls().canModifyQuestion) {
        return;
    }

    judgeSocket.emit("respuesta_incorrecta", {codigo_partida: liveCode, id_solicitud: id});
}

judgeSocket.on("estado_sala", state => {
    if (!state?.partida) {
        $("#connectLive").disabled = false;
        $("#connectLive").textContent = "Abrir";
        setMessage($("#liveOpenMessage"), "La sala indicada no existe o no está disponible.", false);
        return;
    }

    const stateCode = String(state.partida.codigo_partida || "").toUpperCase();

    if (liveCode && stateCode && stateCode !== liveCode) {
        return;
    }

    liveCode = stateCode || liveCode;
    $("#liveCode").value = liveCode;
    $("#connectLive").disabled = false;
    $("#connectLive").textContent = "Abrir";
    setMessage($("#liveOpenMessage"), `Sala ${liveCode} abierta correctamente.`, true);
    const stateQuestionId = state.pregunta?.id_partida_pregunta || null;
    const stateRequests = filterRequestsForQuestion(
        state.solicitudes || [],
        stateQuestionId
    );

    liveState = state;

    if (
        (pendingLiveAction === "pause" && state.partida?.estado === GAME_STATUS_PAUSED)
        || (pendingLiveAction === "resume" && state.partida?.estado === GAME_STATUS_IN_PROGRESS)
    ) {
        pendingLiveAction = "";
    }

    liveQuestionId = stateQuestionId;
    liveTotalQuestions = state.ranking?.total_questions || liveTotalQuestions;
    liveTimerRemaining = normalizedTimerValue(state.timer);
    liveTransitionActive = false;
    liveParticipants = state.participantes || [];
    liveRequests = activeRequests(stateRequests);
    renderCompetitionStatus(state);
    setMessage($("#waitingRoomMessage"), state.mensaje_estado || "Sala lista para recibir equipos.", true);
    renderTimer(
        $("#judgeTimer"),
        {
            ...(state.timer || {}),
            duration: state.partida?.tiempo_por_pregunta
        },
        $("#judgeTimerProgress")
    );
    handleTimerSound(state.timer, "judge");
    renderRanking($("#judgeRanking"), state.ranking);
    renderRequests(liveRequests, state);
    renderParticipants(liveParticipants);
    renderJudgeLayout();
    syncActiveGameSummary();

    if ([GAME_STATUS_IN_PROGRESS, GAME_STATUS_PAUSED].includes(state.partida?.estado) && state.pregunta) {
        renderJudgeQuestion(state.pregunta, "Pregunta actual.");
    } else if (state.partida?.estado === GAME_STATUS_FINISHED) {
        renderJudgeQuestion(null, "Competencia finalizada.");
    } else {
        renderJudgeQuestion(null, "Esperando que el juez inicie la competencia.");
    }

    if (
        pendingLiveAction === "finish-time"
        || state.partida?.estado === GAME_STATUS_FINISHED
    ) {
        clearPendingLiveAction();
    } else {
        updateLiveActionButtons();
    }
});

judgeSocket.on("error_sala", payload => {
    console.warn("No fue posible completar la acción de sala.", payload);
    $("#connectLive").disabled = false;
    $("#connectLive").textContent = "Abrir";
    clearPendingLiveAction();
    setMessage($("#liveOpenMessage"), payload?.message || "No fue posible abrir la sala.", false);
    setLiveMessage(payload?.message || "No fue posible completar la acción.", false);

    if (!liveState?.partida) {
        $("#liveConnectPanel").classList.remove("d-none");
    }
});

judgeSocket.on("resultado_accion", payload => {
    if (!payload?.success) {
        clearPendingLiveAction();
        setLiveMessage(payload?.message || "No fue posible completar la acción.", false);
        return;
    }

    setLiveMessage(payload.message || "Acción completada correctamente.", true);

    if (pendingLiveAction === "finish-time") {
        liveTimerRemaining = 0;
        liveState = {
            ...liveState,
            timer: {
                ...(liveState.timer || {}),
                remaining: 0,
                exhausted: true,
                active_since: null
            }
        };
        renderTimer($("#judgeTimer"), liveState.timer, $("#judgeTimerProgress"));
    }

    if (!["finish", "pause", "resume"].includes(pendingLiveAction)) {
        clearPendingLiveAction();
    }
});

judgeSocket.on("participante_eliminado_espera", payload => {
    const participantId = Number(payload?.id_participante);

    if (participantId) {
        pendingParticipantDeletions.delete(participantId);
    }

    if (!payload?.success) {
        renderWaitingRoom();
        setLiveMessage(payload?.message || "No fue posible eliminar el equipo.", false);
        return;
    }

    liveParticipants = liveParticipants.filter(
        item => Number(item.id_participante) !== participantId
    );
    renderWaitingRoom();
    syncActiveGameSummary();
    setLiveMessage(payload.message || "Equipo eliminado correctamente.", true);
});

judgeSocket.on("participante_conectado", payload => {
    const participant = payload?.participant || payload;

    if (
        participant?.id_partida
        && liveState?.partida?.id_partida
        && Number(participant.id_partida) !== Number(liveState.partida.id_partida)
    ) {
        return;
    }

    liveParticipants = upsertBy(
        liveParticipants,
        {...participant, conectado: 1},
        "codigo_participante"
    );
    renderParticipants(liveParticipants);
    renderWaitingRoom();
    syncActiveGameSummary();

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
    renderWaitingRoom();
    syncActiveGameSummary();

    if (payload?.ranking) {
        renderRanking($("#judgeRanking"), payload.ranking);
    }
});

judgeSocket.on("solicitud_palabra", payload => {
    playSound("request");
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

    liveRequests = activeRequests(liveRequests);
    renderRequests(liveRequests, liveState);
});

judgeSocket.on("palabra_otorgada", request => {
    playSound("turn");
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
    liveRequests = activeRequests(liveRequests);
    renderCompetitionStatus(liveState);
    renderRequests(liveRequests, liveState);
});

judgeSocket.on("respuesta_calificada", payload => {
    const request = payload?.request;

    if (!request) {
        return;
    }

    const correct = request.estado === "CORRECTA";
    playSound(correct ? "correct" : "incorrect");
    liveState = {
        ...liveState,
        estado_competencia: correct ? "Respuesta correcta" : "Respuesta incorrecta",
        mensaje_estado: correct
            ? "Respuesta correcta. Esperando siguiente pregunta."
            : "Respuesta incorrecta. Puede otorgar la palabra al siguiente equipo o esperar nuevas solicitudes."
    };
    liveRequests = Array.isArray(payload.affected_requests)
        ? activeRequests(filterRequestsForQuestion(payload.affected_requests))
        : activeRequests(filterRequestsForQuestion(
            liveRequests.filter(item => item.id_solicitud !== request.id_solicitud)
        ));
    if (payload?.timer) {
        liveTimerRemaining = normalizedTimerValue(payload.timer);
        liveState = {...liveState, timer: payload.timer};
        renderTimer($("#judgeTimer"), payload.timer, $("#judgeTimerProgress"));
        handleTimerSound(payload.timer, "judge");
    }
    renderCompetitionStatus(liveState);
    renderRequests(liveRequests, liveState);
    updateLiveActionButtons();
});

judgeSocket.on("actualizar_puntajes", ranking => {
    liveTotalQuestions = ranking?.total_questions || liveTotalQuestions;
    renderRanking($("#judgeRanking"), ranking);
    updateQuestionCounter($("#judgeQuestionNumber"));
});

judgeSocket.on("mostrar_podio", ranking => {
    playSound("finish");
    liveState = {
        ...liveState,
        partida: {
            ...(liveState.partida || {}),
            estado: GAME_STATUS_FINISHED
        },
        estado_competencia: "Competencia finalizada",
        mensaje_estado: "La competencia ha terminado."
    };
    liveTransitionActive = false;
    liveTimerRemaining = 0;
    clearPendingLiveAction();
    renderCompetitionStatus(liveState);
    renderRanking($("#judgeRanking"), ranking);
    renderJudgeQuestion(null, "Competencia finalizada.");
    renderJudgeLayout();
    syncActiveGameSummary();
});

judgeSocket.on("actualizar_cronometro", timer => {
    liveTimerRemaining = normalizedTimerValue(timer);
    liveState = {...liveState, timer};
    renderTimer($("#judgeTimer"), timer, $("#judgeTimerProgress"));
    handleTimerSound(timer, "judge");
    updateLiveActionButtons();
});

judgeSocket.on("estado_competencia", event => {
    if (event.contador === 5) {
        playSound("countdown");
    }
    if (event.estado === "Cuenta regresiva") {
        liveTransitionActive = true;
        renderJudgeLayout();
    }

    liveState = {
        ...liveState,
        estado_competencia: event.estado,
        mensaje_estado: event.mensaje
    };
    renderCompetitionStatus(event);
    renderJudgeQuestion(null, event.contador ? `${event.mensaje}` : event.mensaje);
    updateLiveActionButtons();
});

judgeSocket.on("mostrar_pregunta", question => {
    if (Number(question?.numero_orden) === 1) {
        playSound("start");
    }
    resetTimerSound("judge");
    liveTransitionActive = false;
    liveState = {
        ...liveState,
        partida: {
            ...(liveState.partida || {}),
            estado: GAME_STATUS_IN_PROGRESS,
            pregunta_actual: question?.numero_orden || liveState?.partida?.pregunta_actual
        },
        pregunta: question,
        estado_competencia: "Pregunta en curso",
        mensaje_estado: "Los equipos pueden pedir la palabra."
    };
    liveQuestionId = question?.id_partida_pregunta || null;
    liveRequests = [];
    renderRequests(liveRequests, {
        ...liveState,
        estado_competencia: "Pregunta en curso"
    });
    renderJudgeQuestion(question, "Pregunta actual.");
    renderJudgeLayout();
    syncActiveGameSummary();
});

const initialTab = window.location.hash.replace("#", "");

loadCatalogs()
    .then(refreshAll)
    .then(() => {
        resetGameForm({clearMessage: false, generateCode: true});
        if (["contenido", "partidas", "competencia", "historial"].includes(initialTab)) {
            showDashboardTab(initialTab, false);
        }
    })
    .catch(error => {
        console.warn("No fue posible cargar completamente el dashboard.", error);
        setMessage($("#partidaMessage"), "No fue posible cargar todos los datos. Actualiza la página e inténtalo de nuevo.", false);
    });


