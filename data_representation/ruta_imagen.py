class RutaImagen:

    def __init__(self):
        self.__id_ruta = None
        self.__descripcion = ""
        self.__ruta = ""

    # Setters

    def set_id_ruta(self, id_ruta):
        self.__id_ruta = id_ruta

    def set_descripcion(self, descripcion):
        self.__descripcion = descripcion

    def set_ruta(self, ruta):
        self.__ruta = ruta

    # Getters

    def get_id_ruta(self):
        return self.__id_ruta

    def get_descripcion(self):
        return self.__descripcion

    def get_ruta(self):
        return self.__ruta

    # Otros métodos

    def get_data(self):
        return (
            self.__id_ruta,
            self.__descripcion,
            self.__ruta
        )
