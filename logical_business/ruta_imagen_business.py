from dao.ruta_imagen_dao import RutaImagenDao

from logical_business.business_result import (
    BusinessResult
)


class RutaImagenBusiness:

    def __init__(self):

        self.__ruta_imagen_dao = (
            RutaImagenDao()
        )

    def save(
            self,
            ruta_imagen
    ):

        result = BusinessResult()

        descripcion = (
            ruta_imagen
            .get_descripcion()
            .strip()
        )

        ruta = (
            ruta_imagen
            .get_ruta()
            .strip()
        )

        if descripcion == "":

            result.set_message(
                "Debe ingresar una descripción para la ruta."
            )

            return result

        if ruta == "":

            result.set_message(
                "Debe ingresar una ruta."
            )

            return result

        if (
                self.__ruta_imagen_dao
                .exists(
                    descripcion
                )
        ):
            result.set_message(
                "Ya existe una ruta con esa descripcion."
            )

            return result

        if (
                self.__ruta_imagen_dao
                        .exists_path(
                    ruta
                )
        ):
            result.set_message(
                "La ruta ya se encuentra registrada."
            )

            return result

        ruta_imagen.set_descripcion(
            descripcion
        )

        ruta_imagen.set_ruta(
            ruta
        )

        if self.__ruta_imagen_dao.insert(
                ruta_imagen
        ):

            result.set_success(
                True
            )

            result.set_message(
                "Ruta guardada correctamente."
            )

            result.set_data(
                ruta_imagen
            )

        else:

            result.set_message(
                "No fue posible guardar la ruta."
            )

        return result

    def update(
            self,
            ruta_imagen
    ):

        result = BusinessResult()

        descripcion = (
            ruta_imagen
            .get_descripcion()
            .strip()
        )

        ruta = (
            ruta_imagen
            .get_ruta()
            .strip()
        )

        if descripcion == "":

            result.set_message(
                "Debe ingresar una descripción para la ruta."
            )

            return result

        if ruta == "":

            result.set_message(
                "Debe ingresar una ruta."
            )

            return result

        descripcion_existente = (
            self.__ruta_imagen_dao
            .get_by_description(
                descripcion
            )
        )

        if (
                descripcion_existente is not None
                and
                descripcion_existente.get_id_ruta()
                != ruta_imagen.get_id_ruta()
        ):
            result.set_message(
                "Ya existe una ruta con esa descripcion."
            )

            return result

        ruta_existente = (
            self.__ruta_imagen_dao
            .get_by_path(
                ruta
            )
        )

        if (
                ruta_existente is not None
                and
                ruta_existente.get_id_ruta()
                != ruta_imagen.get_id_ruta()
        ):
            result.set_message(
                "La ruta ya se encuentra registrada."
            )

            return result

        ruta_imagen.set_descripcion(
            descripcion
        )

        ruta_imagen.set_ruta(
            ruta
        )

        if self.__ruta_imagen_dao.update(
                ruta_imagen
        ):

            result.set_success(
                True
            )

            result.set_message(
                "Ruta modificada correctamente."
            )

            result.set_data(
                ruta_imagen
            )

        else:

            result.set_message(
                "No fue posible modificar la ruta."
            )

        return result

    def delete(
            self,
            id_ruta
    ):

        result = BusinessResult()

        if self.__ruta_imagen_dao.delete(
                id_ruta
        ):

            result.set_success(
                True
            )

            result.set_message(
                "Ruta eliminada correctamente."
            )

        else:

            result.set_message(
                "No fue posible eliminar la ruta."
            )

        return result

    def get_by_id(
            self,
            id_ruta
    ):

        return self.__ruta_imagen_dao.get_by_id(
            id_ruta
        )

    def get_by_description(
            self,
            descripcion
    ):

        return (
            self.__ruta_imagen_dao
            .get_by_description(
                descripcion
            )
        )

    def get_all(self):

        return self.__ruta_imagen_dao.get_all()

    def exists(
            self,
            descripcion
    ):

        return self.__ruta_imagen_dao.exists(
            descripcion
        )

    def get_all_descriptions(self):

        rutas = self.get_all()

        return [
            ruta.get_descripcion()
            for ruta in rutas
        ]

    def get_by_path(
            self,
            ruta
    ):

        return (
            self.__ruta_imagen_dao
            .get_by_path(
                ruta
            )
        )

    def exists_path(
            self,
            ruta
    ):

        return (
            self.__ruta_imagen_dao
            .exists_path(
                ruta
            )
        )

    def get_usage_counts(
            self,
            id_ruta
    ):

        question_uses = (
            self.__ruta_imagen_dao
            .count_question_uses(
                id_ruta
            )
        )

        answer_uses = (
            self.__ruta_imagen_dao
            .count_answer_uses(
                id_ruta
            )
        )

        return (
            question_uses,
            answer_uses
        )

    def get_attachment_usage_counts(
            self,
            id_ruta,
            image_name
    ):

        question_uses = (
            self.__ruta_imagen_dao
            .count_question_attachment_uses(
                id_ruta,
                image_name
            )
        )

        answer_uses = (
            self.__ruta_imagen_dao
            .count_answer_attachment_uses(
                id_ruta,
                image_name
            )
        )

        return (
            question_uses,
            answer_uses
        )
