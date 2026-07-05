const page = document.querySelector(".questionnaire-page");
const questionnaireId = page.dataset.questionnaireId;
const form = document.getElementById("questionDetailForm");
const list = document.getElementById("questionsList");
const message = document.getElementById("questionMessage");
let questionRecords = [];

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

function resetForm(clearMessage = true) {
    form.reset();
    form.id_pregunta.value = "";
    form.id_respuesta.value = "";
    form.id_cuestionario.value = questionnaireId;
    form.id_ruta_imagen.value = "";
    form.nombre_imagen.value = "";
    form.respuesta_id_ruta_imagen.value = "";
    form.respuesta_nombre_imagen.value = "";

    if (clearMessage) {
        setQuestionMessage("");
    }
}

function renderQuestions() {
    document.getElementById("questionCount").textContent = `${questionRecords.length} preguntas`;
    list.innerHTML = questionRecords.map((record, index) => {
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
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteQuestion(${pregunta.id_pregunta})">Eliminar</button>
                </div>
            </div>
        `;
    }).join("") || "<div class='text-secondary'>Este cuestionario aun no tiene preguntas.</div>";
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
            questionRecords = [];
            renderQuestions();
            setQuestionMessage(data?.message || "No fue posible cargar las preguntas.", false);
            return;
        }

        questionRecords = data;
        renderQuestions();
    });
}

function editQuestion(idPregunta) {
    const record = questionRecords.find(item => item.pregunta.id_pregunta === idPregunta);

    if (!record) {
        return;
    }

    form.id_pregunta.value = record.pregunta.id_pregunta;
    form.id_respuesta.value = record.respuesta?.id_respuesta || "";
    form.enunciado.value = record.pregunta.enunciado || "";
    form.nombre_imagen.value = record.pregunta.nombre_imagen || "";
    form.id_ruta_imagen.value = record.pregunta.ruta_imagen?.id_ruta || "";
    form.respuesta_descripcion.value = record.respuesta?.descripcion || "";
    form.respuesta_nombre_imagen.value = record.respuesta?.nombre_imagen || "";
    form.respuesta_id_ruta_imagen.value = record.respuesta?.ruta_imagen?.id_ruta || "";
    setQuestionMessage("Editando pregunta seleccionada.", true);
}

function deleteQuestion(idPregunta) {
    apiFetch(`/api/preguntas/${idPregunta}`, {method: "DELETE"}).then(payload => {
        if (!payload.success) {
            setQuestionMessage(payload.message || "No fue posible eliminar la pregunta.", false);
            return;
        }
        resetForm();
        questionRecords = questionRecords.filter(
            item => item.pregunta.id_pregunta !== idPregunta
        );
        renderQuestions();
    });
}

document.getElementById("newQuestion").addEventListener("click", resetForm);

form.addEventListener("submit", event => {
    event.preventDefault();
    setQuestionMessage("Guardando pregunta...", true);
    const wasEditing = Boolean(form.id_pregunta.value);
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
        });
});

loadQuestions();
