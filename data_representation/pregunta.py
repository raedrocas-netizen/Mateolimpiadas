import os

class Pregunta:

    def __init__(self):
        self.__id_pregunta = None
        self.__cuestionario = None
        self.__enunciado = ""
        self.__ruta_imagen = None
        self.__nombre_imagen = ""

    # Setters

    def set_id_pregunta(self, id_pregunta):
        self.__id_pregunta = id_pregunta

    def set_cuestionario(self, cuestionario):
        self.__cuestionario = cuestionario

    def set_enunciado(self, enunciado):
        self.__enunciado = enunciado

    def set_ruta_imagen(self, ruta_imagen):
        self.__ruta_imagen = ruta_imagen

    def set_nombre_imagen(self, nombre_imagen):
        self.__nombre_imagen = nombre_imagen

    # Getters

    def get_id_pregunta(self):
        return self.__id_pregunta

    def get_cuestionario(self):
        return self.__cuestionario

    def get_enunciado(self):
        return self.__enunciado

    def get_ruta_imagen(self):
        return self.__ruta_imagen

    def get_nombre_imagen(self):
        return self.__nombre_imagen

    def get_full_image_path(self):

        if (
            self.__ruta_imagen is None
            or self.__nombre_imagen == ""
        ):
            return ""

        return os.path.join(
            self.__ruta_imagen.get_ruta(),
            self.__nombre_imagen
        )

    # Otros métodos

    def get_data(self):

        id_cuestionario = None
        id_ruta_imagen = None

        if self.__cuestionario is not None:
            id_cuestionario = (
                self.__cuestionario.get_id_cuestionario()
            )

        if self.__ruta_imagen is not None:
            id_ruta_imagen = (
                self.__ruta_imagen.get_id_ruta()
            )

        return (
            self.__id_pregunta,
            id_cuestionario,
            self.__enunciado,
            id_ruta_imagen,
            self.__nombre_imagen
        )