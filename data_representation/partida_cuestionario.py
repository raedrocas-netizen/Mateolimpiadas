class PartidaCuestionario:

    def __init__(self):
        self.__id_partida_cuestionario = None
        self.__partida = None
        self.__cuestionario = None

    def set_id_partida_cuestionario(
            self,
            id_partida_cuestionario
    ):
        self.__id_partida_cuestionario = id_partida_cuestionario

    def set_partida(self, partida):
        self.__partida = partida

    def set_cuestionario(self, cuestionario):
        self.__cuestionario = cuestionario

    def get_id_partida_cuestionario(self):
        return self.__id_partida_cuestionario

    def get_partida(self):
        return self.__partida

    def get_cuestionario(self):
        return self.__cuestionario

    def get_data(self):
        id_partida = None
        id_cuestionario = None

        if self.__partida is not None:
            id_partida = self.__partida.get_id_partida()

        if self.__cuestionario is not None:
            id_cuestionario = (
                self.__cuestionario.get_id_cuestionario()
            )

        return (
            self.__id_partida_cuestionario,
            id_partida,
            id_cuestionario
        )
