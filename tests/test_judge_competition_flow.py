import unittest
from unittest.mock import Mock, patch

import helper.super_global as sg
from data_representation.partida import Partida
from logical_business.business_result import BusinessResult
from logical_business.partida_business import PartidaBusiness
from socket_events import competition_events


def game(state=sg.GAME_STATUS_IN_PROGRESS, current_question=1):
    partida = Partida()
    partida.set_id_partida(1)
    partida.set_codigo_partida("ABC123")
    partida.set_nombre("Partida de prueba")
    partida.set_area(sg.AREA_PRIMARIA)
    partida.set_tiempo_por_pregunta(30)
    partida.set_puntos_correcta(10)
    partida.set_penalizacion_incorrecta(0)
    partida.set_estado(state)
    partida.set_pregunta_actual(current_question)
    partida.set_fecha_creacion("18/07/2026")
    partida.set_tiempo_restante_actual(30)
    partida.set_tiempo_agotado(0)
    return partida


def successful_result(data=None):
    result = BusinessResult()
    result.set_success(True)
    result.set_message("Acción completada.")
    result.set_data(data)
    return result


class FakeSocketIO:

    def __init__(self):
        self.emissions = []
        self.background_tasks = []

    def emit(self, event, payload, room=None):
        self.emissions.append((event, payload, room))

    def sleep(self, seconds):
        return None

    def start_background_task(self, target, *args, **kwargs):
        self.background_tasks.append((target, args, kwargs))


class CountdownBusiness:

    def __init__(self):
        self.start_calls = 0
        self.advance_calls = 0

    def start_game(self, id_partida):
        self.start_calls += 1
        return successful_result({
            "question": {"numero_orden": 1, "enunciado": "Pregunta"},
            "timer": {"remaining": 30, "exhausted": False, "active_since": None}
        })

    def advance_question(self, id_partida):
        self.advance_calls += 1
        return successful_result({
            "question": {"numero_orden": 2, "enunciado": "Pregunta"},
            "timer": {"remaining": 30, "exhausted": False, "active_since": None}
        })


class JudgeCompetitionFlowTests(unittest.TestCase):

    def tearDown(self):
        competition_events.active_game_actions.clear()
        competition_events.active_participant_deletions.clear()

    def test_generated_code_uses_existing_alphabet_and_requested_length(self):
        business = PartidaBusiness()

        with patch.object(business, "get_by_code", return_value=None):
            result = business.generate_code(6)

        self.assertTrue(result.get_success())
        self.assertEqual(len(result.get_data()), 6)
        self.assertTrue(set(result.get_data()).issubset(set(sg.GAME_CODE_ALPHABET)))

    def test_start_rejects_game_that_already_started(self):
        business = PartidaBusiness()
        dao = Mock()
        business._PartidaBusiness__partida_dao = dao

        with patch.object(business, "get_by_id", return_value=game()):
            result = business.start_game(1)

        self.assertFalse(result.get_success())
        dao.start_game_transaction.assert_not_called()

    def test_advance_rejects_when_time_is_still_running(self):
        business = PartidaBusiness()
        dao = Mock()
        business._PartidaBusiness__partida_dao = dao

        with patch.object(business, "get_by_id", return_value=game()), patch.object(
                business,
                "get_timer_status",
                return_value={"remaining": 8, "exhausted": False}
        ):
            result = business.advance_question(1)

        self.assertFalse(result.get_success())
        self.assertIn("finalizar el tiempo", result.get_message())
        dao.advance_question_transaction.assert_not_called()

    def test_correct_answer_finishes_timer_without_advancing(self):
        business = PartidaBusiness()
        request = {
            "id_solicitud": 7,
            "id_partida": 1,
            "estado": sg.WORD_REQUEST_STATUS_TURN
        }
        answer_result = successful_result({"request": request, "ranking": {"ranking": []}})

        with patch.object(business, "get_word_request_by_id", return_value=request), patch.object(
                business,
                "get_by_id",
                return_value=game()
        ), patch.object(
                business,
                "_mark_word_request_result",
                return_value=answer_result
        ), patch.object(
                business,
                "mark_time_expired",
                return_value=successful_result(game())
        ) as expire, patch.object(
                business,
                "get_timer_status",
                return_value={"remaining": 0, "exhausted": True, "active_since": None}
        ), patch.object(business, "advance_question") as advance:
            result = business.mark_correct(7)

        self.assertTrue(result.get_success())
        self.assertEqual(result.get_data()["timer"]["remaining"], 0)
        expire.assert_called_once_with(1)
        advance.assert_not_called()

    def test_server_action_lock_rejects_double_execution(self):
        self.assertTrue(competition_events.begin_game_action("abc123", "start"))
        self.assertFalse(competition_events.begin_game_action("ABC123", "start"))
        competition_events.finish_game_action("ABC123")
        self.assertTrue(competition_events.begin_game_action("ABC123", "next"))

    def test_start_countdown_occurs_five_times_and_starts_once(self):
        socketio = FakeSocketIO()
        business = CountdownBusiness()

        with patch.object(competition_events, "PartidaBusiness", return_value=business):
            competition_events.countdown_and_start(socketio, "ABC123", 1)

        countdowns = [
            payload["contador"]
            for event, payload, room in socketio.emissions
            if event == "estado_competencia"
            and room == competition_events.game_room("ABC123")
        ]
        self.assertEqual(countdowns, [5, 4, 3, 2, 1])
        self.assertEqual(business.start_calls, 1)

    def test_next_countdown_occurs_five_times_and_advances_once(self):
        socketio = FakeSocketIO()
        business = CountdownBusiness()

        with patch.object(competition_events, "PartidaBusiness", return_value=business):
            competition_events.countdown_and_advance(socketio, "ABC123", 1)

        countdowns = [
            payload["contador"]
            for event, payload, room in socketio.emissions
            if event == "estado_competencia"
            and room == competition_events.game_room("ABC123")
        ]
        self.assertEqual(countdowns, [5, 4, 3, 2, 1])
        self.assertEqual(business.advance_calls, 1)


if __name__ == "__main__":
    unittest.main()
