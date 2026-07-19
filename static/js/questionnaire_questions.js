const page = document.querySelector(".questionnaire-page");
const questionnaireId = page.dataset.questionnaireId;
const form = document.getElementById("questionDetailForm");
const list = document.getElementById("questionsList");
const message = document.getElementById("questionMessage");
const cancelEditButton = document.getElementById("cancelQuestionEdit");
const clearFieldsButton = document.getElementById("clearQuestionFields");
const questionSubmitButton = document.getElementById("questionSubmit");
const questionSearch = document.getElementById("questionSearch");
const clearQuestionSearch = document.getElementById("clearQuestionSearch");
const refreshQuestionsButton = document.getElementById("refreshQuestions");
let questionRecords = [];

const imageModalElement = document.getElementById("imagePreviewModal");
const imageModal = bootstrap.Modal.getOrCreateInstance(imageModalElement);
const imageModalName = document.getElementById("imagePreviewModalName");
const imageModalImage = document.getElementById("imagePreviewModalImage");
const imageModalDownload = document.getElementById("imagePreviewModalDownload");
const ALLOWED_IMAGE_EXTENSIONS = new Set([
    ".png",
    ".jpg",
    ".jpeg",
    ".jfif",
    ".webp",
    ".gif",
    ".avif"
]);
const imagePreviews = {
    question: createImagePreview(
        "question",
        form.elements.imagen,
        form.elements.id_ruta_imagen,
        form.elements.nombre_imagen,
        "Imagen de pregunta"
    ),
    answer: createImagePreview(
        "answer",
        form.elements.respuesta_imagen,
        form.elements.respuesta_id_ruta_imagen,
        form.elements.respuesta_nombre_imagen,
        "Imagen de respuesta esperada"
    )
};

function createImagePreview(key, input, routeInput, nameInput, altText) {
    const root = document.querySelector(`[data-image-preview="${key}"]`);
    const preview = {
        key,
        input,
        routeInput,
        nameInput,
        altText,
        root,
        empty: root.querySelector("[data-preview-empty]"),
        file: root.querySelector("[data-preview-file]"),
        thumbnail: root.querySelector("[data-preview-thumbnail]"),
        name: root.querySelector("[data-preview-name]"),
        download: root.querySelector("[data-preview-download]"),
        remove: root.querySelector("[data-preview-remove]"),
        pending: root.querySelector("[data-preview-pending]"),
        url: "",
        fileName: "",
        objectUrl: "",
        savedUrl: "",
        savedFileName: "",
        savedRouteId: "",
        removeRequested: false
    };

    root.querySelectorAll("[data-preview-open]").forEach(control => {
        control.addEventListener("click", () => openImageModal(preview));
    });
    preview.remove.addEventListener("click", () => removeImage(preview));
    input.addEventListener("change", () => previewSelectedImage(preview));
    return preview;
}

function revokeObjectUrl(preview) {
    if (!preview.objectUrl) {
        return;
    }

    URL.revokeObjectURL(preview.objectUrl);
    preview.objectUrl = "";
}

function setImagePreview(preview, url = "", fileName = "", objectUrl = false) {
    revokeObjectUrl(preview);
    preview.url = url || "";
    preview.fileName = fileName || "Imagen";
    preview.objectUrl = objectUrl ? preview.url : "";
    preview.removeRequested = false;
    preview.pending.classList.add("d-none");

    if (!preview.url) {
        preview.thumbnail.removeAttribute("src");
        preview.name.textContent = "";
        preview.name.removeAttribute("title");
        preview.download.removeAttribute("href");
        preview.download.removeAttribute("download");
        preview.file.classList.add("d-none");
        preview.empty.classList.remove("d-none");
        return;
    }

    preview.thumbnail.src = preview.url;
    preview.thumbnail.alt = `${preview.altText}: ${preview.fileName}`;
    preview.name.textContent = preview.fileName;
    preview.name.title = preview.fileName;
    preview.download.href = preview.url;
    preview.download.download = preview.fileName;
    preview.empty.classList.add("d-none");
    preview.file.classList.remove("d-none");
}

function setPendingRemoval(preview) {
    revokeObjectUrl(preview);
    preview.input.value = "";
    preview.routeInput.value = "";
    preview.nameInput.value = "";
    preview.url = "";
    preview.fileName = "";
    preview.removeRequested = true;
    preview.thumbnail.removeAttribute("src");
    preview.name.textContent = "";
    preview.download.removeAttribute("href");
    preview.download.removeAttribute("download");
    preview.file.classList.add("d-none");
    preview.empty.classList.add("d-none");
    preview.pending.classList.remove("d-none");
}

function clearImagePreview(preview) {
    preview.savedUrl = "";
    preview.savedFileName = "";
    preview.savedRouteId = "";
    setImagePreview(preview);
}

function setSavedImagePreview(preview, url = "", fileName = "", routeId = "") {
    preview.savedUrl = url || "";
    preview.savedFileName = fileName || "";
    preview.savedRouteId = routeId || "";
    setImagePreview(preview, preview.savedUrl, preview.savedFileName);
}

function restoreSavedImage(preview) {
    preview.routeInput.value = preview.savedRouteId;
    preview.nameInput.value = preview.savedFileName;
    setImagePreview(preview, preview.savedUrl, preview.savedFileName);
}

function removeImage(preview) {
    if (preview.objectUrl) {
        preview.input.value = "";
        restoreSavedImage(preview);
        setQuestionMessage(
            preview.savedUrl
                ? "Se descartó la imagen seleccionada y se restauró la imagen guardada."
                : "Se quitó la imagen seleccionada.",
            true
        );
        return;
    }

    if (!preview.savedUrl || preview.removeRequested) {
        return;
    }

    const confirmed = window.confirm(
        "¿Quitar esta imagen?\n\nLa imagen se quitará cuando guardes los cambios."
    );

    if (!confirmed) {
        return;
    }

    setPendingRemoval(preview);
    setQuestionMessage("La imagen se quitará cuando guardes los cambios.", true);
}

function previewSelectedImage(preview) {
    const file = preview.input.files?.[0];

    if (!file) {
        return;
    }

    const extensionIndex = file.name.lastIndexOf(".");
    const extension = extensionIndex >= 0
        ? file.name.slice(extensionIndex).toLocaleLowerCase("en")
        : "";

    if (!ALLOWED_IMAGE_EXTENSIONS.has(extension)) {
        preview.input.value = "";
        restoreSavedImage(preview);
        setQuestionMessage(`El formato de "${file.name}" no esta permitido.`, false);
        return;
    }

    const objectUrl = URL.createObjectURL(file);
    setImagePreview(preview, objectUrl, file.name, true);
    setQuestionMessage(`Vista previa lista: ${file.name}`, true);
}

function openImageModal(preview) {
    if (!preview.url) {
        return;
    }

    imageModalName.textContent = preview.fileName;
    imageModalImage.src = preview.url;
    imageModalImage.alt = `${preview.altText} ampliada: ${preview.fileName}`;
    imageModalDownload.href = preview.url;
    imageModalDownload.download = preview.fileName;
    imageModal.show();
}

function setQuestionMessage(text, success = true) {
    message.textContent = text || "";
    message.classList.toggle("text-danger", !success);
    message.classList.toggle("text-success", success);
}

function uploadImage(input) {
    if (!input || !input.files || input.files.length === 0) {
        return Promise.resolve(null);
    }

    const body = new FormData();
    body.append("imagen", input.files[0]);

    return fetch("/api/imagenes", {
        method: "POST",
        body
    })
        .then(response => response.json())
        .then(payload => {
            if (!payload.success) {
                throw new Error(payload.message || "No fue posible cargar la imagen.");
            }

            return payload.data;
        });
}

function setQuestionFormMode(editing) {
    questionSubmitButton.textContent = editing ? "Guardar cambios" : "Agregar pregunta";
    cancelEditButton.classList.toggle("d-none", !editing);
    clearFieldsButton.classList.toggle("d-none", editing);
}

function resetForm(clearMessage = true) {
    form.reset();
    form.id_pregunta.value = "";
    form.id_respuesta.value = "";
    form.id_cuestionario.value = questionnaireId;
    form.id_ruta_imagen.value = "";
    form.nombre_imagen.value = "";
    form.respuesta_id_ruta_imagen.value = "";
    form.respuesta_nombre_imagen.value = "";
    clearImagePreview(imagePreviews.question);
    clearImagePreview(imagePreviews.answer);
    setQuestionFormMode(false);

    if (clearMessage) {
        setQuestionMessage("");
    }
}

function renderQuestions() {
    const search = questionSearch.value;
    const filteredRecords = ContentFilters.filterQuestions(questionRecords, search);
    const hasSearch = Boolean(ContentFilters.normalizeSearch(search));
    document.getElementById("questionCount").textContent = hasSearch
        ? `${filteredRecords.length} de ${questionRecords.length} preguntas`
        : `${questionRecords.length} preguntas`;
    clearQuestionSearch.disabled = !hasSearch;
    list.innerHTML = filteredRecords.map((record, index) => {
        const pregunta = record.pregunta;
        const respuesta = record.respuesta;
        return `
            <div class="list-row question-row">
                <div>
                    <strong>${index + 1}. ${escapeHtml(pregunta.enunciado)}</strong>
                    <small>Respuesta: ${escapeHtml(respuesta?.descripcion || "Pendiente")}</small>
                </div>
                <div class="d-flex gap-2">
                    <button class="btn btn-sm btn-outline-secondary" onclick="editQuestion(${pregunta.id_pregunta})">Editar</button>
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteQuestion(${pregunta.id_pregunta}, this)">Eliminar</button>
                </div>
            </div>
        `;
    }).join("") || (
        hasSearch
            ? "<div class='text-secondary'>No hay preguntas que coincidan con la búsqueda.</div>"
            : "<div class='text-secondary'>Este cuestionario aún no tiene preguntas.</div>"
    );
}

function upsertQuestionRecord(record) {
    const idPregunta = record?.pregunta?.id_pregunta;

    if (!idPregunta) {
        return;
    }

    const index = questionRecords.findIndex(
        item => item.pregunta.id_pregunta === idPregunta
    );

    if (index >= 0) {
        questionRecords[index] = record;
    } else {
        questionRecords.push(record);
    }

    renderQuestions();
}

function loadQuestions() {
    return apiFetch(`/api/cuestionarios/${questionnaireId}/preguntas-detalle`).then(data => {
        if (!Array.isArray(data)) {
            throw new Error(data?.message || "No fue posible cargar las preguntas.");
        }

        questionRecords = data;
        renderQuestions();
        return data;
    });
}

function editQuestion(idPregunta) {
    const record = questionRecords.find(item => item.pregunta.id_pregunta === idPregunta);

    if (!record) {
        return;
    }

    resetForm(false);
    form.id_pregunta.value = record.pregunta.id_pregunta;
    form.id_respuesta.value = record.respuesta?.id_respuesta || "";
    form.enunciado.value = record.pregunta.enunciado || "";
    form.nombre_imagen.value = record.pregunta.nombre_imagen || "";
    form.id_ruta_imagen.value = record.pregunta.ruta_imagen?.id_ruta || "";
    form.respuesta_descripcion.value = record.respuesta?.descripcion || "";
    form.respuesta_nombre_imagen.value = record.respuesta?.nombre_imagen || "";
    form.respuesta_id_ruta_imagen.value = record.respuesta?.ruta_imagen?.id_ruta || "";
    setSavedImagePreview(
        imagePreviews.question,
        record.pregunta.imagen || "",
        record.pregunta.nombre_imagen || "",
        record.pregunta.ruta_imagen?.id_ruta || ""
    );
    setSavedImagePreview(
        imagePreviews.answer,
        record.respuesta?.imagen || "",
        record.respuesta?.nombre_imagen || "",
        record.respuesta?.ruta_imagen?.id_ruta || ""
    );
    setQuestionFormMode(true);
    setQuestionMessage("Editando pregunta seleccionada.", true);
}

function questionFragment(idPregunta) {
    const record = questionRecords.find(item => item.pregunta.id_pregunta === idPregunta);
    const statement = String(record?.pregunta?.enunciado || "esta pregunta")
        .replace(/\s+/g, " ")
        .trim();

    return statement.length > 120
        ? `${statement.slice(0, 117)}...`
        : statement;
}

async function deleteQuestion(idPregunta, button) {
    if (button?.disabled) {
        return;
    }

    const fragment = questionFragment(idPregunta);
    const confirmed = window.confirm(
        `¿Eliminar la pregunta "${fragment}"?\n\nEsta accion no se puede deshacer.`
    );

    if (!confirmed) {
        return;
    }

    const originalText = button?.textContent || "Eliminar";

    if (button) {
        button.disabled = true;
        button.textContent = "Eliminando...";
    }
    setQuestionMessage("Eliminando pregunta...", true);

    try {
        const payload = await apiFetch(`/api/preguntas/${idPregunta}`, {method: "DELETE"});

        if (!payload.success) {
            setQuestionMessage(payload.message || "No fue posible eliminar la pregunta.", false);
            return;
        }

        questionRecords = questionRecords.filter(
            item => item.pregunta.id_pregunta !== idPregunta
        );

        if (Number(form.id_pregunta.value) === Number(idPregunta)) {
            resetForm(false);
        }

        renderQuestions();
        setQuestionMessage(payload.message || "Pregunta eliminada correctamente.", true);
    } catch (error) {
        setQuestionMessage(
            "No fue posible comunicarse con el servidor para eliminar la pregunta.",
            false
        );
    } finally {
        if (button?.isConnected) {
            button.disabled = false;
            button.textContent = originalText;
        }
    }
}

document.getElementById("newQuestion").addEventListener("click", () => {
    resetForm();
    form.enunciado.focus();
});
cancelEditButton.addEventListener("click", () => {
    resetForm(false);
    setQuestionMessage("Edición cancelada. Formulario listo para crear una pregunta.", true);
    form.enunciado.focus();
});

clearFieldsButton.addEventListener("click", () => {
    resetForm(false);
    setQuestionMessage("Campos limpiados.", true);
    form.enunciado.focus();
});

questionSearch.addEventListener("input", renderQuestions);

clearQuestionSearch.addEventListener("click", () => {
    questionSearch.value = "";
    renderQuestions();
    questionSearch.focus();
});

refreshQuestionsButton.addEventListener("click", async () => {
    refreshQuestionsButton.disabled = true;
    refreshQuestionsButton.textContent = "Actualizando...";
    setQuestionMessage("Actualizando lista de preguntas...", true);

    try {
        await loadQuestions();
        setQuestionMessage("Lista de preguntas actualizada.", true);
    } catch (error) {
        setQuestionMessage(
            error.message || "No fue posible actualizar las preguntas.",
            false
        );
    } finally {
        refreshQuestionsButton.disabled = false;
        refreshQuestionsButton.textContent = "Actualizar";
    }
});

form.addEventListener("submit", event => {
    event.preventDefault();
    const wasEditing = Boolean(form.id_pregunta.value);
    questionSubmitButton.disabled = true;
    questionSubmitButton.textContent = wasEditing ? "Guardando cambios..." : "Agregando pregunta...";
    setQuestionMessage("Guardando pregunta...", true);
    let savedQuestionId = form.id_pregunta.value || "";
    let savedQuestion = null;

    Promise.all([
        uploadImage(form.querySelector('input[name="imagen"]')),
        uploadImage(form.querySelector('input[name="respuesta_imagen"]'))
    ])
        .then(([questionImage, answerImage]) => {
            if (questionImage) {
                form.id_ruta_imagen.value = questionImage.id_ruta_imagen || "";
                form.nombre_imagen.value = questionImage.nombre_imagen || "";
            }

            if (answerImage) {
                form.respuesta_id_ruta_imagen.value = answerImage.id_ruta_imagen || "";
                form.respuesta_nombre_imagen.value = answerImage.nombre_imagen || "";
            }

            const questionPayload = {
                id_cuestionario: questionnaireId,
                enunciado: form.enunciado.value,
                id_ruta_imagen: form.id_ruta_imagen.value,
                nombre_imagen: form.nombre_imagen.value
            };

            const questionUrl = form.id_pregunta.value
                ? `/api/preguntas/${form.id_pregunta.value}`
                : "/api/preguntas";

            return apiFetch(questionUrl, {
                method: form.id_pregunta.value ? "PUT" : "POST",
                body: JSON.stringify(questionPayload)
            });
        })
        .then(questionResult => {
            if (!questionResult.success) {
                throw new Error(questionResult.message || "No fue posible guardar la pregunta.");
            }

            const pregunta = questionResult.data || {};
            const idPregunta = form.id_pregunta.value || pregunta.id_pregunta;
            savedQuestionId = idPregunta;
            savedQuestion = pregunta;

            if (!idPregunta) {
                throw new Error("La pregunta se guardo, pero no se recibio su identificador.");
            }

            const answerPayload = {
                id_pregunta: idPregunta,
                descripcion: form.respuesta_descripcion.value,
                id_ruta_imagen: form.respuesta_id_ruta_imagen.value,
                nombre_imagen: form.respuesta_nombre_imagen.value
            };

            const answerUrl = form.id_respuesta.value
                ? `/api/respuestas/${form.id_respuesta.value}`
                : "/api/respuestas";

            return apiFetch(answerUrl, {
                method: form.id_respuesta.value ? "PUT" : "POST",
                body: JSON.stringify(answerPayload)
            });
        })
        .then(answerResult => {
            if (!answerResult.success) {
                throw new Error(answerResult.message || "La pregunta se guardo, pero falta revisar la respuesta.");
            }

            upsertQuestionRecord({
                pregunta: savedQuestion,
                respuesta: answerResult.data || null
            });
            setQuestionMessage("Pregunta y respuesta guardadas correctamente.", true);
            resetForm(false);
        })
        .catch(error => {
            if (!wasEditing && savedQuestionId) {
                apiFetch(`/api/preguntas/${savedQuestionId}`, {method: "DELETE"})
                    .finally(() => {
                        setQuestionMessage(error.message, false);
                        questionRecords = questionRecords.filter(
                            item => item.pregunta.id_pregunta !== Number(savedQuestionId)
                        );
                        renderQuestions();
                    });
                return;
            }

            setQuestionMessage(error.message, false);
        })
        .finally(() => {
            questionSubmitButton.disabled = false;
            setQuestionFormMode(Boolean(form.id_pregunta.value));
        });
});

loadQuestions().catch(error => {
    setQuestionMessage(error.message || "No fue posible cargar las preguntas.", false);
});

window.addEventListener("beforeunload", () => {
    Object.values(imagePreviews).forEach(revokeObjectUrl);
});
