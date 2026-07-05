class PartidaPregunta:

    def __init__(self):
        self.__id_partida_pregunta = None
        self.__partida = None
        self.__pregunta = None
        self.__numero_orden = 0
        self.__estado = ""

    def set_id_partida_pregunta(self, id_partida_pregunta):
        self.__id_partida_pregunta = id_partida_pregunta

    def set_partida(self, partida):
        self.__partida = partida

    def set_pregunta(self, pregunta):
        self.__pregunta = pregunta

    def set_numero_orden(self, numero_orden):
        self.__numero_orden = numero_orden

    def set_estado(self, estado):
        self.__estado = estado

    def get_id_partida_pregunta(self):
        return self.__id_partida_pregunta

    def get_partida(self):
        return self.__partida

    def get_pregunta(self):
        return self.__pregunta

    def get_numero_orden(self):
        return self.__numero_orden

    def get_estado(self):
        return self.__estado

    def get_data(self):
        id_partida = None
        id_pregunta = None

        if self.__partida is not None:
            id_partida = self.__partida.get_id_partida()

        if self.__pregunta is not None:
            id_pregunta = self.__pregunta.get_id_pregunta()

        return (
            self.__id_partida_pregunta,
            id_partida,
            id_pregunta,
            self.__numero_orden,
            self.__estado
        )
