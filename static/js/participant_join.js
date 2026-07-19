const joinSocket = io({transports: ["websocket"]});
const joinForm = document.getElementById("joinForm");
const sedeSelect = document.getElementById("sede");
const joinMessage = document.getElementById("joinMessage");
const joinButton = document.getElementById("joinButton");
const removalMessage = sessionStorage.getItem("participantRemovalMessage");
let joinPending = false;

if (removalMessage) {
    joinMessage.textContent = removalMessage;
    joinMessage.classList.add("text-danger");
    sessionStorage.removeItem("participantRemovalMessage");
}

apiFetch("/api/catalogos").then(data => {
    sedeSelect.innerHTML = data.sedes
        .map(sede => `<option value="${escapeHtml(sede)}">${escapeHtml(sede)}</option>`)
        .join("");
});

joinForm.addEventListener("submit", event => {
    event.preventDefault();
    const data = formJson(joinForm);
    const hasTeamName = Boolean(data.nombre_equipo?.trim());
    const hasMembers = Boolean(data.integrantes?.trim());

    joinMessage.classList.remove("text-danger", "text-success");

    if (hasTeamName !== hasMembers) {
        joinMessage.textContent = "Para un primer ingreso completa nombre e integrantes; para reconectar, deja ambos vacíos.";
        joinMessage.classList.add("text-danger");
        return;
    }

    if (joinPending) {
        return;
    }

    joinPending = true;
    joinButton.disabled = true;
    data.codigo_partida = data.codigo_partida.toUpperCase();
    joinSocket.emit("participante_unirse", data);
    joinMessage.textContent = "Conectando con la sala...";
});

joinSocket.on("participante_registrado", payload => {
    const data = payload.data;
    localStorage.setItem("participantSession", JSON.stringify({
        codigo_partida: joinForm.codigo_partida.value.toUpperCase(),
        codigo_participante: data.codigo_participante,
        nombre_equipo: data.nombre,
        sede: data.sede
    }));
    sessionStorage.setItem(
        "participantJoinMessage",
        payload.message || (data.reconnected
            ? "Equipo reconectado correctamente."
            : "Equipo conectado correctamente.")
    );
    window.location.href = "/participante/sala";
});

joinSocket.on("error_sala", payload => {
    joinPending = false;
    joinButton.disabled = false;
    joinMessage.textContent = payload.message || "No fue posible unirse a la sala.";
    joinMessage.classList.add("text-danger");
});
