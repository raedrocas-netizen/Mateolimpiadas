from logical_business.cuestionario_business import CuestionarioBusiness
from logical_business.materia_business import MateriaBusiness
from logical_business.pregunta_business import PreguntaBusiness
from logical_business.respuesta_business import RespuestaBusiness
from logical_business.ruta_imagen_business import RutaImagenBusiness


class WebContentServices:

    def __init__(self):
        self.materias = MateriaBusiness()
        self.cuestionarios = CuestionarioBusiness()
        self.preguntas = PreguntaBusiness()
        self.respuestas = RespuestaBusiness()
        self.rutas_imagenes = RutaImagenBusiness()
