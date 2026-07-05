class Materia:

    def __init__(self):
        self.__id_materia = None
        self.__nombre = ""

    # Setters

    def set_id_materia(self, id_materia):
        self.__id_materia = id_materia

    def set_nombre(self, nombre):
        self.__nombre = nombre

    # Getters

    def get_id_materia(self):
        return self.__id_materia

    def get_nombre(self):
        return self.__nombre

    # Otros métodos

    def get_data(self):
        return (
            self.__id_materia,
            self.__nombre
        )
