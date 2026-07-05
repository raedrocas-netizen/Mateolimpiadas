class RespuestaPartida:

    def __init__(self):
        self.__id_respuesta_partida = None
        self.__partida = None
        self.__partida_pregunta = None
        self.__participante = None
        self.__resultado = ""
        self.__puntos_aplicados = 0
        self.__fecha_hora = ""

    def set_id_respuesta_partida(
            self,
            id_respuesta_partida
    ):
        self.__id_respuesta_partida = id_respuesta_partida

    def set_partida(self, partida):
        self.__partida = partida

    def set_partida_pregunta(self, partida_pregunta):
        self.__partida_pregunta = partida_pregunta

    def set_participante(self, participante):
        self.__participante = participante

    def set_resultado(self, resultado):
        self.__resultado = resultado

    def set_puntos_aplicados(self, puntos_aplicados):
        self.__puntos_aplicados = puntos_aplicados

    def set_fecha_hora(self, fecha_hora):
        self.__fecha_hora = fecha_hora

    def get_id_respuesta_partida(self):
        return self.__id_respuesta_partida

    def get_partida(self):
        return self.__partida

    def get_partida_pregunta(self):
        return self.__partida_pregunta

    def get_participante(self):
        return self.__participante

    def get_resultado(self):
        return self.__resultado

    def get_puntos_aplicados(self):
        return self.__puntos_aplicados

    def get_fecha_hora(self):
        return self.__fecha_hora

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
            self.__id_respuesta_partida,
            id_partida,
            id_partida_pregunta,
            id_participante,
            self.__resultado,
            self.__puntos_aplicados,
            self.__fecha_hora
        )
