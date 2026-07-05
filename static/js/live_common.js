function escapeHtml(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function apiFetch(url, options = {}) {
    const finalOptions = {
        headers: {"Content-Type": "application/json"},
        ...options
    };
    return fetch(url, finalOptions).then(response => response.json());
}

function formJson(form) {
    const data = {};
    new FormData(form).forEach((value, key) => {
        if (value instanceof File) {
            return;
        }

        if (data[key]) {
            data[key] = Array.isArray(data[key]) ? data[key] : [data[key]];
            data[key].push(value);
        } else {
            data[key] = value;
        }
    });
    return data;
}

function renderRanking(target, rankingData) {
    const ranking = rankingData?.ranking || [];
    target.innerHTML = ranking.map((item, index) => `
        <div class="list-row podium-row">
            <div>
                <strong>${index + 1}. ${escapeHtml(item.sede || item.nombre)}</strong>
                <small>${escapeHtml(item.nombre || "")}</small>
            </div>
            <span class="badge text-bg-primary">${item.puntaje} pts</span>
        </div>
    `).join("") || "<div class='text-secondary'>Sin puntajes registrados.</div>";
}

function renderTimer(target, timer) {
    target.textContent = timer?.remaining ?? "--";
}
