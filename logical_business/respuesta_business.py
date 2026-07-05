from dao.respuesta_dao import RespuestaDao

from logical_business.business_result import (
    BusinessResult
)

import helper.super_global as sg


class RespuestaBusiness:

    def __init__(self):

        self.__respuesta_dao = RespuestaDao()

    def _auto_activate_questionnaire(
            self,
            respuesta
    ):

        pregunta = respuesta.get_pregunta()

        if (
                pregunta is None
                or pregunta.get_cuestionario() is None
        ):
            return None

        id_cuestionario = (
            pregunta
            .get_cuestionario()
            .get_id_cuestionario()
        )

        if id_cuestionario is None:
            return None

        from logical_business.cuestionario_business import (
            CuestionarioBusiness
        )

        return (
            CuestionarioBusiness()
            .auto_activate_if_ready(
                id_cuestionario
            )
        )

    def _validate(
            self,
            respuesta
    ):

        result = BusinessResult()

        descripcion = (
            respuesta.get_descripcion()
            .strip()
        )

        if descripcion == "":

            result.set_message(
                "Debe ingresar una respuesta."
            )

            return result

        if (
                len(descripcion)
                >
                sg.MAX_ANSWER_TEXT_LENGTH
        ):

            result.set_message(
                f"La respuesta no puede superar "
                f"{sg.MAX_ANSWER_TEXT_LENGTH} caracteres."
            )

            return result

        if respuesta.get_pregunta() is None:

            result.set_message(
                "Debe seleccionar una pregunta."
            )

            return result

        respuesta.set_descripcion(
            descripcion
        )

        result.set_success(True)

        return result

    def save(
            self,
            respuesta
    ):

        validation = self._validate(
            respuesta
        )

        if not validation.get_success():
            return validation

        existing_answer = (
            self.__respuesta_dao
            .get_by_pregunta(
                respuesta
                .get_pregunta()
                .get_id_pregunta()
            )
        )

        if existing_answer is not None:

            validation.set_success(False)

            validation.set_message(
                "La pregunta seleccionada ya tiene una respuesta."
            )

            return validation

        result = BusinessResult()

        if self.__respuesta_dao.insert(
                respuesta
        ):

            result.set_success(True)

            result.set_message(
                "Respuesta guardada correctamente."
            )

            result.set_data(
                respuesta
            )

            self._auto_activate_questionnaire(
                respuesta
            )

        else:

            result.set_message(
                "No fue posible guardar la respuesta."
            )

        return result

    def update(
            self,
            respuesta
    ):

        validation = self._validate(
            respuesta
        )

        if not validation.get_success():
            return validation

        existing_answer = (
            self.__respuesta_dao
            .get_by_pregunta(
                respuesta
                .get_pregunta()
                .get_id_pregunta()
            )
        )

        if (
                existing_answer is not None
                and
                existing_answer.get_id_respuesta()
                != respuesta.get_id_respuesta()
        ):

            validation.set_success(False)

            validation.set_message(
                "La pregunta seleccionada ya tiene una respuesta."
            )

            return validation

        result = BusinessResult()

        if self.__respuesta_dao.update(
                respuesta
        ):

            result.set_success(True)

            result.set_message(
                "Respuesta modificada correctamente."
            )

            result.set_data(
                respuesta
            )

            self._auto_activate_questionnaire(
                respuesta
            )

        else:

            result.set_message(
                "No fue posible modificar la respuesta."
            )

        return result

    def delete(
            self,
            id_respuesta
    ):

        result = BusinessResult()

        if self.__respuesta_dao.delete(
                id_respuesta
        ):

            result.set_success(True)

            result.set_message(
                "Respuesta eliminada correctamente."
            )

        else:

            result.set_message(
                "No fue posible eliminar la respuesta."
            )

        return result

    def get_by_id(
            self,
            id_respuesta
    ):

        return self.__respuesta_dao.get_by_id(
            id_respuesta
        )

    def get_by_pregunta(
            self,
            id_pregunta
    ):

        return self.__respuesta_dao.get_by_pregunta(
            id_pregunta
        )

    def get_all(self):

        return self.__respuesta_dao.get_all()

    def get_by_cuestionario(
            self,
            id_cuestionario
    ):

        return (
            self.__respuesta_dao
            .get_by_cuestionario(
                id_cuestionario
            )
        )

    def count_by_route(
            self,
            id_ruta,
            exclude_id_respuesta=None
    ):

        return self.__respuesta_dao.count_by_route(
            id_ruta,
            exclude_id_respuesta
        )

    def update_shared_route(
            self,
            old_id_ruta,
            new_id_ruta,
            exclude_id_respuesta
    ):

        return self.__respuesta_dao.update_shared_route(
            old_id_ruta,
            new_id_ruta,
            exclude_id_respuesta
        )

    def validate_question(
            self,
            id_pregunta
    ):

        result = BusinessResult()

        respuesta = (
            self.__respuesta_dao
            .get_by_pregunta(
                id_pregunta
            )
        )

        if respuesta is None:

            result.set_message(
                "La pregunta debe tener una respuesta."
            )

            return result

        result.set_success(True)

        result.set_message(
            "La pregunta es valida."
        )

        return result

    def get_count(self):

        return len(
            self.get_all()
        )
