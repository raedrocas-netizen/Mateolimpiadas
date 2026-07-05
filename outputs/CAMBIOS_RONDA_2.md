# Cambios ronda 2

## Apertura de sala

- Abrir una sala ya no inicia ni muestra la primera pregunta.
- El estado inicial muestra que la sala esta abierta y esperando inicio del juez.

## Inicio de competencia

- Al presionar `Iniciar competencia`, el servidor emite una cuenta regresiva 5, 4, 3, 2, 1 por Socket.IO.
- La partida se inicia en base de datos despues de la cuenta regresiva.
- La primera pregunta y el cronometro se muestran solo despues de finalizar la cuenta regresiva.

## Estados visibles

- Se agregaron estados sincronizados:
  - Sala abierta
  - Esperando participantes
  - Cuenta regresiva
  - Pregunta en curso
  - Esperando respuesta
  - Competencia finalizada

## Participantes conectados

- El panel del juez ahora muestra los equipos conectados en tiempo real.
- Cada union de participante emite nuevamente el estado de sala a jueces y participantes conectados.

## Sedes

- Se corrigio la carga del selector de sedes en el formulario de participante.
- El formulario usa `/api/catalogos`, alimentado desde `helper/super_global.py`, sin duplicar listas.

## Verificacion

- Busqueda estatica limpia de referencias viejas o texto roto en los archivos modificados.
- No fue posible ejecutar Python/Node en este entorno porque no estan instalados/disponibles.
