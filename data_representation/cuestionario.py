class Cuestionario:

    def __init__(self):
        self.__id_cuestionario = None
        self.__nombre = ""
        self.__materia = None
        self.__area = ""
        self.__estado = ""
        self.__fecha_creacion = ""

    # Setters

    def set_id_cuestionario(self, id_cuestionario):
        self.__id_cuestionario = id_cuestionario

    def set_nombre(self, nombre):
        self.__nombre = nombre

    def set_materia(self, materia):
        self.__materia = materia

    def set_area(self, area):
        self.__area = area

    def set_estado(self, estado):
        self.__estado = estado

    def set_fecha_creacion(self, fecha_creacion):
        self.__fecha_creacion = fecha_creacion

    # Getters

    def get_id_cuestionario(self):
        return self.__id_cuestionario

    def get_nombre(self):
        return self.__nombre

    def get_materia(self):
        return self.__materia

    def get_area(self):
        return self.__area

    def get_estado(self):
        return self.__estado

    def get_fecha_creacion(self):
        return self.__fecha_creacion

    # Otros métodos

    def get_data(self):

        id_materia = None

        if self.__materia is not None:
            id_materia = self.__materia.get_id_materia()

        return (
            self.__id_cuestionario,
            self.__nombre,
            id_materia,
            self.__area,
            self.__estado,
            self.__fecha_creacion
        )
