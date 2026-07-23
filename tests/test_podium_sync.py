import os
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from flask import Flask, session

import helper.super_global as sg
from socket_events import competition_events


class FakePartida:

    def __init__(self, state=sg.GAME_STATUS_FINISHED):
        self.state = state

    def get_estado(self):
        return self.state

    def get_codigo_partida(self):
        return "ABC123"

    def get_id_partida(self):
        return 1


class FakeSocketIO:

    def __init__(self):
        self.handlers = {}
        self.emissions = []

    def on(self, event):
        def decorator(function):
            self.handlers[event] = function
            return function
        return decorator

    def emit(self, event, payload, room=None):
        self.emissions.append((event, payload, room))

    def start_background_task(self, target, *args, **kwargs):
        return None

    def sleep(self, seconds):
        return None


class PodiumSyncTests(unittest.TestCase):

    def setUp(self):
        os.environ["PERFORMANCE_LOGS"] = "0"
        competition_events.connected_judges.clear()
        competition_events.connected_displays.clear()
        competition_events.connected_participants.clear()
        competition_events.podium_states.clear()
        self.socketio = FakeSocketIO()
        competition_events.register_socket_events(self.socketio)
        self.app = Flask(__name__)
        self.app.secret_key = "podium-test"

    def tearDown(self):
        competition_events.connected_judges.clear()
        competition_events.connected_displays.clear()
        competition_events.connected_participants.clear()
        competition_events.podium_states.clear()

    def call_handler(
            self,
            event,
            payload,
            sid="socket-1",
            judge=False,
            business=None
    ):
        business = business or Mock()
        direct_emissions = []

        with self.app.test_request_context("/"):
            if judge:
                session["judge_authenticated"] = True

            with patch.object(
                    competition_events,
                    "request",
                    SimpleNamespace(sid=sid)
            ), patch.object(
                    competition_events,
                    "join_room"
            ), patch.object(
                    competition_events,
                    "leave_room"
            ), patch.object(
                    competition_events,
                    "emit",
                    side_effect=lambda name, data: direct_emissions.append((name, data))
            ), patch.object(
                    competition_events,
                    "PartidaBusiness",
                    return_value=business
            ):
                self.socketio.handlers[event](payload)

        return direct_emissions

    def test_all_official_states_are_valid_and_revision_only_changes_once(self):
        self.assertEqual(
            competition_events.PODIUM_STATES,
            (
                "OCULTO",
                "TERCER_LUGAR",
                "SEGUNDO_LUGAR",
                "PRIMER_LUGAR",
                "COMPLETO"
            )
        )

        state, changed = competition_events.update_podium_state(
            "abc123",
            "TERCER_LUGAR"
        )
        repeated, repeated_changed = competition_events.update_podium_state(
            "ABC123",
            "TERCER_LUGAR"
        )

        self.assertTrue(changed)
        self.assertFalse(repeated_changed)
        self.assertEqual(state["revision"], 1)
        self.assertEqual(repeated["revision"], 1)

    def test_judge_can_change_podium_and_broadcasts_to_all_roles(self):
        sid = "judge-socket"
        competition_events.connected_judges[sid] = "ABC123"
        business = Mock()
        business.get_by_code.return_value = FakePartida()

        self.call_handler(
            "cambiar_estado_podio",
            {"codigo_partida": "ABC123", "estado": "TERCER_LUGAR"},
            sid=sid,
            judge=True,
            business=business
        )

        podium_emissions = [
            (payload, room)
            for event, payload, room in self.socketio.emissions
            if event == "estado_podio"
        ]
        self.assertEqual(
            {room for payload, room in podium_emissions},
            {
                competition_events.game_room("ABC123"),
                competition_events.judge_room("ABC123"),
                competition_events.display_room("ABC123")
            }
        )
        self.assertTrue(all(
            payload["estado"] == "TERCER_LUGAR"
            and payload["revision"] == 1
            for payload, room in podium_emissions
        ))

    def test_authenticated_display_can_change_podium(self):
        sid = "display-socket"
        competition_events.connected_displays[sid] = "ABC123"
        business = Mock()
        business.get_by_code.return_value = FakePartida()

        self.call_handler(
            "cambiar_estado_podio",
            {"codigo_partida": "ABC123", "estado": "COMPLETO"},
            sid=sid,
            judge=True,
            business=business
        )

        self.assertEqual(
            competition_events.podium_state("ABC123")["estado"],
            "COMPLETO"
        )

    def test_unauthenticated_display_cannot_change_podium(self):
        sid = "display-socket"
        competition_events.connected_displays[sid] = "ABC123"

        direct = self.call_handler(
            "cambiar_estado_podio",
            {"codigo_partida": "ABC123", "estado": "TERCER_LUGAR"},
            sid=sid
        )

        self.assertEqual(self.socketio.emissions, [])
        self.assertFalse(direct[0][1]["success"])
        self.assertEqual(
            competition_events.podium_state("ABC123")["estado"],
            "OCULTO"
        )

    def test_participant_cannot_control_even_if_marked_as_display(self):
        sid = "participant-socket"
        competition_events.connected_participants[sid] = {
            "game_code": "ABC123",
            "participant_code": "PET-001"
        }
        competition_events.connected_displays[sid] = "ABC123"

        direct = self.call_handler(
            "cambiar_estado_podio",
            {"codigo_partida": "ABC123", "estado": "PRIMER_LUGAR"},
            sid=sid,
            judge=True
        )

        self.assertEqual(self.socketio.emissions, [])
        self.assertFalse(direct[0][1]["success"])
        self.assertEqual(
            competition_events.podium_state("ABC123")["estado"],
            "OCULTO"
        )

    def test_rejects_invalid_state_and_non_finished_game(self):
        sid = "display-socket"
        competition_events.connected_displays[sid] = "ABC123"
        business = Mock()
        business.get_by_code.return_value = FakePartida(sg.GAME_STATUS_IN_PROGRESS)

        invalid = self.call_handler(
            "cambiar_estado_podio",
            {"codigo_partida": "ABC123", "estado": "INVENTADO"},
            sid=sid,
            judge=True,
            business=business
        )
        before_finish = self.call_handler(
            "cambiar_estado_podio",
            {"codigo_partida": "ABC123", "estado": "TERCER_LUGAR"},
            sid=sid,
            judge=True,
            business=business
        )

        self.assertFalse(invalid[0][1]["success"])
        self.assertFalse(before_finish[0][1]["success"])
        self.assertEqual(self.socketio.emissions, [])

    def test_duplicate_payload_keeps_revision_and_does_not_rebroadcast(self):
        sid = "display-socket"
        competition_events.connected_displays[sid] = "ABC123"
        competition_events.update_podium_state("ABC123", "SEGUNDO_LUGAR")
        business = Mock()
        business.get_by_code.return_value = FakePartida()

        direct = self.call_handler(
            "cambiar_estado_podio",
            {"codigo_partida": "ABC123", "estado": "SEGUNDO_LUGAR"},
            sid=sid,
            judge=True,
            business=business
        )

        self.assertEqual(self.socketio.emissions, [])
        self.assertEqual(direct[0][0], "estado_podio")
        self.assertEqual(direct[0][1]["revision"], 1)

    def test_join_handlers_recover_current_podium_state(self):
        competition_events.update_podium_state("ABC123", "PRIMER_LUGAR")
        state = {
            "partida": {"estado": sg.GAME_STATUS_FINISHED},
            "participantes": [],
            "ranking": {"ranking": []}
        }

        with patch.object(
                competition_events,
                "build_live_state",
                return_value=state
        ):
            judge_direct = self.call_handler(
                "juez_unirse",
                {"codigo_partida": "ABC123"},
                sid="judge-socket",
                judge=True
            )
            display_direct = self.call_handler(
                "display_unirse",
                {"codigo_partida": "ABC123"},
                sid="display-socket"
            )

            participant_business = Mock()
            participant_business.get_by_code.return_value = FakePartida()
            participant_business.get_participant_by_code.return_value = {
                "codigo_participante": "PET-001",
                "sede": "Petapa",
                "nombre": "Euler",
                "integrantes": "Ana, Luis",
                "conectado": 1
            }
            participant_direct = self.call_handler(
                "participante_reconectar",
                {
                    "codigo_partida": "ABC123",
                    "codigo_participante": "PET-001"
                },
                sid="participant-socket",
                business=participant_business
            )

        for direct in (judge_direct, display_direct, participant_direct):
            recovered = [
                payload
                for event, payload in direct
                if event == "estado_podio"
            ]
            self.assertEqual(recovered[0]["estado"], "PRIMER_LUGAR")
            self.assertEqual(recovered[0]["revision"], 1)

    def test_public_participant_payload_is_minimal(self):
        public = competition_events.public_display_participant({
            "id_participante": 10,
            "codigo_participante": "SECRET-CODE",
            "sede": "Petapa",
            "nombre": "Euler",
            "integrantes": "Ana, Luis",
            "conectado": 1,
            "respuesta_correcta": "No exponer"
        })

        self.assertEqual(public, {
            "sede": "Petapa",
            "nombre": "Euler",
            "integrantes": "Ana, Luis",
            "conectado": 1
        })


if __name__ == "__main__":
    unittest.main()
