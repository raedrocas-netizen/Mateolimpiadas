import unittest
from unittest.mock import patch

from logical_business.business_result import BusinessResult
from socket_events import competition_events


PRIVATE_QUESTION_KEYS = {
    "respuesta_correcta",
    "nombre_imagen_respuesta",
    "ruta_respuesta",
    "descripcion_ruta_respuesta",
    "imagen_respuesta"
}


def private_keys_in(value):
    if isinstance(value, dict):
        keys = set(value).intersection(PRIVATE_QUESTION_KEYS)
        return keys.union(*(
            private_keys_in(item)
            for item in value.values()
        ), set())

    if isinstance(value, (list, tuple)):
        return set().union(*(
            private_keys_in(item)
            for item in value
        ), set())

    return set()


def full_question():
    return {
        "id_partida_pregunta": 10,
        "id_partida": 1,
        "id_pregunta": 20,
        "numero_orden": 1,
        "estado": "ACTUAL",
        "enunciado": "Pregunta publica",
        "nombre_imagen_pregunta": "pregunta.png",
        "ruta_pregunta": "static/img/preguntas",
        "respuesta_correcta": "Respuesta reservada",
        "nombre_imagen_respuesta": "respuesta.png",
        "ruta_respuesta": "static/img/respuestas",
        "descripcion_ruta_respuesta": "Imagen de respuesta"
    }


def successful_result():
    result = BusinessResult()
    result.set_success(True)
    result.set_message("Partida iniciada correctamente.")
    result.set_data({
        "question": full_question(),
        "timer": {
            "remaining": 30,
            "exhausted": False,
            "active_since": None,
            "game_state": "EN_CURSO"
        }
    })
    return result


class FakeSocketIO:

    def __init__(self):
        self.emissions = []
        self.background_tasks = []

    def emit(self, event, payload, room=None):
        self.emissions.append({
            "event": event,
            "payload": payload,
            "room": room
        })

    def sleep(self, seconds):
        return None

    def start_background_task(self, target, *args, **kwargs):
        self.background_tasks.append((target, args, kwargs))


class FakePartida:

    def __init__(self, state="EN_CURSO"):
        self.state = state

    def get_id_partida(self):
        return 1

    def get_codigo_partida(self):
        return "ABC123"

    def get_nombre(self):
        return "Partida de prueba"

    def get_area(self):
        return "MATEMATICA"

    def get_tiempo_por_pregunta(self):
        return 30

    def get_puntos_correcta(self):
        return 10

    def get_penalizacion_incorrecta(self):
        return 0

    def get_estado(self):
        return self.state

    def get_pregunta_actual(self):
        return 1

    def get_fecha_creacion(self):
        return None

    def get_tiempo_restante_actual(self):
        return 30

    def get_tiempo_agotado(self):
        return False


class FakeLiveStateBusiness:

    def __init__(self, state="EN_CURSO"):
        self.state = state
        self.partida = FakePartida(self.state)

    def get_by_code(self, game_code):
        return self.partida

    def get_waiting_room_status(self, id_partida):
        return []

    def get_current_question(self, id_partida):
        return full_question()

    def get_word_requests(self, id_partida):
        return []

    def get_live_ranking(self, game_code, partida=None):
        return {"ranking": [], "total_questions": 1}

    def get_timer_status(self, id_partida):
        return {
            "remaining": 30,
            "exhausted": False,
            "active_since": None,
            "game_state": self.state
        }


class FakeQuestionActionBusiness:

    def __init__(self):
        self.start_calls = []
        self.advance_calls = []

    def start_game(self, id_partida):
        self.start_calls.append(id_partida)
        return successful_result()

    def advance_question(self, id_partida):
        self.advance_calls.append(id_partida)
        result = successful_result()
        result.set_message("Pregunta actualizada correctamente.")
        return result


class QuestionPayloadSecurityTests(unittest.TestCase):

    def emissions_for(self, socketio, event, room):
        return [
            emission["payload"]
            for emission in socketio.emissions
            if emission["event"] == event and emission["room"] == room
        ]

    def assert_public_payload(self, payload):
        self.assertEqual(private_keys_in(payload), set())
        serialized = str(payload)
        self.assertNotIn("Respuesta reservada", serialized)
        self.assertNotIn("respuesta.png", serialized)
        self.assertNotIn("static/img/respuestas", serialized)

    def test_mostrar_pregunta_is_public_for_participants_and_display(self):
        socketio = FakeSocketIO()

        competition_events.emit_question(socketio, full_question(), "ABC123")

        participant_payload = self.emissions_for(
            socketio,
            "mostrar_pregunta",
            competition_events.game_room("ABC123")
        )[0]
        display_payload = self.emissions_for(
            socketio,
            "mostrar_pregunta",
            competition_events.display_room("ABC123")
        )[0]

        for payload in (participant_payload, display_payload):
            self.assert_public_payload(payload)
            self.assertEqual(payload["enunciado"], "Pregunta publica")
            self.assertEqual(payload["numero_orden"], 1)
            self.assertEqual(payload["imagen"], "/static/img/preguntas/pregunta.png")

    def test_judge_receives_complete_question(self):
        socketio = FakeSocketIO()

        competition_events.emit_question(socketio, full_question(), "ABC123")

        judge_payload = self.emissions_for(
            socketio,
            "mostrar_pregunta",
            competition_events.judge_room("ABC123")
        )[0]
        self.assertEqual(judge_payload["respuesta_correcta"], "Respuesta reservada")
        self.assertEqual(judge_payload["nombre_imagen_respuesta"], "respuesta.png")
        self.assertEqual(
            judge_payload["imagen_respuesta"],
            "/static/img/respuestas/respuesta.png"
        )

    def test_resultado_accion_separates_public_and_judge_payloads(self):
        socketio = FakeSocketIO()
        result = successful_result()

        competition_events.emit_question_action_result(socketio, result, "ABC123")

        participant_payload = self.emissions_for(
            socketio,
            "resultado_accion",
            competition_events.game_room("ABC123")
        )[0]
        judge_payload = self.emissions_for(
            socketio,
            "resultado_accion",
            competition_events.judge_room("ABC123")
        )[0]
        display_payloads = self.emissions_for(
            socketio,
            "resultado_accion",
            competition_events.display_room("ABC123")
        )

        self.assertEqual(participant_payload, {
            "success": True,
            "message": "Partida iniciada correctamente."
        })
        self.assert_public_payload(participant_payload)
        self.assertEqual(
            judge_payload["data"]["question"]["respuesta_correcta"],
            "Respuesta reservada"
        )
        self.assertEqual(display_payloads, [])

    def test_start_game_emits_sanitized_result_and_public_question(self):
        socketio = FakeSocketIO()
        business = FakeQuestionActionBusiness()

        with patch.object(competition_events, "PartidaBusiness", return_value=business):
            competition_events.countdown_and_start(socketio, "ABC123", 1)

        self.assertEqual(business.start_calls, [1])
        public_result = self.emissions_for(
            socketio,
            "resultado_accion",
            competition_events.game_room("ABC123")
        )[0]
        public_question = self.emissions_for(
            socketio,
            "mostrar_pregunta",
            competition_events.game_room("ABC123")
        )[0]
        self.assert_public_payload(public_result)
        self.assert_public_payload(public_question)

    def test_advance_question_emits_sanitized_result_and_public_question(self):
        socketio = FakeSocketIO()
        business = FakeQuestionActionBusiness()

        with patch.object(competition_events, "PartidaBusiness", return_value=business):
            competition_events.countdown_and_advance(socketio, "ABC123", 1)

        self.assertEqual(business.advance_calls, [1])
        public_result = self.emissions_for(
            socketio,
            "resultado_accion",
            competition_events.game_room("ABC123")
        )[0]
        public_question = self.emissions_for(
            socketio,
            "mostrar_pregunta",
            competition_events.game_room("ABC123")
        )[0]
        self.assert_public_payload(public_result)
        self.assert_public_payload(public_question)

    def test_reconnection_state_is_public_but_judge_state_is_complete(self):
        with patch.object(
                competition_events,
                "PartidaBusiness",
                return_value=FakeLiveStateBusiness()
        ):
            reconnect_state = competition_events.build_live_state("ABC123")
            judge_state = competition_events.build_live_state(
                "ABC123",
                include_answer=True
            )

        self.assert_public_payload(reconnect_state)
        self.assertEqual(reconnect_state["pregunta"]["enunciado"], "Pregunta publica")
        self.assertEqual(
            judge_state["pregunta"]["respuesta_correcta"],
            "Respuesta reservada"
        )

    def test_emit_state_removes_derived_answer_image_from_public_rooms(self):
        socketio = FakeSocketIO()

        with patch.object(
                competition_events,
                "PartidaBusiness",
                return_value=FakeLiveStateBusiness()
        ):
            competition_events.emit_state(socketio, "ABC123")

        participant_state = self.emissions_for(
            socketio,
            "estado_sala",
            competition_events.game_room("ABC123")
        )[0]
        display_state = self.emissions_for(
            socketio,
            "estado_sala",
            competition_events.display_room("ABC123")
        )[0]
        judge_state = self.emissions_for(
            socketio,
            "estado_sala",
            competition_events.judge_room("ABC123")
        )[0]

        self.assert_public_payload(participant_state)
        self.assert_public_payload(display_state)
        self.assertEqual(
            judge_state["pregunta"]["imagen_respuesta"],
            "/static/img/respuestas/respuesta.png"
        )

    def test_paused_reconnection_hides_public_question_but_keeps_judge_question(self):
        business = FakeLiveStateBusiness(state="PAUSADA")

        with patch.object(
                competition_events,
                "PartidaBusiness",
                return_value=business
        ):
            reconnect_state = competition_events.build_live_state("ABC123")
            judge_state = competition_events.build_live_state(
                "ABC123",
                include_answer=True
            )

        self.assertIsNone(reconnect_state["pregunta"])
        self.assertEqual(reconnect_state["estado_competencia"], "PARTIDA PAUSADA")
        self.assertEqual(
            judge_state["pregunta"]["respuesta_correcta"],
            "Respuesta reservada"
        )

    def test_paused_emit_state_sends_no_question_to_participant_or_display(self):
        socketio = FakeSocketIO()

        with patch.object(
                competition_events,
                "PartidaBusiness",
                return_value=FakeLiveStateBusiness(state="PAUSADA")
        ):
            competition_events.emit_state(socketio, "ABC123")

        participant_state = self.emissions_for(
            socketio,
            "estado_sala",
            competition_events.game_room("ABC123")
        )[0]
        display_state = self.emissions_for(
            socketio,
            "estado_sala",
            competition_events.display_room("ABC123")
        )[0]
        judge_state = self.emissions_for(
            socketio,
            "estado_sala",
            competition_events.judge_room("ABC123")
        )[0]

        self.assertIsNone(participant_state["pregunta"])
        self.assertIsNone(display_state["pregunta"])
        self.assertIsNotNone(judge_state["pregunta"])
        self.assert_public_payload(participant_state)
        self.assert_public_payload(display_state)


if __name__ == "__main__":
    unittest.main()
