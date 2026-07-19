const test = require("node:test");
const assert = require("node:assert/strict");

const {
    filterQuestionnaires,
    filterQuestions,
    normalizeSearch
} = require("../static/js/content_filters.js");

const questionnaires = [
    {
        nombre: "  Álgebra básica  ",
        materia: {nombre: "Matemática"},
        area: "Básicos",
        estado: "ACTIVO"
    },
    {
        nombre: "Ciencias naturales",
        materia: {nombre: "Ciencias"},
        area: "Primaria",
        estado: "BORRADOR"
    }
];

const questions = [
    {
        pregunta: {enunciado: "¿Cuánto es dos más dos?"},
        respuesta: {descripcion: "Cuatro"}
    },
    {
        pregunta: {enunciado: "Capital de Guatemala"},
        respuesta: {descripcion: "Ciudad de Guatemala"}
    }
];

test("normaliza mayúsculas y espacios innecesarios", () => {
    assert.equal(normalizeSearch("  ÁLGEBRA   BÁSICA "), "algebra basica");
});

test("filtra cuestionarios por todos sus campos", () => {
    assert.equal(filterQuestionnaires(questionnaires, "algebra").length, 1);
    assert.equal(filterQuestionnaires(questionnaires, "matematica").length, 1);
    assert.equal(filterQuestionnaires(questionnaires, "BASICOS").length, 1);
    assert.equal(filterQuestionnaires(questionnaires, "primaria").length, 1);
    assert.equal(filterQuestionnaires(questionnaires, "borrador").length, 1);
});

test("una búsqueda vacía restaura todos los cuestionarios", () => {
    assert.equal(filterQuestionnaires(questionnaires, "   ").length, 2);
});

test("filtra preguntas por enunciado y respuesta", () => {
    assert.equal(filterQuestions(questions, "dos mas dos").length, 1);
    assert.equal(filterQuestions(questions, "CUATRO").length, 1);
    assert.equal(filterQuestions(questions, "ciudad de guatemala").length, 1);
});
