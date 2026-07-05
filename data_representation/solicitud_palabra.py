class SolicitudPalabra:

    def __init__(self):
        self.__id_solicitud = None
        self.__partida = None
        self.__partida_pregunta = None
        self.__participante = None
        self.__orden_solicitud = 0
        self.__fecha_hora = ""
        self.__estado = ""

    def set_id_solicitud(self, id_solicitud):
        self.__id_solicitud = id_solicitud

    def set_partida(self, partida):
        self.__partida = partida

    def set_partida_pregunta(self, partida_pregunta):
        self.__partida_pregunta = partida_pregunta

    def set_participante(self, participante):
        self.__participante = participante

    def set_orden_solicitud(self, orden_solicitud):
        self.__orden_solicitud = orden_solicitud

    def set_fecha_hora(self, fecha_hora):
        self.__fecha_hora = fecha_hora

    def set_estado(self, estado):
        self.__estado = estado

    def get_id_solicitud(self):
        return self.__id_solicitud

    def get_partida(self):
        return self.__partida

    def get_partida_pregunta(self):
        return self.__partida_pregunta

    def get_participante(self):
        return self.__participante

    def get_orden_solicitud(self):
        return self.__orden_solicitud

    def get_fecha_hora(self):
        return self.__fecha_hora

    def get_estado(self):
        return self.__estado

    def get_data(self):
        id_partida = None
        id_partida_pregunta = None
        id_participante = None

        if self.__partida is not None:
            id_partida = self.__partida.get_id_partida()

        if self.__partida_pregunta is not None:
            id_partida_pregunta = (
                self.__partida_pregunta
                .get_id_partida_pregunta()
            )

        if self.__participante is not None:
            id_participante = (
                self.__participante.get_id_participante()
            )

        return (
            self.__id_solicitud,
            id_partida,
            id_partida_pregunta,
            id_participante,
            self.__orden_solicitud,
            self.__fecha_hora,
            self.__estado
        )
