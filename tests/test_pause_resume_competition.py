import os
import unittest
from unittest.mock import Mock, patch

from flask import Flask, session

import helper.super_global as sg
from dao.partida_dao import PartidaDao
from data_representation.partida import Partida
from logical_business.business_result import BusinessResult
from logical_business.partida_business import PartidaBusiness
from socket_events import competition_events


def game(state=sg.GAME_STATUS_IN_PROGRESS, remaining=30):
    partida = Partida()
    partida.set_id_partida(1)
    partida.set_codigo_partida("ABC123")
    partida.set_nombre("Partida de prueba")
    partida.set_area(sg.AREA_PRIMARIA)
    partida.set_tiempo_por_pregunta(30)
    partida.set_puntos_correcta(10)
    partida.set_penalizacion_incorrecta(0)
    partida.set_estado(state)
    partida.set_pregunta_actual(1)
    partida.set_fecha_creacion("18/07/2026")
    partida.set_tiempo_restante_actual(remaining)
    partida.set_tiempo_agotado(remaining <= 0)
    return partida


def question():
    return {
        "id_partida_pregunta": 10,
        "id_partida": 1,
        "id_pregunta": 20,
        "numero_orden": 1,
        "estado": sg.GAME_QUESTION_STATUS_CURRENT,
        "estado_partida_pregunta": sg.GAME_QUESTION_STATUS_CURRENT,
        "enunciado": "La misma pregunta",
        "nombre_imagen_pregunta": "pregunta.png",
        "ruta_pregunta": "static/img/preguntas",
        "respuesta_correcta": "Respuesta reservada",
        "nombre_imagen_respuesta": "respuesta.png",
        "ruta_respuesta": "static/img/respuestas"
    }


def request_data(request_id=1, status=sg.WORD_REQUEST_STATUS_TURN, order=1):
    return {
        "id_solicitud": request_id,
        "id_partida": 1,
        "id_partida_pregunta": 10,
        "id_participante": request_id,
        "orden_solicitud": order,
        "estado": status,
        "codigo_participante": f"EQ{request_id}",
        "nombre": f"Equipo {request_id}",
        "sede": f"Sede {request_id}"
    }


def successful_result(data=None, message="Accion completada."):
    result = BusinessResult()
    result.set_success(True)
    result.set_message(message)
    result.set_data(data)
    return result


class FakeConnection:

    def __init__(self):
        self.commits = 0
        self.rollbacks = 0

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1


class ScriptedCursor:

    def __init__(self, select_results):
        self.select_results = list(select_results)
        self.calls = []
        self.current_result = None
        self.rowcount = 1

    def execute(self, sql, parameters=()):
        self.calls.append((sql, parameters))
        if sql.lstrip().upper().startswith("SELECT"):
            self.current_result = self.select_results.pop(0)
        else:
            self.current_result = None
        return self

    def fetchone(self):
        return self.current_result

    def close(self):
        return None


class ScriptedDao:

    def __init__(self, select_results):
        self.cursor = ScriptedCursor(select_results)
        self.conexion = FakeConnection()
        self.closed = False

    def conectar(self):
        return True

    def cerrar(self):
        self.closed = True


class FakeLiveBusiness:

    def __init__(self, state=sg.GAME_STATUS_PAUSED, active_turn=True):
        self.partida = game(state, remaining=18)
        self.requests = [
            request_data(1, sg.WORD_REQUEST_STATUS_TURN if active_turn else sg.WORD_REQUEST_STATUS_QUEUED, 1),
            request_data(2, sg.WORD_REQUEST_STATUS_QUEUED, 2),
            request_data(3, sg.WORD_REQUEST_STATUS_QUEUED, 3)
        ]

    def get_by_code(self, game_code):
        return self.partida

    def get_waiting_room_status(self, id_partida):
        return []

    def get_current_question(self, id_partida):
        return question()

    def get_word_requests(self, id_partida):
        return self.requests

    def get_live_ranking(self, game_code):
        return {"ranking": [], "total_questions": 3, "current_question": 1}

    def get_timer_status(self, id_partida):
        return {
            "remaining": 18,
            "exhausted": False,
            "active_since": None if self.partida.get_estado() == sg.GAME_STATUS_PAUSED else "18/07/2026 12:00:00",
            "game_state": self.partida.get_estado()
        }


class RegisteredSocketIO:

    def __init__(self):
        self.handlers = {}
        self.emissions = []
        self.background_tasks = []

    def on(self, event):
        def decorator(function):
            self.handlers[event] = function
            return function
        return decorator

    def emit(self, event, payload, room=None):
        self.emissions.append((event, payload, room))

    def start_background_task(self, target, *args, **kwargs):
        self.background_tasks.append((target, args, kwargs))

    def sleep(self, seconds):
        return None


class PauseResumeBusinessTests(unittest.TestCase):

    def setUp(self):
        self.business = PartidaBusiness()
        self.dao = Mock()
        self.business._PartidaBusiness__partida_dao = self.dao

    def test_in_progress_can_pause_and_preserves_timer_payload(self):
        self.dao.pause_game_transaction.return_value = True

        with patch.object(self.business, "get_by_id", return_value=game()), patch.object(
                self.business, "get_current_question", return_value=question()
        ), patch.object(
                self.business,
                "get_timer_status",
                side_effect=[
                    {"remaining": 16, "exhausted": False, "active_since": "inicio"},
                    {"remaining": 16, "exhausted": False, "active_since": None}
                ]
        ):
            result = self.business.pause_game(1)

        self.assertTrue(result.get_success())
        self.assertEqual(result.get_data()["timer"]["remaining"], 16)
        self.assertIsNone(result.get_data()["timer"]["active_since"])
        self.dao.pause_game_transaction.assert_called_once_with(1)

    def test_paused_can_resume_from_same_time(self):
        self.dao.resume_game_transaction.return_value = True

        with patch.object(
                self.business,
                "get_by_id",
                return_value=game(sg.GAME_STATUS_PAUSED, remaining=16)
        ), patch.object(
                self.business, "get_current_question", return_value=question()
        ), patch.object(
                self.business,
                "get_timer_status",
                side_effect=[
                    {"remaining": 16, "exhausted": False, "active_since": None},
                    {"remaining": 16, "exhausted": False, "active_since": "nuevo-inicio"}
                ]
        ):
            result = self.business.resume_game(1)

        self.assertTrue(result.get_success())
        self.assertEqual(result.get_data()["timer"]["remaining"], 16)
        self.dao.resume_game_transaction.assert_called_once_with(1)

    def test_duplicate_pause_and_resume_without_pause_are_rejected(self):
        with patch.object(
                self.business,
                "get_by_id",
                return_value=game(sg.GAME_STATUS_PAUSED)
        ):
            duplicate_pause = self.business.pause_game(1)

        with patch.object(self.business, "get_by_id", return_value=game()):
            invalid_resume = self.business.resume_game(1)

        self.assertFalse(duplicate_pause.get_success())
        self.assertFalse(invalid_resume.get_success())
        self.dao.pause_game_transaction.assert_not_called()
        self.dao.resume_game_transaction.assert_not_called()

    def test_finished_game_cannot_pause_or_resume(self):
        with patch.object(
                self.business,
                "get_by_id",
                return_value=game(sg.GAME_STATUS_FINISHED)
        ):
            pause_result = self.business.pause_game(1)
            resume_result = self.business.resume_game(1)

        self.assertFalse(pause_result.get_success())
        self.assertFalse(resume_result.get_success())

    def test_exhausted_question_cannot_pause(self):
        with patch.object(self.business, "get_by_id", return_value=game()), patch.object(
                self.business, "get_current_question", return_value=question()
        ), patch.object(
                self.business,
                "get_timer_status",
                return_value={"remaining": 0, "exhausted": True, "active_since": None}
        ):
            result = self.business.pause_game(1)

        self.assertFalse(result.get_success())
        self.dao.pause_game_transaction.assert_not_called()

    def test_paused_game_rejects_queue_and_grading_actions(self):
        current_request = request_data()

        with patch.object(
                self.business, "get_word_request_by_id", return_value=current_request
        ), patch.object(
                self.business,
                "get_by_id",
                return_value=game(sg.GAME_STATUS_PAUSED)
        ):
            give_result = self.business.give_word(1)
            correct_result = self.business.mark_correct(1)
            incorrect_result = self.business.mark_incorrect(1)
            pass_result = self.business.pass_word(1)

        self.assertFalse(give_result.get_success())
        self.assertFalse(correct_result.get_success())
        self.assertFalse(incorrect_result.get_success())
        self.assertFalse(pass_result.get_success())
        self.dao.give_word_transaction.assert_not_called()
        self.dao.mark_word_request_result_transaction.assert_not_called()
        self.dao.pass_word_transaction.assert_not_called()

    def test_new_word_request_is_rejected_while_paused(self):
        with patch.object(
                self.business,
                "get_by_code",
                return_value=game(sg.GAME_STATUS_PAUSED)
        ):
            result = self.business.request_word("ABC123", "EQ1")

        self.assertFalse(result.get_success())
        self.dao.request_word_transaction.assert_not_called()

    def test_finish_game_is_allowed_from_paused(self):
        paused_game = game(sg.GAME_STATUS_PAUSED)
        self.dao.update_estado.return_value = True

        with patch.object(self.business, "get_by_id", return_value=paused_game):
            result = self.business.finish_game(1)

        self.assertTrue(result.get_success())
        self.dao.update_estado.assert_called_once_with(1, sg.GAME_STATUS_FINISHED)


class PauseResumeDaoTests(unittest.TestCase):

    def test_pause_materializes_running_remaining_without_touching_queue(self):
        scripted = ScriptedDao([{
            "estado": sg.GAME_STATUS_IN_PROGRESS,
            "tiempo_por_pregunta": 30,
            "tiempo_restante_actual": 30,
            "temporizador_activo_desde": "18/07/2026 12:00:00",
            "tiempo_agotado": 0,
            "id_partida_pregunta": 10,
            "question_state": sg.GAME_QUESTION_STATUS_CURRENT
        }])
        dao = PartidaDao()
        dao.dao = scripted

        with patch.object(dao, "_calculate_remaining", return_value=16):
            result = dao.pause_game_transaction(1)

        update = next(
            call for call in scripted.cursor.calls
            if "UPDATE partidas" in call[0]
        )
        self.assertTrue(result)
        self.assertEqual(update[1], (sg.GAME_STATUS_PAUSED, 16, 16, 1))
        self.assertFalse(any(
            "UPDATE solicitudes_palabra" in sql
            for sql, parameters in scripted.cursor.calls
        ))

    def test_resume_starts_timer_when_there_is_no_active_turn(self):
        scripted = ScriptedDao([{
            "estado": sg.GAME_STATUS_PAUSED,
            "tiempo_por_pregunta": 30,
            "tiempo_restante_actual": 18,
            "tiempo_agotado": 0,
            "id_partida_pregunta": 10,
            "question_state": sg.GAME_QUESTION_STATUS_CURRENT
        }, (0,)])
        dao = PartidaDao()
        dao.dao = scripted

        with patch.object(dao, "_now_text", return_value="18/07/2026 12:10:00"):
            result = dao.resume_game_transaction(1)

        update = next(
            call for call in scripted.cursor.calls
            if "UPDATE partidas" in call[0]
        )
        self.assertTrue(result)
        self.assertEqual(
            update[1],
            (sg.GAME_STATUS_IN_PROGRESS, 18, "18/07/2026 12:10:00", 1)
        )

    def test_resume_keeps_timer_stopped_when_a_participant_has_turn(self):
        scripted = ScriptedDao([{
            "estado": sg.GAME_STATUS_PAUSED,
            "tiempo_por_pregunta": 30,
            "tiempo_restante_actual": 18,
            "tiempo_agotado": 0,
            "id_partida_pregunta": 10,
            "question_state": sg.GAME_QUESTION_STATUS_CURRENT
        }, (1,)])
        dao = PartidaDao()
        dao.dao = scripted

        result = dao.resume_game_transaction(1)

        update = next(
            call for call in scripted.cursor.calls
            if "UPDATE partidas" in call[0]
        )
        self.assertTrue(result)
        self.assertEqual(
            update[1],
            (sg.GAME_STATUS_IN_PROGRESS, 18, None, 1)
        )


class PauseResumePayloadTests(unittest.TestCase):

    def test_paused_public_state_hides_question_but_judge_keeps_everything(self):
        business = FakeLiveBusiness()

        with patch.object(competition_events, "PartidaBusiness", return_value=business):
            participant_state = competition_events.build_live_state("ABC123")
            display_state = competition_events.build_live_state("ABC123")
            judge_state = competition_events.build_live_state("ABC123", include_answer=True)

        self.assertIsNone(participant_state["pregunta"])
        self.assertIsNone(display_state["pregunta"])
        self.assertEqual(
            judge_state["pregunta"]["respuesta_correcta"],
            "Respuesta reservada"
        )
        self.assertEqual(judge_state["pregunta"]["numero_orden"], 1)
        self.assertEqual(
            [item["id_solicitud"] for item in judge_state["solicitudes"]],
            [1, 2, 3]
        )
        self.assertEqual(judge_state["solicitudes"][0]["estado"], "EN_TURNO")

    def test_resume_republishes_same_sanitized_question_and_queue(self):
        business = FakeLiveBusiness(state=sg.GAME_STATUS_IN_PROGRESS)

        with patch.object(competition_events, "PartidaBusiness", return_value=business):
            public_state = competition_events.build_live_state("ABC123")
            judge_state = competition_events.build_live_state("ABC123", include_answer=True)

        self.assertEqual(public_state["pregunta"]["id_partida_pregunta"], 10)
        self.assertEqual(public_state["pregunta"]["numero_orden"], 1)
        self.assertNotIn("respuesta_correcta", public_state["pregunta"])
        self.assertEqual(
            public_state["pregunta"]["id_partida_pregunta"],
            judge_state["pregunta"]["id_partida_pregunta"]
        )
        self.assertEqual(public_state["solicitudes"], judge_state["solicitudes"])


class PauseResumeSocketTests(unittest.TestCase):

    def setUp(self):
        os.environ["PERFORMANCE_LOGS"] = "0"
        competition_events.active_game_actions.clear()
        competition_events.active_timer_tokens.clear()
        self.socketio = RegisteredSocketIO()
        competition_events.register_socket_events(self.socketio)
        self.app = Flask(__name__)
        self.app.secret_key = "test-secret"

    def tearDown(self):
        competition_events.active_game_actions.clear()
        competition_events.active_timer_tokens.clear()

    def call_judge_handler(self, event, payload):
        with self.app.test_request_context("/"):
            session["judge_authenticated"] = True
            self.socketio.handlers[event](payload)

    def test_pause_and_resume_do_not_emit_countdown_or_change_question(self):
        partida = game()
        business = Mock()
        business.get_by_code.return_value = partida
        business.pause_game.return_value = successful_result()
        resumed_state = {
            "partida": {"estado": sg.GAME_STATUS_IN_PROGRESS, "pregunta_actual": 1},
            "pregunta": question(),
            "timer": {
                "remaining": 16,
                "exhausted": False,
                "active_since": "18/07/2026 12:10:00"
            },
            "solicitudes": []
        }

        with patch.object(competition_events, "PartidaBusiness", return_value=business), patch.object(
                competition_events, "emit_state", return_value=resumed_state
        ) as emit_state, patch.object(competition_events, "emit"):
            self.call_judge_handler(
                "pausar_competencia",
                {"codigo_partida": "ABC123"}
            )

        self.assertEqual(emit_state.call_count, 1)
        self.assertEqual(self.socketio.background_tasks, [])
        self.assertFalse(any(
            event == "estado_competencia" and payload.get("contador")
            for event, payload, room in self.socketio.emissions
        ))
        self.assertEqual(resumed_state["partida"]["pregunta_actual"], 1)

        partida.set_estado(sg.GAME_STATUS_PAUSED)
        business.resume_game.return_value = successful_result()

        with patch.object(competition_events, "PartidaBusiness", return_value=business), patch.object(
                competition_events, "emit_state", return_value=resumed_state
        ), patch.object(competition_events, "emit"):
            self.call_judge_handler(
                "reanudar_competencia",
                {"codigo_partida": "ABC123"}
            )

        self.assertEqual(len(self.socketio.background_tasks), 1)
        self.assertIs(self.socketio.background_tasks[0][0], competition_events.timer_loop)
        self.assertFalse(any(
            event == "estado_competencia" and payload.get("contador")
            for event, payload, room in self.socketio.emissions
        ))

    def test_resume_with_active_turn_does_not_start_timer_task(self):
        partida = game(sg.GAME_STATUS_PAUSED, remaining=18)
        business = Mock()
        business.get_by_code.return_value = partida
        business.resume_game.return_value = successful_result()
        state = {
            "partida": {"estado": sg.GAME_STATUS_IN_PROGRESS, "pregunta_actual": 1},
            "pregunta": question(),
            "timer": {
                "remaining": 18,
                "exhausted": False,
                "active_since": None
            },
            "solicitudes": [request_data()]
        }

        with patch.object(competition_events, "PartidaBusiness", return_value=business), patch.object(
                competition_events, "emit_state", return_value=state
        ), patch.object(competition_events, "emit"):
            self.call_judge_handler(
                "reanudar_competencia",
                {"codigo_partida": "ABC123"}
            )

        self.assertEqual(self.socketio.background_tasks, [])
        self.assertEqual(state["solicitudes"][0]["estado"], "EN_TURNO")
        self.assertEqual(state["timer"]["remaining"], 18)

    def test_server_lock_rejects_duplicate_pause(self):
        partida = game()
        business = Mock()
        business.get_by_code.return_value = partida
        self.assertTrue(competition_events.begin_game_action("ABC123", "pause"))

        with patch.object(competition_events, "PartidaBusiness", return_value=business), patch.object(
                competition_events, "emit"
        ) as emit:
            self.call_judge_handler(
                "pausar_competencia",
                {"codigo_partida": "ABC123"}
            )

        business.pause_game.assert_not_called()
        self.assertIn("otra acción", emit.call_args.args[1]["message"])

    def test_server_lock_rejects_duplicate_resume(self):
        partida = game(sg.GAME_STATUS_PAUSED)
        business = Mock()
        business.get_by_code.return_value = partida
        self.assertTrue(competition_events.begin_game_action("ABC123", "resume"))

        with patch.object(competition_events, "PartidaBusiness", return_value=business), patch.object(
                competition_events, "emit"
        ) as emit:
            self.call_judge_handler(
                "reanudar_competencia",
                {"codigo_partida": "ABC123"}
            )

        business.resume_game.assert_not_called()
        self.assertIn("otra acción", emit.call_args.args[1]["message"])

    def test_finish_from_paused_does_not_resume_timer_or_advance_question(self):
        partida = game(sg.GAME_STATUS_PAUSED, remaining=18)
        business = Mock()
        business.get_by_code.return_value = partida
        business.finish_game.return_value = successful_result()
        business.get_live_ranking.return_value = {
            "ranking": [],
            "current_question": 1,
            "total_questions": 3
        }

        with patch.object(competition_events, "PartidaBusiness", return_value=business), patch.object(
                competition_events, "emit"
        ):
            self.call_judge_handler(
                "finalizar_competencia",
                {"codigo_partida": "ABC123"}
            )

        self.assertEqual(self.socketio.background_tasks, [])
        business.start_game.assert_not_called()
        business.advance_question.assert_not_called()
        self.assertFalse(any(
            event == "estado_competencia" and payload.get("contador")
            for event, payload, room in self.socketio.emissions
        ))
        final_events = [
            payload
            for event, payload, room in self.socketio.emissions
            if event == "estado_competencia"
        ]
        self.assertTrue(final_events)
        self.assertEqual(final_events[0]["estado"], "Competencia finalizada")


if __name__ == "__main__":
    unittest.main()
