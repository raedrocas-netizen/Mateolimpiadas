from dao.materia_dao import MateriaDao
from logical_business.business_result import BusinessResult


class MateriaBusiness:

    def __init__(self):
        self.__materia_dao = MateriaDao()

    def save(self, materia):

        result = BusinessResult()

        nombre = materia.get_nombre().strip()

        if nombre == "":
            result.set_message(
                "Debe ingresar un nombre para la materia."
            )
            return result

        if self.__materia_dao.exists(nombre):
            result.set_message(
                "Ya existe una materia con ese nombre."
            )
            return result

        materia.set_nombre(nombre)

        if self.__materia_dao.insert(materia):

            result.set_success(True)

            result.set_message(
                "Materia guardada correctamente."
            )

            result.set_data(materia)

        else:

            result.set_message(
                "No fue posible guardar la materia."
            )

        return result

    def update(self, materia):

        result = BusinessResult()

        nombre = materia.get_nombre().strip()

        if nombre == "":
            result.set_message(
                "Debe ingresar un nombre para la materia."
            )
            return result

        materia_existente = (
            self.__materia_dao.get_by_name(nombre)
        )

        if (
            materia_existente is not None
            and
            materia_existente.get_id_materia()
            != materia.get_id_materia()
        ):
            result.set_message(
                "Ya existe una materia con ese nombre."
            )
            return result

        materia.set_nombre(nombre)

        if self.__materia_dao.update(materia):

            result.set_success(True)

            result.set_message(
                "Materia modificada correctamente."
            )

            result.set_data(materia)

        else:

            result.set_message(
                "No fue posible modificar la materia."
            )

        return result

    def delete(self, id_materia):

        result = BusinessResult()

        if self.__materia_dao.delete(id_materia):

            result.set_success(True)

            result.set_message(
                "Materia eliminada correctamente."
            )

        else:

            result.set_message(
                "No fue posible eliminar la materia."
            )

        return result

    def get_by_id(self, id_materia):
        return self.__materia_dao.get_by_id(
            id_materia
        )

    def get_all(self):
        return self.__materia_dao.get_all()

    def get_all_names(self):
        return self.__materia_dao.get_all_names()

    def get_by_name(self, nombre):
        return self.__materia_dao.get_by_name(
            nombre
        )

    def exists(self, nombre):
        return self.__materia_dao.exists(
            nombre
        )

    def get_count(self):
        return len(self.get_all())

    def get_by_index(self, index):

        materias = self.get_all()

        if (
                index < 0
                or
                index >= len(materias)
        ):
            return None

        return materias[index]