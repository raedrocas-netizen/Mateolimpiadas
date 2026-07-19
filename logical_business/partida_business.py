import random
import re
import unicodedata
from datetime import datetime

from dao.partida_dao import PartidaDao

from logical_business.business_result import BusinessResult
from logical_business.cuestionario_business import CuestionarioBusiness
from logical_business.pregunta_business import PreguntaBusiness
from logical_business.respuesta_business import RespuestaBusiness

import helper.super_global as sg


class PartidaBusiness:

    ALLOWED_TRANSITIONS = {
        sg.GAME_STATUS_DRAFT: (
            sg.GAME_STATUS_WAITING,
            sg.GAME_STATUS_CANCELLED
        ),
        sg.GAME_STATUS_WAITING: (
            sg.GAME_STATUS_IN_PROGRESS,
            sg.GAME_STATUS_CANCELLED
        ),
        sg.GAME_STATUS_IN_PROGRESS: (
            sg.GAME_STATUS_PAUSED,
            sg.GAME_STATUS_FINISHED,
            sg.GAME_STATUS_CANCELLED
        ),
        sg.GAME_STATUS_PAUSED: (
            sg.GAME_STATUS_IN_PROGRESS,
            sg.GAME_STATUS_FINISHED,
            sg.GAME_STATUS_CANCELLED
        ),
        sg.GAME_STATUS_FINISHED: (),
        sg.GAME_STATUS_CANCELLED: ()
    }

    def __init__(self):
        self.__partida_dao = PartidaDao()
        self.__cuestionario_business = CuestionarioBusiness()
        self.__pregunta_business = PreguntaBusiness()
        self.__respuesta_business = RespuestaBusiness()

    def _set_error(
            self,
            message
    ):

        result = BusinessResult()
        result.set_message(message)
        return result

    def _to_int(
            self,
            value,
            default=None
    ):

        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    def generate_code(
            self,
            length=sg.DEFAULT_GAME_CODE_LENGTH
    ):

        result = BusinessResult()

        length = self._to_int(
            length,
            sg.DEFAULT_GAME_CODE_LENGTH
        )

        if (
                length < sg.MIN_GAME_CODE_LENGTH
                or length > sg.MAX_GAME_CODE_LENGTH
        ):
            result.set_message(
                "La longitud del cÃ³digo debe estar entre "
                f"{sg.MIN_GAME_CODE_LENGTH} y "
                f"{sg.MAX_GAME_CODE_LENGTH} dÃ­gitos."
            )

            return result

        for _ in range(100):
            code = "".join(
                random.choice(sg.GAME_CODE_ALPHABET)
                for _ in range(length)
            )

            if self.get_by_code(code) is None:
                result.set_success(True)
                result.set_message(
                    "CÃ³digo generado correctamente."
                )
                result.set_data(code)
                return result

        result.set_message(
            "No fue posible generar un cÃ³digo Ãºnico."
        )

        return result

    def _validate_partida(
            self,
            partida
    ):

        result = BusinessResult()

        codigo = partida.get_codigo_partida().strip()
        nombre = partida.get_nombre().strip()

        if codigo == "":
            result.set_message(
                "Debe generar el cÃ³digo de partida."
            )
            return result
        if (
                len(codigo) < sg.MIN_GAME_CODE_LENGTH
                or len(codigo) > sg.MAX_GAME_CODE_LENGTH
        ):
            result.set_message(
                "El cÃ³digo de partida debe tener entre "
                f"{sg.MIN_GAME_CODE_LENGTH} y "
                f"{sg.MAX_GAME_CODE_LENGTH} dÃ­gitos."
            )
            return result

        codigo = codigo.upper()

        if any(
                character not in sg.GAME_CODE_ALPHABET
                for character in codigo
        ):
            result.set_message(
                "El codigo de partida contiene caracteres no validos."
            )
            return result

        existing = self.get_by_code(codigo)

        if existing is not None:
            result.set_message(
                "Ya existe una partida con ese cÃ³digo."
            )
            return result

        if nombre == "":
            result.set_message(
                "Debe ingresar un nombre para la partida."
            )
            return result

        if partida.get_area().strip() == "":
            result.set_message(
                "Debe seleccionar un Ã¡rea."
            )
            return result

        tiempo = self._to_int(
            partida.get_tiempo_por_pregunta()
        )

        if (
                tiempo is None
                or tiempo < sg.MIN_GAME_TIME
                or tiempo > sg.MAX_GAME_TIME
        ):
            result.set_message(
                "El tiempo por pregunta debe estar entre "
                f"{sg.MIN_GAME_TIME} y {sg.MAX_GAME_TIME} segundos."
            )
            return result

        puntos = self._to_int(
            partida.get_puntos_correcta()
        )

        if puntos is None or puntos < 0:
            result.set_message(
                "Los puntos por respuesta correcta deben ser "
                "mayores o iguales a 0."
            )
            return result

        penalizacion = self._to_int(
            partida.get_penalizacion_incorrecta()
        )

        if penalizacion is None or penalizacion < 0:
            result.set_message(
                "La penalizaciÃ³n por respuesta incorrecta debe "
                "ser mayor o igual a 0."
            )
            return result

        if partida.get_estado() not in sg.GAME_STATUS:
            result.set_message(
                "El estado de la partida no es vÃ¡lido."
            )
            return result

        partida.set_codigo_partida(codigo)
        partida.set_nombre(nombre)
        partida.set_tiempo_por_pregunta(tiempo)
        partida.set_puntos_correcta(puntos)
        partida.set_penalizacion_incorrecta(penalizacion)

        result.set_success(True)

        return result

    def _collect_valid_questions(
            self,
            cuestionarios
    ):

        result = BusinessResult()

        preguntas_partida = []

        for cuestionario in cuestionarios:

            if (
                    cuestionario.get_estado()
                    != sg.QUESTIONNAIRE_STATUS_ACTIVE
            ):
                result.set_message(
                    "Todos los cuestionarios seleccionados "
                    "deben estar activos."
                )
                return result

            preguntas = (
                self.__pregunta_business
                .get_by_cuestionario(
                    cuestionario.get_id_cuestionario()
                )
            )

            if not preguntas:
                result.set_message(
                    "El cuestionario "
                    f"'{cuestionario.get_nombre()}' "
                    "no contiene preguntas."
                )
                return result

            respuestas_ids = {
                respuesta.get_pregunta().get_id_pregunta()
                for respuesta in (
                    self.__respuesta_business
                    .get_by_cuestionario(
                        cuestionario.get_id_cuestionario()
                    )
                )
            }

            for pregunta in preguntas:
                if pregunta.get_id_pregunta() not in respuestas_ids:
                    result.set_message(
                        "El cuestionario "
                        f"'{cuestionario.get_nombre()}' "
                        "tiene preguntas sin respuesta."
                    )
                    return result

                preguntas_partida.append(
                    pregunta
                )

        if not preguntas_partida:
            result.set_message(
                "No hay preguntas disponibles para generar la partida."
            )
            return result

        random.shuffle(
            preguntas_partida
        )

        result.set_success(True)
        result.set_data(preguntas_partida)

        return result

    def create_game(
            self,
            partida,
            id_cuestionarios
    ):

        validation = self._validate_partida(
            partida
        )

        if not validation.get_success():
            return validation

        result = BusinessResult()

        if not id_cuestionarios:
            result.set_message(
                "Debe seleccionar al menos un cuestionario."
            )
            return result

        cuestionarios = []

        for id_cuestionario in id_cuestionarios:

            cuestionario = (
                self.__cuestionario_business
                .get_by_id(
                    id_cuestionario
                )
            )

            if cuestionario is None:
                result.set_message(
                    "No fue posible cargar uno de los "
                    "cuestionarios seleccionados."
                )
                return result

            cuestionarios.append(
                cuestionario
            )

        questions_result = self._collect_valid_questions(
            cuestionarios
        )

        if not questions_result.get_success():
            return questions_result

        if partida.get_fecha_creacion().strip() == "":
            partida.set_fecha_creacion(
                datetime.now().strftime(
                    sg.DATE_FORMAT
                )
            )

        if partida.get_pregunta_actual() is None:
            partida.set_pregunta_actual(0)

        id_partida = (
            self.__partida_dao
            .create_game_transaction(
                partida,
                cuestionarios,
                questions_result.get_data()
            )
        )

        if id_partida is None:
            result.set_message(
                "No fue posible generar la partida."
            )
            return result

        partida.set_id_partida(id_partida)
        created = partida

        result.set_success(True)
        result.set_message(
            "Partida generada correctamente."
        )
        result.set_data(created)

        return result

    def delete_game(
            self,
            id_partida
    ):

        result = BusinessResult()

        delete_result = (
            self.__partida_dao
            .delete_game_transaction(
                id_partida
            )
        )

        if delete_result.get("success"):
            result.set_success(True)
            result.set_message(
                "Partida eliminada correctamente."
            )
            result.set_data(
                delete_result.get("deleted", {})
            )
            return result

        result.set_message(
            delete_result.get(
                "message",
                "No fue posible eliminar la partida."
            )
        )

        return result

    def get_allowed_next_states(
            self,
            current_state
    ):

        return self.ALLOWED_TRANSITIONS.get(
            current_state,
            ()
        )

    def change_state(
            self,
            id_partida,
            new_state
    ):

        result = BusinessResult()

        partida = self.get_by_id(
            id_partida
        )

        if partida is None:
            result.set_message(
                "No fue posible cargar la partida."
            )
            return result

        allowed_states = self.get_allowed_next_states(
            partida.get_estado()
        )

        if new_state not in allowed_states:
            result.set_message(
                "El cambio de estado no estÃ¡ permitido."
            )
            return result

        current_state = partida.get_estado()

        if (
                current_state == sg.GAME_STATUS_WAITING
                and new_state == sg.GAME_STATUS_IN_PROGRESS
        ):
            return self.start_game(
                id_partida
            )

        if (
                current_state == sg.GAME_STATUS_IN_PROGRESS
                and new_state == sg.GAME_STATUS_PAUSED
        ):
            return self.pause_game(
                id_partida
            )

        if (
                current_state == sg.GAME_STATUS_PAUSED
                and new_state == sg.GAME_STATUS_IN_PROGRESS
        ):
            return self.resume_game(
                id_partida
            )

        if self.__partida_dao.update_estado(
                id_partida,
                new_state
        ):
            result.set_success(True)
            result.set_message(
                "Estado actualizado correctamente."
            )
            result.set_data(
                self.get_by_id(id_partida)
            )
            return result

        result.set_message(
            "No fue posible actualizar el estado."
        )

        return result

    def advance_question(
            self,
            id_partida
    ):

        result = BusinessResult()

        partida = self.get_by_id(
            id_partida
        )

        if partida is None:
            result.set_message(
                "No fue posible cargar la partida."
            )
            return result

        if partida.get_estado() != sg.GAME_STATUS_IN_PROGRESS:
            result.set_message(
                "Solo puede avanzar preguntas con la partida en curso."
            )
            return result

        timer_status = self.get_timer_status(
            id_partida
        )

        if (
                partida.get_pregunta_actual() > 0
                and timer_status is not None
                and timer_status.get("remaining", 0) > 0
        ):
            result.set_message(
                "Debe finalizar el tiempo de la pregunta actual antes "
                "de avanzar."
            )
            return result

        total_questions = self.get_total_questions(
            id_partida
        )

        next_order = (
            partida.get_pregunta_actual()
            + 1
        )

        if next_order > total_questions:
            result.set_message(
                "Ya no hay mÃ¡s preguntas disponibles."
            )
            return result

        dao_result = self.__partida_dao.advance_question_transaction(
                id_partida,
                next_order
        )

        if dao_result:
            result.set_success(True)
            result.set_message(
                "Pregunta actualizada correctamente."
            )
            result.set_data(dao_result)
            return result

        result.set_message(
            "No fue posible avanzar a la siguiente pregunta."
        )

        return result

    def start_game(
            self,
            id_partida
    ):

        partida = self.get_by_id(
            id_partida
        )

        if partida is None:
            return self._set_error(
                "No fue posible cargar la partida."
            )

        if partida.get_estado() != sg.GAME_STATUS_WAITING:
            return self._set_error(
                "Solo puede iniciar una partida en sala de espera."
            )

        result = BusinessResult()

        dao_result = self.__partida_dao.start_game_transaction(
                id_partida
        )

        if dao_result:
            result.set_success(True)
            result.set_message(
                "Partida iniciada correctamente."
            )
            result.set_data(dao_result)
            return result

        result.set_message(
            "No fue posible iniciar la partida."
        )
        return result

    def pause_game(
            self,
            id_partida
    ):

        result = BusinessResult()

        if self.__partida_dao.pause_game_transaction(
                id_partida
        ):
            result.set_success(True)
            result.set_message(
                "Partida pausada correctamente."
            )
            result.set_data(
                self.get_by_id(id_partida)
            )
            return result

        result.set_message(
            "No fue posible pausar la partida."
        )
        return result

    def resume_game(
            self,
            id_partida
    ):

        result = BusinessResult()

        if self.__partida_dao.resume_game_transaction(
                id_partida
        ):
            result.set_success(True)
            result.set_message(
                "Partida reanudada correctamente."
            )
            result.set_data(
                self.get_by_id(id_partida)
            )
            return result

        result.set_message(
            "No fue posible reanudar la partida."
        )
        return result

    def finish_game(
            self,
            id_partida
    ):

        return self.change_state(
            id_partida,
            sg.GAME_STATUS_FINISHED
        )

    def cancel_game(
            self,
            id_partida
    ):

        return self.change_state(
            id_partida,
            sg.GAME_STATUS_CANCELLED
        )

    def get_by_id(
            self,
            id_partida
    ):

        return self.__partida_dao.get_by_id(
            id_partida
        )

    def get_by_code(
            self,
            codigo_partida
    ):

        return self.__partida_dao.get_by_code(
            codigo_partida
        )

    def get_all(self):

        return self.__partida_dao.get_all()

    def get_all_with_summary(self, owner=None):

        return self.__partida_dao.get_all_with_summary(owner=owner)

    def get_by_estado(
            self,
            estado
    ):

        return self.__partida_dao.get_by_estado(
            estado
        )

    def get_recoverable_games(self):

        return self.__partida_dao.get_by_estados(
            sg.RECOVERABLE_GAME_STATUS
        )

    def get_statistics_games(self):

        return self.__partida_dao.get_statistics_games(
            (
                sg.GAME_STATUS_WAITING,
                sg.GAME_STATUS_IN_PROGRESS,
                sg.GAME_STATUS_PAUSED,
                sg.GAME_STATUS_FINISHED
            )
        )

    def get_live_ranking(
            self,
            game_code
    ):

        game_code = str(
            game_code or ""
        ).strip()

        if game_code == "":
            return None

        partida = self.get_by_code(
            game_code
        )

        if partida is None:
            return None

        id_partida = partida.get_id_partida()

        return {
            "game_code": partida.get_codigo_partida(),
            "game_name": partida.get_nombre(),
            "game_state": partida.get_estado(),
            "current_question":
                partida.get_pregunta_actual(),
            "total_questions":
                self.get_total_questions(id_partida),
            "ranking":
                self.__partida_dao.get_live_ranking(
                    id_partida
                ),
            "last_event":
                self.__partida_dao.get_last_game_event(
                    id_partida
                )
        }

    def get_total_questions(
            self,
            id_partida
    ):

        return self.__partida_dao.get_total_questions(
            id_partida
        )

    def get_questions_by_game(
            self,
            id_partida
    ):

        return self.__partida_dao.get_questions_by_game(
            id_partida
        )

    def get_current_question(
            self,
            id_partida
    ):

        return self.__partida_dao.get_current_question(
            id_partida
        )

    def get_timer_status(
            self,
            id_partida
    ):

        return self.__partida_dao.get_timer_status(
            id_partida
        )

    def mark_time_expired(
            self,
            id_partida
    ):

        result = BusinessResult()
        partida = self.get_by_id(
            id_partida
        )

        if partida is None:
            result.set_message(
                "No fue posible cargar la partida."
            )
            return result

        if partida.get_estado() != sg.GAME_STATUS_IN_PROGRESS:
            result.set_message(
                "Solo puede finalizar el tiempo con la partida en curso."
            )
            return result

        if partida.get_pregunta_actual() <= 0:
            result.set_message(
                "No hay una pregunta actual para finalizar."
            )
            return result

        if self.__partida_dao.mark_time_expired_transaction(
                id_partida
        ):
            result.set_success(True)
            result.set_message(
                "Tiempo agotado."
            )
            result.set_data(
                self.get_by_id(id_partida)
            )
            return result

        result.set_message(
            "No fue posible marcar el tiempo agotado."
        )
        return result

    def can_accept_word_request(
            self,
            id_partida
    ):

        result = BusinessResult()

        partida = self.get_by_id(
            id_partida
        )

        if partida is None:
            result.set_message(
                "No fue posible cargar la partida."
            )
            return result

        if partida.get_estado() != sg.GAME_STATUS_IN_PROGRESS:
            result.set_message(
                "Solo se puede pedir la palabra con la partida en curso."
            )
            return result

        timer_status = self.get_timer_status(
            id_partida
        )

        if (
                timer_status is None
                or timer_status["exhausted"]
        ):
            result.set_message(
                "El tiempo de la pregunta ya se agotÃ³."
            )
            return result

        current_question = self.get_current_question(
            id_partida
        )

        if current_question is None:
            result.set_message(
                "No hay pregunta actual."
            )
            return result

        if (
                current_question["estado"]
                != sg.GAME_QUESTION_STATUS_CURRENT
        ):
            result.set_message(
                "La pregunta ya fue cerrada. Espere la siguiente pregunta."
            )
            return result

        result.set_success(True)
        result.set_message(
            "La solicitud de palabra puede registrarse."
        )
        return result

    def get_question_by_order(
            self,
            id_partida,
            numero_orden
    ):

        return self.__partida_dao.get_question_by_order(
            id_partida,
            numero_orden
        )

    def get_participants(
            self,
            id_partida
    ):

        return self.__partida_dao.get_participants(
            id_partida
        )

    def get_participant_by_code(
            self,
            id_partida,
            participant_code
    ):

        return self.__partida_dao.get_participant_by_code(
            id_partida,
            participant_code
        )

    def get_participant_by_site(
            self,
            id_partida,
            site
    ):

        return self.__partida_dao.get_participant_by_site(
            id_partida,
            site
        )

    def join_game(
            self,
            game_code,
            sede,
            nombre,
            integrantes=""
    ):

        game_code = str(game_code or "").strip()
        sede = str(sede or "").strip()
        nombre = str(nombre or "").strip()

        if game_code == "":
            return self._set_error(
                "Debe ingresar el cÃ³digo de partida."
            )

        partida = self.get_by_code(
            game_code
        )

        if partida is None:
            return self._set_error(
                "La partida no existe."
            )

        if partida.get_estado() not in sg.RECOVERABLE_GAME_STATUS:
            if partida.get_estado() == sg.GAME_STATUS_FINISHED:
                return self._set_error(
                    "La sala ya finalizo. Ingresa a otra sala o consulta con el juez."
                )

            return self._set_error(
                "La sala no esta disponible para participantes."
            )

        if sede not in sg.IMB_PC_TEAMS:
            return self._set_error(
                "La sede seleccionada no es vÃ¡lida."
            )

        existing_participant = self.get_participant_by_site(
            partida.get_id_partida(),
            sede
        )

        if (
                existing_participant is None
                and nombre == ""
        ):
            return self._set_error(
                "Debe ingresar el nombre del equipo o participante."
            )

        if (
                existing_participant is not None
                and existing_participant["conectado"] == 1
        ):
            return self._set_error(
                "Esta sede ya estÃ¡ conectada en la partida. "
                "Consulta con el juez antes de volver a ingresar."
            )

        normalized_site = unicodedata.normalize(
            "NFKD",
            sede
        ).encode(
            "ascii",
            "ignore"
        ).decode(
            "ascii"
        )

        code_prefix = re.sub(
            r"[^A-Za-z0-9]",
            "",
            normalized_site
        )[:3].upper()

        if code_prefix == "":
            code_prefix = "EQP"

        dao_result = (
            self.__partida_dao.join_participant_transaction(
                partida.get_id_partida(),
                code_prefix,
                sede,
                nombre,
                integrantes
            )
        )

        if not dao_result.get("success"):
            reason = dao_result.get("reason")

            if reason == "already_connected":
                return self._set_error(
                    "Esta sede ya estÃ¡ conectada en la partida. "
                    "Consulta con el juez antes de volver a ingresar."
                )

            if reason == "game_unavailable":
                return self._set_error(
                    "La partida ya no estÃ¡ disponible."
                )

            return self._set_error(
                "No fue posible conectar al participante."
            )

        participant = dao_result["participant"]
        result = BusinessResult()
        result.set_success(True)
        participant["reconnected"] = dao_result.get(
            "reconnected",
            False
        )

        if participant["reconnected"]:
            result.set_message(
                "ReconexiÃ³n exitosa."
            )
        else:
            result.set_message(
                "Participante conectado correctamente."
            )
        result.set_data(
            participant
        )
        return result

    def disconnect_participant(
            self,
            game_code,
            participant_code
    ):

        result = BusinessResult()
        partida = self.get_by_code(
            str(game_code or "").strip()
        )

        if partida is None:
            result.set_message(
                "La partida no existe."
            )
            return result

        if self.__partida_dao.disconnect_participant(
                partida.get_id_partida(),
                str(participant_code or "").strip()
        ):
            result.set_success(True)
            result.set_message(
                "Participante desconectado correctamente."
            )
            return result

        result.set_message(
            "No fue posible desconectar al participante."
        )
        return result

    def delete_waiting_participant(
            self,
            id_partida,
            id_participante
    ):

        result = BusinessResult()
        dao_result = (
            self.__partida_dao
            .delete_waiting_participant_transaction(
                id_partida,
                id_participante
            )
        )

        if dao_result.get("success"):
            result.set_success(True)
            result.set_message(
                "Participante eliminado correctamente."
            )
            return result

        messages = {
            "game_not_found":
                "La partida no existe.",
            "invalid_game_state":
                "Solo se pueden eliminar participantes en "
                "partidas en borrador o sala de espera.",
            "participant_not_found":
                "Debe seleccionar un participante conectado "
                "o registrado.",
            "participant_has_history":
                "No se puede eliminar un participante con "
                "historial de respuestas o solicitudes."
        }
        result.set_message(
            messages.get(
                dao_result.get("reason"),
                "No fue posible eliminar al participante."
            )
        )
        return result

    def get_participant_question_status(
            self,
            id_partida,
            id_partida_pregunta,
            id_participante
    ):

        return (
            self.__partida_dao
            .get_participant_question_status(
                id_partida,
                id_partida_pregunta,
                id_participante
            )
        )

    def request_word(
            self,
            game_code,
            participant_code
    ):

        result = BusinessResult()
        partida = self.get_by_code(
            str(game_code or "").strip()
        )

        if partida is None:
            result.set_message(
                "La partida no existe."
            )
            return result

        dao_result = (
            self.__partida_dao.request_word_transaction(
                partida.get_id_partida(),
                str(participant_code or "").strip()
            )
        )

        if dao_result.get("success"):
            result.set_success(True)
            result.set_message(
                "Solicitud enviada correctamente."
            )
            result.set_data(
                {
                    "request_order": dao_result[
                        "request_order"
                    ],
                    "request_status": dao_result[
                        "request_status"
                    ],
                    "request": dao_result.get("request"),
                    "queue": dao_result.get("queue", [])
                }
            )
            return result

        messages = {
            "participant_not_found":
                "El participante no existe.",
            "participant_disconnected":
                "El participante estÃ¡ desconectado.",
            "game_not_in_progress":
                "La partida no estÃ¡ en curso.",
            "no_current_question":
                "No hay pregunta actual.",
            "time_exhausted":
                "El tiempo de la pregunta ya se agotÃ³.",
            "question_answered":
                "La pregunta ya fue contestada correctamente.",
            "question_closed":
                "La pregunta ya fue cerrada. Espere la siguiente pregunta.",
            "already_requested":
                "Ya pediste la palabra en esta pregunta.",
            "already_answered":
                "Ya respondiste esta pregunta."
        }

        result.set_message(
            messages.get(
                dao_result.get("reason"),
                "No fue posible enviar la solicitud."
            )
        )
        return result

    def get_waiting_room_status(
            self,
            id_partida
    ):

        participants = self.get_participants(
            id_partida
        )

        participants_by_site = {}

        for participant in participants:
            participants_by_site[
                participant["sede"]
            ] = participant

        waiting_rows = []

        for site in sg.IMB_PC_TEAMS:
            participant = participants_by_site.get(
                site
            )

            if participant is None:
                waiting_rows.append(
                    {
                        "sede": site,
                        "codigo_participante": "",
                        "nombre": "",
                        "puntaje": 0,
                        "estado": sg.TEAM_STATUS_DISCONNECTED,
                        "conectado": 0
                    }
                )
            else:
                waiting_rows.append(
                    participant
                )

        extra_sites = [
            participant
            for participant in participants
            if participant["sede"] not in sg.IMB_PC_TEAMS
        ]

        waiting_rows.extend(
            extra_sites
        )

        return waiting_rows

    def get_word_requests(
            self,
            id_partida
    ):

        return self.__partida_dao.get_word_requests(
            id_partida
        )

    def get_word_request_by_id(
            self,
            id_solicitud
    ):

        return self.__partida_dao.get_word_request_by_id(
            id_solicitud
        )

    def give_word(
            self,
            id_solicitud
    ):

        result = BusinessResult()

        dao_result = self.__partida_dao.give_word_transaction(
                id_solicitud
        )

        if dao_result:
            result.set_success(True)
            result.set_message(
                "Palabra dada correctamente."
            )
            result.set_data(dao_result)
            return result

        result.set_message(
            "No fue posible dar la palabra. Verifique que no haya "
            "otra solicitud en turno."
        )
        return result

    def mark_correct(
            self,
            id_solicitud
    ):

        request = self.get_word_request_by_id(
            id_solicitud
        )

        if request is None:
            return self._set_error(
                "Debe seleccionar una solicitud de palabra."
            )

        partida = self.get_by_id(
            request["id_partida"]
        )

        if partida is None:
            return self._set_error(
                "No fue posible cargar la partida."
            )

        result = self._mark_word_request_result(
            id_solicitud,
            sg.GAME_ANSWER_RESULT_CORRECT,
            partida.get_puntos_correcta(),
            request
        )

        if not result.get_success():
            return result

        timer_result = self.mark_time_expired(
            request["id_partida"]
        )

        if timer_result.get_success():
            data = result.get_data() or {}
            data["timer"] = self.get_timer_status(
                request["id_partida"]
            )
            result.set_data(data)

        return result

    def mark_incorrect(
            self,
            id_solicitud
    ):

        request = self.get_word_request_by_id(
            id_solicitud
        )

        if request is None:
            return self._set_error(
                "Debe seleccionar una solicitud de palabra."
            )

        partida = self.get_by_id(
            request["id_partida"]
        )

        if partida is None:
            return self._set_error(
                "No fue posible cargar la partida."
            )

        return self._mark_word_request_result(
            id_solicitud,
            sg.GAME_ANSWER_RESULT_INCORRECT,
            partida.get_penalizacion_incorrecta() * -1,
            request
        )

    def _mark_word_request_result(
            self,
            id_solicitud,
            resultado,
            puntos_aplicados,
            request=None
    ):

        result = BusinessResult()

        if request is None:
            request = self.get_word_request_by_id(
                id_solicitud
            )

        if request is None:
            result.set_message(
                "Debe seleccionar una solicitud de palabra."
            )
            return result

        if request["estado"] != sg.WORD_REQUEST_STATUS_TURN:
            result.set_message(
                "Solo se puede calificar una solicitud en turno."
            )
            return result

        dao_result = self.__partida_dao.mark_word_request_result_transaction(
                id_solicitud,
                resultado,
                puntos_aplicados
        )

        if dao_result:
            result.set_success(True)
            result.set_message(
                "Respuesta registrada correctamente."
            )
            result.set_data(dao_result)
            return result

        result.set_message(
            "No fue posible registrar la respuesta. El participante "
            "puede haber respondido ya esta pregunta."
        )
        return result

    def pass_word(
            self,
            id_solicitud
    ):

        result = BusinessResult()

        request = self.get_word_request_by_id(
            id_solicitud
        )

        if request is None:
            result.set_message(
                "Debe seleccionar una solicitud de palabra."
            )
            return result

        if request["estado"] != sg.WORD_REQUEST_STATUS_TURN:
            result.set_message(
                "Solo se puede pasar una solicitud en turno."
            )
            return result

        if self.__partida_dao.pass_word_transaction(
                id_solicitud
        ):
            result.set_success(True)
            result.set_message(
                "Palabra pasada correctamente."
            )
            return result

        result.set_message(
            "No fue posible pasar la palabra."
        )
        return result

