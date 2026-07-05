from dao.cuestionario_dao import CuestionarioDao
from logical_business.business_result import BusinessResult
import helper.super_global as sg


class CuestionarioBusiness:

    def __init__(self):
        self.__cuestionario_dao = CuestionarioDao()

    def save(self, cuestionario):

        result = BusinessResult()

        nombre = cuestionario.get_nombre().strip()

        if nombre == "":
            result.set_message(
                "Debe ingresar un nombre para el cuestionario."
            )
            return result

        if cuestionario.get_materia() is None:
            result.set_message(
                "Debe seleccionar una materia."
            )
            return result

        if cuestionario.get_area() == "":
            result.set_message(
                "Debe seleccionar un área."
            )
            return result

        if cuestionario.get_estado() == "":
            result.set_message(
                "Debe seleccionar un estado."
            )
            return result

        if self.__cuestionario_dao.exists(nombre):
            result.set_message(
                "Ya existe un cuestionario con ese nombre."
            )
            return result

        cuestionario.set_nombre(nombre)

        if self.__cuestionario_dao.insert(
            cuestionario
        ):

            result.set_success(True)

            result.set_message(
                "Cuestionario guardado correctamente."
            )

            result.set_data(cuestionario)

        else:

            result.set_message(
                "No fue posible guardar el cuestionario."
            )

        return result

    def update(self, cuestionario):

        result = BusinessResult()

        nombre = cuestionario.get_nombre().strip()

        if nombre == "":
            result.set_message(
                "Debe ingresar un nombre para el cuestionario."
            )
            return result

        cuestionario_existente = (
            self.__cuestionario_dao.get_by_name(
                nombre
            )
        )

        if (
            cuestionario_existente is not None
            and
            cuestionario_existente.get_id_cuestionario()
            != cuestionario.get_id_cuestionario()
        ):
            result.set_message(
                "Ya existe un cuestionario con ese nombre."
            )
            return result

        cuestionario.set_nombre(nombre)

        if self.__cuestionario_dao.update(
            cuestionario
        ):

            result.set_success(True)

            result.set_message(
                "Cuestionario modificado correctamente."
            )

            result.set_data(cuestionario)

        else:

            result.set_message(
                "No fue posible modificar el cuestionario."
            )

        return result

    def auto_activate_if_ready(
            self,
            id_cuestionario
    ):

        result = BusinessResult()

        cuestionario = self.__cuestionario_dao.get_by_id(
            id_cuestionario
        )

        if cuestionario is None:
            result.set_message(
                "No fue posible cargar el cuestionario."
            )
            return result

        if (
                cuestionario.get_estado()
                != sg.QUESTIONNAIRE_STATUS_DRAFT
        ):
            result.set_success(True)
            result.set_data(False)
            return result

        complete_questions = (
            self.__cuestionario_dao
            .count_questions_with_answer_by_questionnaire(
                id_cuestionario
            )
        )

        if (
                complete_questions
                < sg.MIN_QUESTIONS_PER_QUESTIONNAIRE
        ):
            result.set_success(True)
            result.set_data(False)
            return result

        cuestionario.set_estado(
            sg.QUESTIONNAIRE_STATUS_ACTIVE
        )

        if not self.__cuestionario_dao.update(
                cuestionario
        ):
            result.set_message(
                "No fue posible activar automáticamente "
                "el cuestionario."
            )
            return result

        result.set_success(True)
        result.set_data(True)
        result.set_message(
            "El cuestionario alcanzó "
            f"{sg.MIN_QUESTIONS_PER_QUESTIONNAIRE} preguntas "
            "con respuesta y fue activado automáticamente."
        )

        return result

    def delete(self, id_cuestionario):

        result = BusinessResult()

        if self.__cuestionario_dao.delete(
            id_cuestionario
        ):

            result.set_success(True)

            result.set_message(
                "Cuestionario eliminado correctamente."
            )

        else:

            result.set_message(
                "No fue posible eliminar el cuestionario."
            )

        return result

    def get_by_id(self, id_cuestionario):
        return self.__cuestionario_dao.get_by_id(
            id_cuestionario
        )

    def get_all(self):
        return self.__cuestionario_dao.get_all()

    def get_by_name(self, nombre):
        return self.__cuestionario_dao.get_by_name(
            nombre
        )

    def get_by_estado(self, estado):
        return self.__cuestionario_dao.get_by_estado(
            estado
        )

    def get_by_area(self, area):
        return self.__cuestionario_dao.get_by_area(
            area
        )

    def get_by_materia(self, id_materia):
        return self.__cuestionario_dao.get_by_materia(
            id_materia
        )

    def exists(self, nombre):
        return self.__cuestionario_dao.exists(
            nombre
        )

    def get_count(self):
        return len(self.get_all())
