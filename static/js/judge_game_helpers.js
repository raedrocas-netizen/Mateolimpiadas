(function exposeJudgeGameHelpers(root, factory) {
    const filters = (
        typeof module !== "undefined" && module.exports
            ? require("./content_filters.js")
            : root.ContentFilters
    );
    const helpers = factory(filters);

    if (typeof module !== "undefined" && module.exports) {
        module.exports = helpers;
    }

    root.JudgeGameHelpers = helpers;
}(typeof globalThis !== "undefined" ? globalThis : this, function createJudgeGameHelpers(filters) {
    const ACTIVE_STATUS = "ACTIVO";
    const IN_PROGRESS_STATUS = "EN_CURSO";
    const PAUSED_STATUS = "PAUSADA";
    const ACTIVE_WORD_REQUEST_STATUSES = new Set(["EN_COLA", "EN_TURNO"]);
    const DEFAULT_SITE_IDENTITY = Object.freeze({
        key: "default",
        accent: "#2563eb",
        tint: "#f4f7fb",
        detail: "#1e3a5f"
    });
    const SITE_IDENTITIES = Object.freeze({
        petapa: Object.freeze({
            key: "petapa",
            accent: "#d4a900",
            tint: "#fff5bf",
            detail: "#705700"
        }),
        "villa nueva": Object.freeze({
            key: "villa-nueva",
            accent: "#23834b",
            tint: "#e5f7ec",
            detail: "#14532d"
        }),
        "san cristobal": Object.freeze({
            key: "san-cristobal",
            accent: "#c83e48",
            tint: "#ffe8ea",
            detail: "#7f1d2d"
        }),
        antigua: Object.freeze({
            key: "antigua",
            accent: "#7c3fb4",
            tint: "#f4e8ff",
            detail: "#581c87"
        }),
        naranjo: Object.freeze({
            key: "naranjo",
            accent: "#e87920",
            tint: "#ffead7",
            detail: "#9a3412"
        }),
        "aguilar batres": Object.freeze({
            key: "aguilar-batres",
            accent: "#2d9fc5",
            tint: "#e1f6fd",
            detail: "#075985"
        }),
        "san juan": Object.freeze({
            key: "san-juan",
            accent: "#173f73",
            tint: "#e5edf8",
            detail: "#172f55"
        }),
        amatitlan: Object.freeze({
            key: "amatitlan",
            accent: "#8b2635",
            tint: "#fff2dc",
            detail: "#701f2b"
        })
    });

    function normalizedId(value) {
        return String(value ?? "");
    }

    function activeQuestionnaires(items) {
        return (items || []).filter(item => item?.estado === ACTIVE_STATUS);
    }

    function filterActiveQuestionnaires(items, query) {
        return filters.filterQuestionnaires(activeQuestionnaires(items), query);
    }

    function teamSiteIdentity(site) {
        const normalizedSite = filters.normalizeSearch(site);
        return SITE_IDENTITIES[normalizedSite] || DEFAULT_SITE_IDENTITY;
    }

    function activeWordRequests(items) {
        const uniqueRequests = new Map();

        (items || []).forEach(item => {
            if (
                !item?.id_solicitud
                || !ACTIVE_WORD_REQUEST_STATUSES.has(item.estado)
            ) {
                return;
            }

            uniqueRequests.set(String(item.id_solicitud), item);
        });

        return [...uniqueRequests.values()].sort((a, b) => (
            Number(a.orden_solicitud || 0) - Number(b.orden_solicitud || 0)
        ));
    }

    function questionnaireSelectionState(
        items,
        selectedIds,
        areaSelectedManually = false,
        currentArea = ""
    ) {
        const normalizedSelection = new Set(
            Array.from(selectedIds || [], normalizedId)
        );
        const selected = activeQuestionnaires(items).filter(item => (
            normalizedSelection.has(normalizedId(item.id_cuestionario))
        ));
        const areas = [...new Set(
            selected.map(item => String(item.area || "").trim()).filter(Boolean)
        )];
        let area = String(currentArea || "");
        let inferred = false;
        let requiresManualArea = false;

        if (!areaSelectedManually) {
            if (areas.length === 1) {
                [area] = areas;
                inferred = true;
            } else {
                area = "";
                requiresManualArea = areas.length > 1;
            }
        }

        return {
            area,
            areas,
            inferred,
            requiresManualArea,
            selected,
            selectedCount: selected.length
        };
    }

    function nextQuestionAction({
        gameState,
        remaining,
        currentQuestion,
        totalQuestions,
        transitionActive = false
    } = {}) {
        if (transitionActive || gameState !== IN_PROGRESS_STATUS) {
            return "blocked";
        }

        if (Number(remaining) > 0) {
            return "finish_time";
        }

        const current = Number(currentQuestion || 0);
        const total = Number(totalQuestions || 0);

        if (total > 0 && current >= total) {
            return "finish_game";
        }

        return "advance";
    }

    function competitionControlState({
        gameState,
        hasQuestion = false,
        questionState = "",
        remaining = 0,
        transitionActive = false,
        pendingAction = ""
    } = {}) {
        const inProgress = gameState === IN_PROGRESS_STATUS;
        const paused = gameState === PAUSED_STATUS;
        const busy = transitionActive || Boolean(pendingAction);
        const activeQuestion = (
            hasQuestion
            && questionState === "ACTUAL"
            && Number(remaining) > 0
        );
        let pauseResumeAction = "blocked";

        if (!busy && paused) {
            pauseResumeAction = "resume";
        } else if (!busy && inProgress && activeQuestion) {
            pauseResumeAction = "pause";
        }

        return {
            busy,
            inProgress,
            paused,
            activeQuestion,
            pauseResumeAction,
            showPauseResume: paused || (
                inProgress
                && activeQuestion
                && !transitionActive
            ),
            canNext: inProgress && !busy,
            canFinish: (inProgress || paused) && !busy,
            canModifyQuestion: inProgress && !busy
        };
    }

    function gameActionLabel(status) {
        const labels = {
            ESPERANDO: "Abrir sala",
            EN_CURSO: "Volver a competencia",
            PAUSADA: "Volver a competencia",
            FINALIZADA: "Ver resultados"
        };

        return labels[status] || "Abrir";
    }

    function activeRoomCode(game) {
        return String(game?.codigo_partida || "").trim().toUpperCase();
    }

    function activeRoomName(game) {
        return String(game?.nombre || "").trim() || "Competencia";
    }

    return {
        ACTIVE_STATUS,
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
    };
}));
