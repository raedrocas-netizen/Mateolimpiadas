from flask import request, session
from flask_socketio import emit, join_room
from uuid import uuid4

from helpers.serializers import (
    business_result_to_dict,
    game_question_to_dict,
    partida_to_dict,
    serialize_any
)
from helpers.performance import measure, performance_operation, socket_event_performance
from logical_business.partida_business import PartidaBusiness


active_timer_tokens = {}
connected_participants = {}


def game_room(game_code):
    return f"game:{str(game_code).strip().upper()}"


def judge_room(game_code):
    return f"judge:{str(game_code).strip().upper()}"


def display_room(game_code):
    return f"display:{str(game_code).strip().upper()}"


def participant_room(participant_code):
    return f"participant:{participant_code}"


def live_rooms(game_code):
    return (
        game_room(game_code),
        judge_room(game_code)
    )


def emit_live_event(socketio, event, payload, game_code):
    for room in live_rooms(game_code):
        with measure("SocketIO"):
            socketio.emit(event, payload, room=room)

    if event in (
            "actualizar_cronometro",
            "estado_competencia",
            "actualizar_puntajes",
            "mostrar_podio"
    ):
        with measure("SocketIO"):
            socketio.emit(event, payload, room=display_room(game_code))


def emit_question(socketio, question, game_code):
    public_question = game_question_to_dict(question, include_answer=False)
    with measure("SocketIO"):
        socketio.emit(
            "mostrar_pregunta",
            public_question,
            room=game_room(game_code)
        )
    with measure("SocketIO"):
        socketio.emit(
            "mostrar_pregunta",
            public_question,
            room=display_room(game_code)
        )
    with measure("SocketIO"):
        socketio.emit(
            "mostrar_pregunta",
            game_question_to_dict(question, include_answer=True),
            room=judge_room(game_code)
        )


def emit_to_judge(socketio, event, payload, game_code):
    with measure("SocketIO"):
        socketio.emit(
            event,
            payload,
            room=judge_room(game_code)
        )


def emit_to_display(socketio, event, payload, game_code):
    with measure("SocketIO"):
        socketio.emit(
            event,
            payload,
            room=display_room(game_code)
        )


def emit_to_participant(socketio, event, payload, participant_code):
    with measure("SocketIO"):
        socketio.emit(
            event,
            payload,
            room=participant_room(participant_code)
        )


def stop_timer(game_code):
    active_timer_tokens[str(game_code).strip().upper()] = None


def judge_authenticated():
    return session.get("judge_authenticated") is True


def reject_non_judge():
    if judge_authenticated():
        return False

    emit("error_sala", {"message": "Debe iniciar sesion como juez."})
    return True


def get_competition_status(partida, participantes, solicitudes, pregunta=None):
    estado = partida.get("estado") if isinstance(partida, dict) else None
    connected = [
        participant
        for participant in participantes
        if participant.get("conectado") == 1
    ]

    if estado in ("BORRADOR", "ESPERANDO"):
        if connected:
            return {
                "estado": "Sala abierta",
                "mensaje": "Esperando que el juez inicie la competencia."
            }

        return {
            "estado": "Esperando participantes",
            "mensaje": "La sala esta abierta para que los equipos se unan."
        }

    if estado == "EN_CURSO":
        current_question_id = (
            pregunta.get("id_partida_pregunta")
            if pregunta
            else None
        )
        current_requests = [
            request
            for request in solicitudes
            if (
                    current_question_id is None
                    or request.get("id_partida_pregunta") == current_question_id
            )
        ]
        active_turn = any(
            request.get("estado") == "EN_TURNO"
            for request in current_requests
        )
        correct_answer = any(
            request.get("estado") == "CORRECTA"
            for request in current_requests
        )
        incorrect_answer = any(
            request.get("estado") == "INCORRECTA"
            for request in current_requests
        )

        if active_turn:
            return {
                "estado": "Esperando respuesta",
                "mensaje": "Un equipo tiene la palabra."
            }

        if pregunta and pregunta.get("estado") == "CONTESTADA":
            return {
                "estado": "Respuesta correcta",
                "mensaje": "Respuesta correcta. Esperando siguiente pregunta."
            }

        if pregunta and pregunta.get("estado") == "SIN_RESPUESTA":
            answer_status = "Respuesta incorrecta" if incorrect_answer else "Esperando siguiente pregunta"
            return {
                "estado": answer_status,
                "mensaje": f"{answer_status}. Esperando siguiente pregunta."
            }

        if correct_answer:
            return {
                "estado": "Respuesta correcta",
                "mensaje": "Respuesta correcta. Esperando siguiente pregunta."
            }

        if incorrect_answer:
            return {
                "estado": "Respuesta incorrecta",
                "mensaje": "Respuesta incorrecta. Esperando siguiente pregunta."
            }

        return {
            "estado": "Pregunta en curso",
            "mensaje": "Los equipos pueden pedir la palabra."
        }

    if estado == "FINALIZADA":
        return {
            "estado": "Competencia finalizada",
            "mensaje": "La competencia ha terminado."
        }

    return {
        "estado": estado or "Sala abierta",
        "mensaje": "Estado de competencia actualizado."
    }


def filter_current_question_requests(solicitudes, pregunta):
    current_question_id = (
        pregunta.get("id_partida_pregunta")
        if isinstance(pregunta, dict)
        else None
    )

    if current_question_id is None:
        return []

    current_question_id = str(current_question_id)

    return [
        request
        for request in solicitudes
        if str(request.get("id_partida_pregunta")) == current_question_id
    ]


def build_live_state(game_code, include_answer=False):
    business = PartidaBusiness()
    partida = business.get_by_code(str(game_code or "").strip().upper())

    if partida is None:
        return None

    id_partida = partida.get_id_partida()
    partida_data = partida_to_dict(partida)
    participantes = serialize_any(business.get_waiting_room_status(id_partida))
    pregunta = game_question_to_dict(
        business.get_current_question(id_partida),
        include_answer=include_answer
    )
    solicitudes = filter_current_question_requests(
        serialize_any(business.get_word_requests(id_partida)),
        pregunta
    )
    status = get_competition_status(
        partida_data,
        participantes,
        solicitudes,
        pregunta
    )

    return {
        "partida": partida_data,
        "participantes": participantes,
        "pregunta": pregunta,
        "solicitudes": solicitudes,
        "ranking": serialize_any(business.get_live_ranking(partida.get_codigo_partida())),
        "timer": serialize_any(business.get_timer_status(id_partida)),
        "estado_competencia": status["estado"],
        "mensaje_estado": status["mensaje"]
    }


def emit_state(socketio, game_code):
    judge_state = build_live_state(game_code, include_answer=True)

    if judge_state is not None:
        participant_state = {
            **judge_state,
            "pregunta": game_question_to_dict(
                judge_state.get("pregunta"),
                include_answer=False
            )
        }
        with measure("SocketIO"):
            socketio.emit(
                "estado_sala",
                participant_state,
                room=game_room(game_code)
            )

        with measure("SocketIO"):
            socketio.emit(
                "estado_sala",
                judge_state,
                room=judge_room(game_code)
            )

        with measure("SocketIO"):
            socketio.emit(
                "estado_sala",
                participant_state,
                room=display_room(game_code)
            )

    return judge_state


def emit_state_later(socketio, game_code):
    socketio.sleep(0.05)
    emit_state(socketio, game_code)


def emit_question_start(socketio, business, game_code, id_partida, payload=None):
    payload = payload or {}
    question = payload.get("question") or business.get_current_question(id_partida)
    timer = serialize_any(payload.get("timer") or business.get_timer_status(id_partida))

    emit_question(socketio, question, game_code)
    emit_live_event(socketio, "actualizar_cronometro", timer, game_code)
    socketio.start_background_task(
        emit_state_later,
        socketio,
        game_code
    )
    start_timer_from_payload(socketio, game_code, id_partida, timer)


def start_timer_from_payload(socketio, game_code, id_partida, timer):
    if not timer or timer.get("exhausted") or not timer.get("active_since"):
        return

    token = uuid4().hex
    active_timer_tokens[str(game_code).strip().upper()] = token
    socketio.start_background_task(
        timer_loop,
        socketio,
        game_code,
        id_partida,
        timer,
        token
    )


def timer_loop(socketio, game_code, id_partida, initial_timer, token):
    business = PartidaBusiness()
    normalized_code = str(game_code).strip().upper()
    remaining = int((initial_timer or {}).get("remaining") or 0)

    while remaining > 0:
        socketio.sleep(1)

        if active_timer_tokens.get(normalized_code) != token:
            return

        remaining -= 1
        timer = {
            **(initial_timer or {}),
            "remaining": remaining,
            "exhausted": remaining <= 0
        }
        emit_live_event(socketio, "actualizar_cronometro", timer, game_code)

    if active_timer_tokens.get(normalized_code) == token:
        active_timer_tokens[normalized_code] = None
        business.mark_time_expired(id_partida)
        emit_state(socketio, game_code)



def countdown_and_start(socketio, game_code, id_partida):
    for number in range(5, 0, -1):
        emit_live_event(
            socketio,
            "estado_competencia",
            {
                "estado": "Cuenta regresiva",
                "mensaje": f"La competencia inicia en {number}.",
                "contador": number
            },
            game_code
        )
        socketio.sleep(1)

    with performance_operation("SocketIO iniciar_competencia publicar_pregunta", kind="socket"):
        business = PartidaBusiness()
        result = business.start_game(id_partida)

        if result.get_success():
            emit_question_start(socketio, business, game_code, id_partida, result.get_data())

        emit_live_event(socketio, "resultado_accion", business_result_to_dict(result), game_code)


def countdown_and_advance(socketio, game_code, id_partida):
    for number in range(5, 0, -1):
        emit_live_event(
            socketio,
            "estado_competencia",
            {
                "estado": "Cuenta regresiva",
                "mensaje": f"Siguiente pregunta en {number}.",
                "contador": number
            },
            game_code
        )
        socketio.sleep(1)

    with performance_operation("SocketIO siguiente_pregunta publicar_pregunta", kind="socket"):
        business = PartidaBusiness()
        result = business.advance_question(id_partida)

        if result.get_success():
            emit_question_start(socketio, business, game_code, id_partida, result.get_data())

        emit_live_event(socketio, "resultado_accion", business_result_to_dict(result), game_code)


def register_socket_events(socketio):

    @socketio.on("juez_unirse")
    @socket_event_performance("juez_unirse")
    def juez_unirse(data):
        if reject_non_judge():
            return

        game_code = str(data.get("codigo_partida", "")).strip().upper()
        join_room(judge_room(game_code))
        with measure("SocketIO"):
            emit("estado_sala", build_live_state(game_code, include_answer=True))

    @socketio.on("display_unirse")
    @socket_event_performance("display_unirse")
    def display_unirse(data):
        game_code = str(data.get("codigo_partida", "")).strip().upper()
        state = build_live_state(game_code, include_answer=False)

        if state is None:
            with measure("SocketIO"):
                emit("error_sala", {
                    "success": False,
                    "message": "La sala no existe."
                })
            return

        join_room(display_room(game_code))
        with measure("SocketIO"):
            emit("estado_sala", state)

    @socketio.on("participante_unirse")
    @socket_event_performance("participante_unirse")
    def participante_unirse(data):
        business = PartidaBusiness()
        result = business.join_game(
            data.get("codigo_partida"),
            data.get("sede"),
            data.get("nombre_equipo"),
            data.get("integrantes", "")
        )
        payload = business_result_to_dict(result)

        if result.get_success():
            participant = result.get_data()
            game_code = data.get("codigo_partida", "").strip().upper()
            join_room(game_room(game_code))
            join_room(participant_room(participant["codigo_participante"]))
            with measure("SocketIO"):
                emit("participante_registrado", payload)
            ranking = serialize_any(business.get_live_ranking(game_code))
            emit_to_judge(
                socketio,
                "participante_conectado",
                {
                    "participant": participant,
                    "ranking": ranking
                },
                game_code
            )
            if ranking is not None:
                with measure("SocketIO"):
                    socketio.emit(
                        "actualizar_puntajes",
                        ranking,
                        room=game_room(game_code)
                    )
                emit_to_display(
                    socketio,
                    "actualizar_puntajes",
                    ranking,
                    game_code
                )

        else:
            with measure("SocketIO"):
                emit("error_sala", payload)

    @socketio.on("participante_reconectar")
    @socket_event_performance("participante_reconectar")
    def participante_reconectar(data):
        game_code = str(data.get("codigo_partida", "")).strip().upper()
        code = data.get("codigo_participante")
        join_room(game_room(game_code))

        if code:
            join_room(participant_room(code))
            connected_participants[request.sid] = {
                "game_code": game_code,
                "participant_code": code
            }

        with measure("SocketIO"):
            emit("estado_sala", build_live_state(game_code))

    @socketio.on("disconnect")
    @socket_event_performance("disconnect")
    def participante_desconectar():
        participant_ref = connected_participants.pop(request.sid, None)

        if not participant_ref:
            return

        business = PartidaBusiness()
        result = business.disconnect_participant(
            participant_ref["game_code"],
            participant_ref["participant_code"]
        )

        if result.get_success():
            ranking = serialize_any(
                business.get_live_ranking(participant_ref["game_code"])
            )
            emit_to_judge(
                socketio,
                "participante_desconectado",
                {
                    "codigo_participante": participant_ref["participant_code"],
                    "ranking": ranking
                },
                participant_ref["game_code"]
            )

            if ranking is not None:
                with measure("SocketIO"):
                    socketio.emit(
                        "actualizar_puntajes",
                        ranking,
                        room=game_room(participant_ref["game_code"])
                    )
                emit_to_display(
                    socketio,
                    "actualizar_puntajes",
                    ranking,
                    participant_ref["game_code"]
                )

    @socketio.on("iniciar_competencia")
    @socket_event_performance("iniciar_competencia")
    def iniciar_competencia(data):
        if reject_non_judge():
            return

        business = PartidaBusiness()
        partida = business.get_by_code(data.get("codigo_partida"))

        if partida is None:
            emit("error_sala", {"message": "La partida no existe."})
            return

        socketio.start_background_task(
            countdown_and_start,
            socketio,
            partida.get_codigo_partida(),
            partida.get_id_partida()
        )

    @socketio.on("pedir_palabra")
    @socket_event_performance("pedir_palabra")
    def pedir_palabra(data):
        business = PartidaBusiness()
        result = business.request_word(
            data.get("codigo_partida"),
            data.get("codigo_participante")
        )
        payload = business_result_to_dict(result)
        with measure("SocketIO"):
            emit("resultado_accion", payload)

        if result.get_success():
            game_code = str(data.get("codigo_partida", "")).strip().upper()
            request_data = result.get_data() or {}
            request = request_data.get("request")

            if request is not None:
                emit_to_judge(
                    socketio,
                    "solicitud_palabra",
                    {
                        "request": request,
                        "queue": request_data.get("queue", [request])
                    },
                    game_code
                )
                emit_to_display(
                    socketio,
                    "solicitud_palabra_publica",
                    {"request": request},
                    game_code
                )

    @socketio.on("dar_palabra")
    @socket_event_performance("dar_palabra")
    def dar_palabra(data):
        if reject_non_judge():
            return

        business = PartidaBusiness()
        result = business.give_word(int(data.get("id_solicitud")))
        payload = business_result_to_dict(result)
        with measure("SocketIO"):
            emit("resultado_accion", payload)

        if result.get_success():
            game_code = str(data.get("codigo_partida", "")).strip().upper()
            request = (result.get_data() or {}).get("request")
            timer = (result.get_data() or {}).get("timer")
            stop_timer(game_code)

            if request is not None:
                emit_to_judge(
                    socketio,
                    "palabra_otorgada",
                    request,
                    game_code
                )
                with measure("SocketIO"):
                    socketio.emit(
                        "estado_palabra",
                        request,
                        room=game_room(game_code)
                    )
                emit_to_display(
                    socketio,
                    "estado_palabra",
                    request,
                    game_code
                )

            if timer is not None:
                emit_live_event(socketio, "actualizar_cronometro", timer, game_code)

    @socketio.on("respuesta_correcta")
    @socket_event_performance("respuesta_correcta")
    def respuesta_correcta(data):
        if reject_non_judge():
            return

        business = PartidaBusiness()
        result = business.mark_correct(int(data.get("id_solicitud")))
        payload = business_result_to_dict(result)
        with measure("SocketIO"):
            emit("resultado_accion", payload)

        if result.get_success():
            game_code = str(data.get("codigo_partida", "")).strip().upper()
            data_result = result.get_data() or {}
            request = data_result.get("request")
            ranking = data_result.get("ranking")
            stop_timer(game_code)

            if request is not None:
                emit_to_participant(
                    socketio,
                    "resultado_respuesta",
                    data_result,
                    request["codigo_participante"]
                )
                emit_to_judge(
                    socketio,
                    "respuesta_calificada",
                    data_result,
                    game_code
                )
                emit_to_display(
                    socketio,
                    "respuesta_publica",
                    {
                        "resultado": request.get("estado"),
                        "request": request
                    },
                    game_code
                )

            if ranking is not None:
                emit_live_event(socketio, "actualizar_puntajes", ranking, game_code)

    @socketio.on("respuesta_incorrecta")
    @socket_event_performance("respuesta_incorrecta")
    def respuesta_incorrecta(data):
        if reject_non_judge():
            return

        business = PartidaBusiness()
        result = business.mark_incorrect(int(data.get("id_solicitud")))
        payload = business_result_to_dict(result)
        with measure("SocketIO"):
            emit("resultado_accion", payload)

        if result.get_success():
            game_code = str(data.get("codigo_partida", "")).strip().upper()
            data_result = result.get_data() or {}
            request = data_result.get("request")
            ranking = data_result.get("ranking")
            timer = data_result.get("timer")

            if request is not None:
                emit_to_participant(
                    socketio,
                    "resultado_respuesta",
                    data_result,
                    request["codigo_participante"]
                )
                emit_to_judge(
                    socketio,
                    "respuesta_calificada",
                    data_result,
                    game_code
                )
                emit_to_display(
                    socketio,
                    "respuesta_publica",
                    {
                        "resultado": request.get("estado"),
                        "request": request
                    },
                    game_code
                )

            if ranking is not None:
                emit_live_event(socketio, "actualizar_puntajes", ranking, game_code)

            if timer is not None and request is not None:
                emit_live_event(socketio, "actualizar_cronometro", timer, game_code)
                start_timer_from_payload(socketio, game_code, request["id_partida"], timer)
                with measure("SocketIO"):
                    socketio.emit(
                        "estado_competencia",
                        {
                            "estado": "Pregunta en curso",
                            "mensaje": "Los equipos pueden pedir la palabra."
                        },
                        room=game_room(game_code)
                    )
                emit_to_display(
                    socketio,
                    "estado_competencia",
                    {
                        "estado": "Pregunta en curso",
                        "mensaje": "Los equipos pueden pedir la palabra."
                    },
                    game_code
                )

    @socketio.on("siguiente_pregunta")
    @socket_event_performance("siguiente_pregunta")
    def siguiente_pregunta(data):
        if reject_non_judge():
            return

        business = PartidaBusiness()
        partida = business.get_by_code(data.get("codigo_partida"))

        if partida is None:
            emit("error_sala", {"message": "La partida no existe."})
            return

        socketio.start_background_task(
            countdown_and_advance,
            socketio,
            partida.get_codigo_partida(),
            partida.get_id_partida()
        )

    @socketio.on("finalizar_competencia")
    @socket_event_performance("finalizar_competencia")
    def finalizar_competencia(data):
        if reject_non_judge():
            return

        business = PartidaBusiness()
        partida = business.get_by_code(data.get("codigo_partida"))

        if partida is None:
            emit("error_sala", {"message": "La partida no existe."})
            return

        result = business.finish_game(partida.get_id_partida())
        with measure("SocketIO"):
            emit("resultado_accion", business_result_to_dict(result))

        if result.get_success():
            game_code = partida.get_codigo_partida()
            stop_timer(game_code)
            ranking = serialize_any(business.get_live_ranking(game_code))
            emit_live_event(
                socketio,
                "estado_competencia",
                {
                    "estado": "Competencia finalizada",
                    "mensaje": "La competencia ha terminado."
                },
                game_code
            )

            if ranking is not None:
                emit_live_event(
                    socketio,
                    "actualizar_puntajes",
                    ranking,
                    game_code
                )
                emit_live_event(
                    socketio,
                    "mostrar_podio",
                    ranking,
                    game_code
                )
