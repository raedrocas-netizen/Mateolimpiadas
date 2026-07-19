const joinSocket = io({transports: ["websocket"]});
const joinForm = document.getElementById("joinForm");
const sedeSelect = document.getElementById("sede");
const joinMessage = document.getElementById("joinMessage");
const removalMessage = sessionStorage.getItem("participantRemovalMessage");

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
    joinMessage.classList.remove("text-danger");
    const data = formJson(joinForm);
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
    window.location.href = "/participante/sala";
});

joinSocket.on("error_sala", payload => {
    joinMessage.textContent = payload.message || "No fue posible unirse a la sala.";
});
