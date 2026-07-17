from dao.pregunta_dao import PreguntaDao

from logical_business.business_result import (
    BusinessResult
)
import helper.super_global as sg

class PreguntaBusiness:

    def __init__(self):

        self.__pregunta_dao = (
            PreguntaDao()
        )

    def save(
            self,
            pregunta
    ):

        result = BusinessResult()

        enunciado = (
            pregunta.get_enunciado()
            .strip()
        )

        if enunciado == "":

            result.set_message(
                "Debe ingresar el enunciado de la pregunta."
            )

            return result

        if (
                len(enunciado)
                >
                sg.MAX_QUESTION_TEXT_LENGTH
        ):
            result.set_message(
                f"La pregunta no puede superar "
                f"{sg.MAX_QUESTION_TEXT_LENGTH} caracteres."
            )

            return result

        if pregunta.get_cuestionario() is None:

            result.set_message(
                "Debe seleccionar un cuestionario."
            )

            return result

        pregunta.set_enunciado(
            enunciado
        )

        if self.__pregunta_dao.insert(
                pregunta
        ):

            result.set_success(
                True
            )

            result.set_message(
                "Pregunta guardada correctamente."
            )

            result.set_data(
                pregunta
            )

        else:

            result.set_message(
                "No fue posible guardar la pregunta."
            )

        return result

    def update(
            self,
            pregunta
    ):

        result = BusinessResult()

        enunciado = (
            pregunta.get_enunciado()
            .strip()
        )

        if enunciado == "":

            result.set_message(
                "Debe ingresar el enunciado de la pregunta."
            )

            return result

        if (
                len(enunciado)
                >
                sg.MAX_QUESTION_TEXT_LENGTH
        ):
            result.set_message(
                f"La pregunta no puede superar "
                f"{sg.MAX_QUESTION_TEXT_LENGTH} caracteres."
            )

            return result

        pregunta.set_enunciado(
            enunciado
        )

        if self.__pregunta_dao.update(
                pregunta
        ):

            result.set_success(
                True
            )

            result.set_message(
                "Pregunta modificada correctamente."
            )

            result.set_data(
                pregunta
            )

        else:

            result.set_message(
                "No fue posible modificar la pregunta."
            )

        return result

    def delete(
            self,
            id_pregunta
    ):

        result = BusinessResult()

        if self.__pregunta_dao.count_game_uses(
                id_pregunta
        ) > 0:

            result.set_message(
                "Esta pregunta no puede eliminarse porque ya fue utilizada en una partida."
            )

            return result

        if self.__pregunta_dao.delete(
                id_pregunta
        ):

            result.set_success(
                True
            )

            result.set_message(
                "Pregunta eliminada correctamente."
            )

        else:

            if self.__pregunta_dao.count_game_uses(
                    id_pregunta
            ) > 0:

                result.set_message(
                    "Esta pregunta no puede eliminarse porque ya fue utilizada en una partida."
                )

                return result

            result.set_message(
                "No fue posible eliminar la pregunta."
            )

        return result

    def get_by_id(
            self,
            id_pregunta
    ):

        return self.__pregunta_dao.get_by_id(
            id_pregunta
        )

    def get_all(self):

        return self.__pregunta_dao.get_all()

    def get_by_cuestionario(
            self,
            id_cuestionario
    ):

        return self.__pregunta_dao.get_by_cuestionario(
            id_cuestionario
        )

    def count_by_route(
            self,
            id_ruta,
            exclude_id_pregunta=None
    ):

        return self.__pregunta_dao.count_by_route(
            id_ruta,
            exclude_id_pregunta
        )

    def update_shared_route(
            self,
            old_id_ruta,
            new_id_ruta,
            exclude_id_pregunta
    ):

        return self.__pregunta_dao.update_shared_route(
            old_id_ruta,
            new_id_ruta,
            exclude_id_pregunta
        )

    def get_count(self):

        return len(
            self.get_all()
        )
