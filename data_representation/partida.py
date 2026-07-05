class Partida:

    def __init__(self):
        self.__id_partida = None
        self.__codigo_partida = ""
        self.__nombre = ""
        self.__area = ""
        self.__tiempo_por_pregunta = 0
        self.__puntos_correcta = 0
        self.__penalizacion_incorrecta = 0
        self.__estado = ""
        self.__pregunta_actual = 0
        self.__fecha_creacion = ""
        self.__tiempo_restante_actual = 0
        self.__temporizador_activo_desde = None
        self.__tiempo_agotado = 0

    # Setters

    def set_id_partida(self, id_partida):
        self.__id_partida = id_partida

    def set_codigo_partida(self, codigo_partida):
        self.__codigo_partida = codigo_partida

    def set_nombre(self, nombre):
        self.__nombre = nombre

    def set_area(self, area):
        self.__area = area

    def set_tiempo_por_pregunta(self, tiempo_por_pregunta):
        self.__tiempo_por_pregunta = tiempo_por_pregunta

    def set_puntos_correcta(self, puntos_correcta):
        self.__puntos_correcta = puntos_correcta

    def set_penalizacion_incorrecta(
            self,
            penalizacion_incorrecta
    ):
        self.__penalizacion_incorrecta = penalizacion_incorrecta

    def set_estado(self, estado):
        self.__estado = estado

    def set_pregunta_actual(self, pregunta_actual):
        self.__pregunta_actual = pregunta_actual

    def set_fecha_creacion(self, fecha_creacion):
        self.__fecha_creacion = fecha_creacion

    def set_tiempo_restante_actual(
            self,
            tiempo_restante_actual
    ):
        self.__tiempo_restante_actual = tiempo_restante_actual

    def set_temporizador_activo_desde(
            self,
            temporizador_activo_desde
    ):
        self.__temporizador_activo_desde = temporizador_activo_desde

    def set_tiempo_agotado(self, tiempo_agotado):
        self.__tiempo_agotado = tiempo_agotado

    # Getters

    def get_id_partida(self):
        return self.__id_partida

    def get_codigo_partida(self):
        return self.__codigo_partida

    def get_nombre(self):
        return self.__nombre

    def get_area(self):
        return self.__area

    def get_tiempo_por_pregunta(self):
        return self.__tiempo_por_pregunta

    def get_puntos_correcta(self):
        return self.__puntos_correcta

    def get_penalizacion_incorrecta(self):
        return self.__penalizacion_incorrecta

    def get_estado(self):
        return self.__estado

    def get_pregunta_actual(self):
        return self.__pregunta_actual

    def get_fecha_creacion(self):
        return self.__fecha_creacion

    def get_tiempo_restante_actual(self):
        return self.__tiempo_restante_actual

    def get_temporizador_activo_desde(self):
        return self.__temporizador_activo_desde

    def get_tiempo_agotado(self):
        return self.__tiempo_agotado

    # Otros metodos

    def get_data(self):
        return (
            self.__id_partida,
            self.__codigo_partida,
            self.__nombre,
            self.__area,
            self.__tiempo_por_pregunta,
            self.__puntos_correcta,
            self.__penalizacion_incorrecta,
            self.__estado,
            self.__pregunta_actual,
            self.__fecha_creacion,
            self.__tiempo_restante_actual,
            self.__temporizador_activo_desde,
            self.__tiempo_agotado
        )
