(function exposeContentFilters(root, factory) {
    const filters = factory();

    if (typeof module !== "undefined" && module.exports) {
        module.exports = filters;
    }

    root.ContentFilters = filters;
}(typeof globalThis !== "undefined" ? globalThis : this, function createContentFilters() {
    function normalizeSearch(value) {
        return String(value ?? "")
            .trim()
            .replace(/\s+/g, " ")
            .toLocaleLowerCase("es");
    }

    function includesQuery(values, query) {
        const normalizedQuery = normalizeSearch(query);

        if (!normalizedQuery) {
            return true;
        }

        return normalizeSearch(values.join(" ")).includes(normalizedQuery);
    }

    function filterQuestionnaires(items, query) {
        return (items || []).filter(item => includesQuery([
            item?.nombre,
            item?.materia?.nombre,
            item?.area,
            item?.estado
        ], query));
    }

    function filterQuestions(records, query) {
        return (records || []).filter(record => includesQuery([
            record?.pregunta?.enunciado,
            record?.respuesta?.descripcion
        ], query));
    }

    return {
        normalizeSearch,
        filterQuestionnaires,
        filterQuestions
    };
}));
