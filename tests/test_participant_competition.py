import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import helper.super_global as sg
from dao.partida_dao import PartidaDao
from data_representation.partida import Partida
from helper.database_implements import SCHEMA_STATEMENTS
from logical_business.partida_business import PartidaBusiness
from socket_events import competition_events


def game(state=sg.GAME_STATUS_IN_PROGRESS):
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
    partida.set_tiempo_restante_actual(20)
    partida.set_tiempo_agotado(False)
    return partida


def participant(connected=1, score=40):
    return {
        "id_participante": 7,
        "id_partida": 1,
        "codigo_participante": "PET-001",
        "nombre": "Equipo Pitágoras",
        "sede": "Petapa",
        "integrantes": "Ana, Luis",
        "puntaje": score,
        "estado": sg.TEAM_STATUS_CONNECTED if connected else sg.TEAM_STATUS_DISCONNECTED,
        "conectado": connected,
    }


class ParticipantReconnectBusinessTests(unittest.TestCase):

    def setUp(self):
        self.business = PartidaBusiness()
        self.dao = Mock()
        self.business._PartidaBusiness__partida_dao = self.dao

    def join_with(self, partida, existing, dao_result, name="", members=""):
        self.dao.get_participant_by_site.return_value = existing
        self.dao.join_participant_transaction.return_value = dao_result

        with patch.object(self.business, "get_by_code", return_value=partida):
            return self.business.join_game(
                "ABC123",
                "Petapa",
                name,
                members,
            )

    def test_first_join_still_creates_a_new_participant(self):
        created = participant(score=0)
        created["reconnected"] = False
        result = self.join_with(
            game(sg.GAME_STATUS_WAITING),
            None,
            {"success": True, "participant": created, "reconnected": False},
            "Equipo Pitágoras",
            "Ana, Luis",
        )

        self.assertTrue(result.get_success())
        self.assertFalse(result.get_data()["reconnected"])
        self.dao.join_participant_transaction.assert_called_once_with(
            1,
            "PET",
            "Petapa",
            "Equipo Pitágoras",
            "Ana, Luis",
        )

    def test_code_and_site_reuse_connected_participant_and_preserve_score(self):
        existing = participant(connected=1, score=55)
        result = self.join_with(
            game(),
            existing,
            {"success": True, "participant": dict(existing), "reconnected": True},
        )

        self.assertTrue(result.get_success())
        self.assertEqual(result.get_message(), "Equipo reconectado correctamente.")
        self.assertEqual(result.get_data()["id_participante"], 7)
        self.assertEqual(result.get_data()["codigo_participante"], "PET-001")
        self.assertEqual(result.get_data()["puntaje"], 55)
        self.assertEqual(result.get_data()["integrantes"], "Ana, Luis")

    def test_finished_game_only_allows_an_existing_team_to_reconstruct_state(self):
        existing = participant(connected=0)
        reconnected = self.join_with(
            game(sg.GAME_STATUS_FINISHED),
            existing,
            {"success": True, "participant": dict(existing), "reconnected": True},
        )

        self.assertTrue(reconnected.get_success())

        self.dao.reset_mock()
        missing = self.join_with(
            game(sg.GAME_STATUS_FINISHED),
            None,
            {"success": False, "reason": "game_unavailable"},
        )
        self.assertFalse(missing.get_success())
        self.dao.join_participant_transaction.assert_not_called()

    def test_new_team_without_identity_is_not_created_empty(self):
        result = self.join_with(
            game(sg.GAME_STATUS_WAITING),
            None,
            {"success": False},
            "Equipo incompleto",
            "",
        )

        self.assertFalse(result.get_success())
        self.assertIn("integrantes", result.get_message().lower())
        self.dao.join_participant_transaction.assert_not_called()


class FakeConnection:

    def __init__(self):
        self.commits = 0
        self.rollbacks = 0

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1


class JoinCursor:

    def __init__(self, select_results):
        self.select_results = list(select_results)
        self.calls = []
        self.current_result = None

    def execute(self, sql, parameters=()):
        self.calls.append((sql, parameters))

        if sql.lstrip().upper().startswith("SELECT"):
            self.current_result = self.select_results.pop(0)
        else:
            self.current_result = None

        return self

    def fetchone(self):
        return self.current_result


class JoinDao:

    def __init__(self, select_results):
        self.cursor = JoinCursor(select_results)
        self.conexion = FakeConnection()
        self.closed = False

    def conectar(self):
        return True

    def cerrar(self):
        self.closed = True


class ParticipantReconnectDaoTests(unittest.TestCase):

    def test_existing_participant_is_updated_without_insert_and_game_row_is_locked(self):
        existing = participant(connected=1, score=55)
        scripted = JoinDao([
            {"estado": sg.GAME_STATUS_IN_PROGRESS},
            existing,
            existing,
        ])
        dao = PartidaDao()
        dao.dao = scripted

        result = dao.join_participant_transaction(
            1,
            "PET",
            "Petapa",
            "",
            "",
        )

        statements = [sql for sql, parameters in scripted.cursor.calls]
        select_game = next(sql for sql in statements if "FROM partidas" in sql)

        self.assertTrue(result["success"])
        self.assertTrue(result["reconnected"])
        self.assertEqual(result["participant"]["id_participante"], 7)
        self.assertEqual(result["participant"]["puntaje"], 55)
        self.assertIn("FOR UPDATE", select_game)
        self.assertFalse(any("INSERT INTO participantes" in sql for sql in statements))
        self.assertEqual(scripted.conexion.commits, 1)

    def test_schema_guards_one_team_per_site_and_one_request_per_question(self):
        schema = "\n".join(SCHEMA_STATEMENTS).replace(" ", "").replace("\n", "")

        self.assertIn("UNIQUE(id_partida,sede)", schema)
        self.assertIn("UNIQUE(id_partida_pregunta,id_participante)", schema)

    def test_local_disconnect_only_marks_history_disconnected(self):
        dao = PartidaDao()
        scripted = Mock()
        scripted.conectar.return_value = True
        scripted.ejecutar_sql.return_value = True
        scripted.cursor.rowcount = 1
        dao.dao = scripted

        changed = dao.disconnect_participant(1, "PET-001")
        sql = scripted.ejecutar_sql.call_args.args[0]

        self.assertTrue(changed)
        self.assertIn("UPDATE participantes", sql)
        self.assertNotIn("DELETE", sql)
        scripted.ejecutar_sql.assert_called_once_with(
            sql,
            (
                sg.TEAM_STATUS_DISCONNECTED,
                1,
                "PET-001",
            ),
        )


class FakeLiveBusiness:

    def __init__(self, game_state, request_status):
        self.partida = game(game_state)
        self.request_status = request_status

    def get_by_code(self, game_code):
        return self.partida

    def get_waiting_room_status(self, id_partida):
        return [participant(score=55)]

    def get_current_question(self, id_partida):
        return {
            "id_partida_pregunta": 10,
            "id_partida": 1,
            "numero_orden": 1,
            "estado": sg.GAME_QUESTION_STATUS_CURRENT,
            "enunciado": "Pregunta pública",
            "ruta_pregunta": "static/img/preguntas",
            "nombre_imagen_pregunta": "pregunta.png",
            "respuesta_correcta": "Respuesta reservada",
            "ruta_respuesta": "static/img/respuestas",
            "nombre_imagen_respuesta": "respuesta.png",
        }

    def get_word_requests(self, id_partida):
        if not self.request_status:
            return []

        return [{
            "id_solicitud": 3,
            "id_partida": 1,
            "id_partida_pregunta": 10,
            "id_participante": 7,
            "estado": self.request_status,
            "codigo_participante": "PET-001",
            "nombre": "Equipo Pitágoras",
            "sede": "Petapa",
        }]

    def get_live_ranking(self, game_code):
        return {
            "ranking": [{
                "participant_code": "PET-001",
                "sede": "Petapa",
                "puntaje": 55,
            }],
            "total_questions": 1,
        }

    def get_timer_status(self, id_partida):
        return {
            "remaining": 20,
            "exhausted": False,
            "active_since": None,
            "game_state": self.partida.get_estado(),
        }


class ParticipantReconnectStateTests(unittest.TestCase):

    def build_state(self, game_state, request_status):
        with patch.object(
                competition_events,
                "PartidaBusiness",
                return_value=FakeLiveBusiness(game_state, request_status),
        ):
            return competition_events.build_live_state("ABC123")

    def test_queue_and_turn_are_preserved_in_reconstructed_state(self):
        for request_status in (sg.WORD_REQUEST_STATUS_QUEUED, sg.WORD_REQUEST_STATUS_TURN):
            state = self.build_state(sg.GAME_STATUS_IN_PROGRESS, request_status)

            self.assertEqual(state["solicitudes"][0]["estado"], request_status)
            self.assertEqual(state["ranking"]["ranking"][0]["puntaje"], 55)

    def test_paused_and_finished_states_reconstruct_without_private_answer(self):
        paused = self.build_state(sg.GAME_STATUS_PAUSED, sg.WORD_REQUEST_STATUS_TURN)
        finished = self.build_state(sg.GAME_STATUS_FINISHED, sg.WORD_REQUEST_STATUS_CORRECT)

        self.assertIsNone(paused["pregunta"])
        self.assertEqual(paused["estado_competencia"], "PARTIDA PAUSADA")
        self.assertEqual(finished["partida"]["estado"], sg.GAME_STATUS_FINISHED)
        self.assertEqual(finished["estado_competencia"], "Competencia finalizada")
        self.assertNotIn("respuesta_correcta", str(finished))
        self.assertNotIn("respuesta.png", str(finished))


class RegisteredSocketIO:

    def __init__(self):
        self.handlers = {}

    def on(self, event):
        def decorator(function):
            self.handlers[event] = function
            return function
        return decorator

    def emit(self, event, payload, room=None):
        return None

    def start_background_task(self, target, *args, **kwargs):
        return None

    def sleep(self, seconds):
        return None


class ParticipantMultipleSocketTests(unittest.TestCase):

    def setUp(self):
        competition_events.connected_participants.clear()
        self.socketio = RegisteredSocketIO()
        competition_events.register_socket_events(self.socketio)

    def tearDown(self):
        competition_events.connected_participants.clear()

    def test_disconnecting_one_socket_keeps_same_team_connected(self):
        reference = {
            "game_code": "ABC123",
            "participant_code": "PET-001",
        }
        competition_events.connected_participants.update({
            "socket-a": dict(reference),
            "socket-b": dict(reference),
        })

        with patch.object(
                competition_events,
                "request",
                SimpleNamespace(sid="socket-a"),
        ), patch.object(competition_events, "PartidaBusiness") as business_class:
            self.socketio.handlers["disconnect"]()

        business_class.assert_not_called()
        self.assertNotIn("socket-a", competition_events.connected_participants)
        self.assertEqual(
            competition_events.connected_participants["socket-b"],
            reference,
        )


if __name__ == "__main__":
    unittest.main()
