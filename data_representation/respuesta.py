import os


class Respuesta:

    def __init__(self):

        self.__id_respuesta = None

        self.__pregunta = None

        self.__descripcion = ""

        self.__ruta_imagen = None

        self.__nombre_imagen = ""

    # ==========================================
    # SETTERS
    # ==========================================

    def set_id_respuesta(
            self,
            id_respuesta
    ):

        self.__id_respuesta = id_respuesta

    def set_pregunta(
            self,
            pregunta
    ):

        self.__pregunta = pregunta

    def set_descripcion(
            self,
            descripcion
    ):

        self.__descripcion = descripcion

    def set_ruta_imagen(
            self,
            ruta_imagen
    ):

        self.__ruta_imagen = ruta_imagen

    def set_nombre_imagen(
            self,
            nombre_imagen
    ):

        self.__nombre_imagen = nombre_imagen

    # ==========================================
    # GETTERS
    # ==========================================

    def get_id_respuesta(self):

        return self.__id_respuesta

    def get_pregunta(self):

        return self.__pregunta

    def get_descripcion(self):

        return self.__descripcion

    def get_ruta_imagen(self):

        return self.__ruta_imagen

    def get_nombre_imagen(self):

        return self.__nombre_imagen

    # ==========================================
    # OTROS METODOS
    # ==========================================

    def get_full_image_path(self):

        if (
                self.__ruta_imagen is None
                or
                self.__nombre_imagen == ""
        ):
            return ""

        return os.path.join(
            self.__ruta_imagen.get_ruta(),
            self.__nombre_imagen
        )

    def get_data(self):

        id_pregunta = None

        id_ruta = None

        if self.__pregunta is not None:

            id_pregunta = (
                self.__pregunta
                .get_id_pregunta()
            )

        if self.__ruta_imagen is not None:

            id_ruta = (
                self.__ruta_imagen
                .get_id_ruta()
            )

        return (
            self.__id_respuesta,
            id_pregunta,
            self.__descripcion,
            id_ruta,
            self.__nombre_imagen
        )
