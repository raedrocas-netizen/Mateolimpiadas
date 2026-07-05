class Participante:

    def __init__(self):
        self.__id_participante = None
        self.__partida = None
        self.__codigo_participante = ""
        self.__nombre = ""
        self.__sede = ""
        self.__puntaje = 0
        self.__estado = ""
        self.__conectado = 0

    def set_id_participante(self, id_participante):
        self.__id_participante = id_participante

    def set_partida(self, partida):
        self.__partida = partida

    def set_codigo_participante(self, codigo_participante):
        self.__codigo_participante = codigo_participante

    def set_nombre(self, nombre):
        self.__nombre = nombre

    def set_sede(self, sede):
        self.__sede = sede

    def set_puntaje(self, puntaje):
        self.__puntaje = puntaje

    def set_estado(self, estado):
        self.__estado = estado

    def set_conectado(self, conectado):
        self.__conectado = conectado

    def get_id_participante(self):
        return self.__id_participante

    def get_partida(self):
        return self.__partida

    def get_codigo_participante(self):
        return self.__codigo_participante

    def get_nombre(self):
        return self.__nombre

    def get_sede(self):
        return self.__sede

    def get_puntaje(self):
        return self.__puntaje

    def get_estado(self):
        return self.__estado

    def get_conectado(self):
        return self.__conectado

    def get_data(self):
        id_partida = None

        if self.__partida is not None:
            id_partida = self.__partida.get_id_partida()

        return (
            self.__id_participante,
            id_partida,
            self.__codigo_participante,
            self.__nombre,
            self.__sede,
            self.__puntaje,
            self.__estado,
            self.__conectado
        )
