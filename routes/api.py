import os
from datetime import datetime
from uuid import uuid4

from flask import Blueprint, current_app, g, jsonify, request, session
from werkzeug.exceptions import HTTPException
from werkzeug.utils import secure_filename

import helper.super_global as sg
from data_representation.cuestionario import Cuestionario
from data_representation.materia import Materia
from data_representation.partida import Partida
from data_representation.pregunta import Pregunta
from data_representation.respuesta import Respuesta
from data_representation.ruta_imagen import RutaImagen
from logical_business.business_result import BusinessResult
from helpers.serializers import (
    business_result_to_dict,
    cuestionario_to_dict,
    game_question_to_dict,
    materia_to_dict,
    partida_to_dict,
    pregunta_to_dict,
    respuesta_to_dict,
    ruta_imagen_to_dict,
    serialize_any,
)
from helpers.ownership import (
    get_owned_ids,
    is_owned,
    current_owner,
)
from helpers.performance import begin_operation, finish_operation, measure_serialization
from logical_business.cuestionario_business import CuestionarioBusiness
from logical_business.materia_business import MateriaBusiness
from logical_business.partida_business import PartidaBusiness
from logical_business.pregunta_business import PreguntaBusiness
from logical_business.respuesta_business import RespuestaBusiness
from logical_business.ruta_imagen_business import RutaImagenBusiness


api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.before_request
def start_api_performance():
    context, token = begin_operation(
        f"{request.method} {request.path}",
        kind="api"
    )
    g.performance_context = context
    g.performance_token = token


@api_bp.after_request
def finish_api_performance(response):
    finish_operation(
        getattr(g, "performance_context", None),
        getattr(g, "performance_token", None),
        status=response.status_code
    )
    g.performance_context = None
    g.performance_token = None
    return response


def payload():
    return request.get_json(silent=True) or request.form.to_dict()


def current_question_requests(solicitudes, pregunta):
    current_question_id = (
        pregunta.get("id_partida_pregunta")
        if isinstance(pregunta, dict)
        else None
    )

    if current_question_id is None:
        return []

    current_question_id = str(current_question_id)

    return [
        item
        for item in solicitudes
        if str(item.get("id_partida_pregunta")) == current_question_id
    ]


def json_result(result, status=200):
    with measure_serialization():
        response = jsonify(business_result_to_dict(result))

    return response, status


def json_data(data, status=200):
    with measure_serialization():
        response = jsonify(data)

    return response, status


def error_json(message, status=400):
    with measure_serialization():
        response = jsonify({
            "success": False,
            "message": message,
            "data": None
        })

    return response, status


@api_bp.errorhandler(Exception)
def api_error(error):
    if isinstance(error, HTTPException):
        return error_json(error.description, error.code)

    current_app.logger.exception("Error en API")
    return error_json(
        "Ocurrio un error interno al procesar la solicitud.",
        500
    )


def success_result(message, data=None):
    result = BusinessResult()
    result.set_success(True)
    result.set_message(message)
    result.set_data(data)
    return result


def to_int(value, default):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


@api_bp.get("/catalogos")
def catalogs():
    return json_data({
        "areas": list(sg.AREAS),
        "estados_cuestionario": list(sg.QUESTIONNAIRE_STATUS),
        "sedes": list(sg.IMB_PC_TEAMS),
        "estados_partida": list(sg.GAME_STATUS)
    })


@api_bp.route("/materias", methods=["GET", "POST"])
def materias():
    business = MateriaBusiness()

    if request.method == "GET":
        items = business.get_all()
        return json_data([materia_to_dict(item) for item in items])

    data = payload()
    materia = Materia()
    materia.set_nombre(data.get("nombre", ""))
    result = business.save(materia)

    if result.get_success():
        return json_result(
            success_result(
                result.get_message(),
                materia
            )
        )

    return json_result(result)


@api_bp.route("/materias/<int:id_materia>", methods=["PUT", "DELETE"])
def materia_detail(id_materia):
    business = MateriaBusiness()

    if request.method == "DELETE":
        if not is_owned("materias", "id_materia", id_materia):
            return error_json("La materia no pertenece a este juez.", 403)
        result = business.delete(id_materia)
        return json_result(
            result,
            200 if result.get_success() else 409
        )

    data = payload()
    materia = Materia()
    materia.set_id_materia(id_materia)
    materia.set_nombre(data.get("nombre", ""))
    if not is_owned("materias", "id_materia", id_materia):
        return error_json("La materia no pertenece a este juez.", 403)
    result = business.update(materia)

    if result.get_success():
        return json_result(
            success_result(
                result.get_message(),
                materia
            )
        )

    return json_result(result)


@api_bp.route("/cuestionarios", methods=["GET", "POST"])
def cuestionarios():
    business = CuestionarioBusiness()

    if request.method == "GET":
        items = business.get_all()
        id_materia = request.args.get("id_materia")
        area = request.args.get("area")

        if id_materia:
            if not is_owned("materias", "id_materia", int(id_materia)):
                return json_data([])
            items = [
                item
                for item in items
                if item.get_materia().get_id_materia() == int(id_materia)
            ]
        elif area:
            items = [
                item
                for item in items
                if item.get_area() == area
            ]

        return json_data([cuestionario_to_dict(item) for item in items])

    data = payload()
    id_materia = int(data.get("id_materia", 0))

    if not is_owned("materias", "id_materia", id_materia):
        return error_json("Debe seleccionar una materia propia.", 403)

    materia = MateriaBusiness().get_by_id(id_materia)
    cuestionario = Cuestionario()
    cuestionario.set_nombre(data.get("nombre", ""))
    cuestionario.set_materia(materia)
    cuestionario.set_area(data.get("area", ""))
    cuestionario.set_estado(data.get("estado", sg.QUESTIONNAIRE_STATUS_DRAFT))
    cuestionario.set_fecha_creacion(datetime.now().strftime(sg.DATE_FORMAT))
    result = business.save(cuestionario)

    if result.get_success():
        return json_result(
            success_result(
                result.get_message(),
                cuestionario
            )
        )

    return json_result(result)


@api_bp.route("/cuestionarios/<int:id_cuestionario>", methods=["PUT", "DELETE"])
def cuestionario_detail(id_cuestionario):
    business = CuestionarioBusiness()

    if request.method == "DELETE":
        if not is_owned("cuestionarios", "id_cuestionario", id_cuestionario):
            return error_json("El cuestionario no pertenece a este juez.", 403)
        result = business.delete(id_cuestionario)
        return json_result(
            result,
            200 if result.get_success() else 409
        )

    data = payload()
    if not is_owned("cuestionarios", "id_cuestionario", id_cuestionario):
        return error_json("El cuestionario no pertenece a este juez.", 403)

    id_materia = int(data.get("id_materia", 0))
    if not is_owned("materias", "id_materia", id_materia):
        return error_json("Debe seleccionar una materia propia.", 403)

    materia = MateriaBusiness().get_by_id(id_materia)
    cuestionario = business.get_by_id(id_cuestionario) or Cuestionario()
    cuestionario.set_id_cuestionario(id_cuestionario)
    cuestionario.set_nombre(data.get("nombre", ""))
    cuestionario.set_materia(materia)
    cuestionario.set_area(data.get("area", ""))
    cuestionario.set_estado(data.get("estado", sg.QUESTIONNAIRE_STATUS_DRAFT))
    cuestionario.set_fecha_creacion(cuestionario.get_fecha_creacion() or datetime.now().strftime(sg.DATE_FORMAT))
    result = business.update(cuestionario)

    if result.get_success():
        return json_result(
            success_result(
                result.get_message(),
                cuestionario
            )
        )

    return json_result(result)


@api_bp.get("/cuestionarios/<int:id_cuestionario>/preguntas-detalle")
def cuestionario_preguntas_detalle(id_cuestionario):
    if not is_owned("cuestionarios", "id_cuestionario", id_cuestionario):
        return error_json("El cuestionario no pertenece a este juez.", 403)

    preguntas = PreguntaBusiness().get_by_cuestionario(id_cuestionario)
    respuestas = {
        respuesta.get_pregunta().get_id_pregunta(): respuesta
        for respuesta in RespuestaBusiness().get_by_cuestionario(id_cuestionario)
    }

    return json_data([
        {
            "pregunta": pregunta_to_dict(pregunta),
            "respuesta": respuesta_to_dict(
                respuestas.get(pregunta.get_id_pregunta())
            )
        }
        for pregunta in preguntas
    ])


@api_bp.route("/rutas-imagen", methods=["GET", "POST"])
def rutas_imagen():
    business = RutaImagenBusiness()

    if request.method == "GET":
        items = business.get_all()
        return json_data([ruta_imagen_to_dict(item) for item in items])

    data = payload()
    ruta = RutaImagen()
    ruta.set_descripcion(data.get("descripcion", ""))
    ruta.set_ruta(data.get("ruta", ""))
    result = business.save(ruta)

    return json_result(result)


@api_bp.route("/preguntas", methods=["GET", "POST"])
def preguntas():
    business = PreguntaBusiness()

    if request.method == "GET":
        id_cuestionario = request.args.get("id_cuestionario")

        if id_cuestionario:
            if not is_owned("cuestionarios", "id_cuestionario", int(id_cuestionario)):
                return json_data([])
            items = business.get_by_cuestionario(int(id_cuestionario))
        else:
            allowed = set(get_owned_ids("cuestionarios", "id_cuestionario"))
            items = [
                item
                for item in business.get_all()
                if item.get_cuestionario().get_id_cuestionario() in allowed
            ]
        return json_data([pregunta_to_dict(item) for item in items])

    data = payload()
    id_cuestionario = int(data.get("id_cuestionario", 0))
    if not is_owned("cuestionarios", "id_cuestionario", id_cuestionario):
        return error_json("El cuestionario no pertenece a este juez.", 403)

    pregunta = Pregunta()
    pregunta.set_cuestionario(CuestionarioBusiness().get_by_id(id_cuestionario))
    pregunta.set_enunciado(data.get("enunciado", ""))
    pregunta.set_nombre_imagen(data.get("nombre_imagen", ""))
    id_ruta = data.get("id_ruta_imagen")
    pregunta.set_ruta_imagen(RutaImagenBusiness().get_by_id(int(id_ruta)) if id_ruta else None)
    result = business.save(pregunta)

    if result.get_success():
        created = pregunta

        if created.get_id_pregunta() is None:
            preguntas_creadas = business.get_by_cuestionario(id_cuestionario)
            created = preguntas_creadas[-1] if preguntas_creadas else pregunta

        return json_result(
            success_result(
                result.get_message(),
                created
            )
        )

    return json_result(result)


@api_bp.route("/preguntas/<int:id_pregunta>", methods=["PUT", "DELETE"])
def pregunta_detail(id_pregunta):
    business = PreguntaBusiness()

    if request.method == "DELETE":
        pregunta = business.get_by_id(id_pregunta)
        if (
                pregunta is None
                or not is_owned(
                    "cuestionarios",
                    "id_cuestionario",
                    pregunta.get_cuestionario().get_id_cuestionario()
                )
        ):
            return error_json("La pregunta no pertenece a este juez.", 403)
        return json_result(business.delete(id_pregunta))

    data = payload()
    pregunta = business.get_by_id(id_pregunta) or Pregunta()
    id_cuestionario = int(data.get("id_cuestionario", 0))
    if not is_owned("cuestionarios", "id_cuestionario", id_cuestionario):
        return error_json("El cuestionario no pertenece a este juez.", 403)
    pregunta.set_id_pregunta(id_pregunta)
    pregunta.set_cuestionario(CuestionarioBusiness().get_by_id(id_cuestionario))
    pregunta.set_enunciado(data.get("enunciado", ""))
    pregunta.set_nombre_imagen(data.get("nombre_imagen", ""))
    id_ruta = data.get("id_ruta_imagen")
    pregunta.set_ruta_imagen(RutaImagenBusiness().get_by_id(int(id_ruta)) if id_ruta else None)
    result = business.update(pregunta)

    if result.get_success():
        return json_result(
            success_result(
                result.get_message(),
                business.get_by_id(id_pregunta)
            )
        )

    return json_result(result)


@api_bp.route("/respuestas", methods=["GET", "POST"])
def respuestas():
    business = RespuestaBusiness()

    if request.method == "GET":
        id_pregunta = request.args.get("id_pregunta")
        if id_pregunta:
            pregunta = PreguntaBusiness().get_by_id(int(id_pregunta))
            if (
                    pregunta is None
                    or not is_owned(
                        "cuestionarios",
                        "id_cuestionario",
                        pregunta.get_cuestionario().get_id_cuestionario()
                    )
            ):
                return json_data(None)
            return json_data(respuesta_to_dict(business.get_by_pregunta(int(id_pregunta))))

        allowed = set(get_owned_ids("cuestionarios", "id_cuestionario"))
        return json_data([
            respuesta_to_dict(item)
            for item in business.get_all()
            if (
                item.get_pregunta().get_cuestionario().get_id_cuestionario()
                in allowed
            )
        ])

    data = payload()
    id_pregunta = data.get("id_pregunta")

    if id_pregunta in (None, ""):
        return error_json("No se recibio el identificador de la pregunta.", 400)

    pregunta = PreguntaBusiness().get_by_id(int(id_pregunta))
    if (
            pregunta is None
            or not is_owned(
                "cuestionarios",
                "id_cuestionario",
                pregunta.get_cuestionario().get_id_cuestionario()
            )
    ):
        return error_json("La pregunta no pertenece a este juez.", 403)

    respuesta = Respuesta()
    respuesta.set_pregunta(pregunta)
    respuesta.set_descripcion(data.get("descripcion", ""))
    respuesta.set_nombre_imagen(data.get("nombre_imagen", ""))
    id_ruta = data.get("id_ruta_imagen")
    respuesta.set_ruta_imagen(RutaImagenBusiness().get_by_id(int(id_ruta)) if id_ruta else None)
    result = business.save(respuesta)

    if result.get_success():
        return json_result(
            success_result(
                result.get_message(),
                respuesta
            )
        )

    return json_result(result)


@api_bp.route("/respuestas/<int:id_respuesta>", methods=["PUT", "DELETE"])
def respuesta_detail(id_respuesta):
    business = RespuestaBusiness()

    if request.method == "DELETE":
        respuesta = business.get_by_id(id_respuesta)
        if (
                respuesta is None
                or not is_owned(
                    "cuestionarios",
                    "id_cuestionario",
                    respuesta.get_pregunta().get_cuestionario().get_id_cuestionario()
                )
        ):
            return error_json("La respuesta no pertenece a este juez.", 403)
        return json_result(business.delete(id_respuesta))

    data = payload()
    pregunta = PreguntaBusiness().get_by_id(int(data.get("id_pregunta", 0)))
    if (
            pregunta is None
            or not is_owned(
                "cuestionarios",
                "id_cuestionario",
                pregunta.get_cuestionario().get_id_cuestionario()
            )
    ):
        return error_json("La pregunta no pertenece a este juez.", 403)

    respuesta = business.get_by_id(id_respuesta) or Respuesta()
    respuesta.set_id_respuesta(id_respuesta)
    respuesta.set_pregunta(pregunta)
    respuesta.set_descripcion(data.get("descripcion", ""))
    respuesta.set_nombre_imagen(data.get("nombre_imagen", ""))
    id_ruta = data.get("id_ruta_imagen")
    respuesta.set_ruta_imagen(RutaImagenBusiness().get_by_id(int(id_ruta)) if id_ruta else None)
    result = business.update(respuesta)

    if result.get_success():
        return json_result(
            success_result(
                result.get_message(),
                respuesta
            )
        )

    return json_result(result)


@api_bp.get("/partidas")
def partidas():
    return json_data(
        serialize_any(PartidaBusiness().get_all_with_summary(current_owner()))
    )


@api_bp.get("/partidas/generar-codigo")
def generar_codigo():
    return json_result(PartidaBusiness().generate_code(6))


@api_bp.post("/partidas")
def crear_partida():
    data = payload()
    business = PartidaBusiness()
    codigo = str(data.get("codigo_partida", "")).strip().upper()

    if not codigo:
        generated = business.generate_code(6)
        if not generated.get_success():
            return json_result(generated, 400)
        codigo = generated.get_data()

    partida = Partida()
    partida.set_codigo_partida(codigo)
    partida.set_nombre(data.get("nombre", ""))
    partida.set_area(data.get("area", ""))
    tiempo = to_int(data.get("tiempo_por_pregunta"), sg.DEFAULT_GAME_TIME)
    partida.set_tiempo_por_pregunta(tiempo)
    partida.set_puntos_correcta(to_int(data.get("puntos_correcta"), sg.DEFAULT_GAME_CORRECT_POINTS))
    partida.set_penalizacion_incorrecta(to_int(data.get("penalizacion_incorrecta"), sg.DEFAULT_GAME_INCORRECT_PENALTY))
    partida.set_estado(sg.GAME_STATUS_WAITING)
    partida.set_pregunta_actual(0)
    partida.set_fecha_creacion(datetime.now().strftime(sg.DATE_FORMAT))
    partida.set_tiempo_restante_actual(tiempo)
    partida.set_tiempo_agotado(0)
    ids = data.get("id_cuestionarios", [])

    if isinstance(ids, str):
        ids = [item for item in ids.split(",") if item]

    for id_cuestionario in ids:
        if not is_owned("cuestionarios", "id_cuestionario", int(id_cuestionario)):
            return error_json("Solo puede crear partidas con cuestionarios propios.", 403)

    result = business.create_game(partida, [int(item) for item in ids])

    if result.get_success() and result.get_data() is not None:
        created = result.get_data()
        return json_result(
            success_result(
                result.get_message(),
                {
                    **partida_to_dict(created),
                    "cuestionarios": "",
                    "materias": "",
                    "participantes_conectados": 0,
                    "total_participantes": 0
                }
            )
        )

    return json_result(result)


@api_bp.delete("/partidas/<int:id_partida>")
def eliminar_partida(id_partida):
    if not is_owned("partidas", "id_partida", id_partida):
        return error_json("La partida no pertenece a este juez.", 403)

    result = PartidaBusiness().delete_game(id_partida)
    return json_result(
        result,
        200 if result.get_success() else 409
    )


@api_bp.post("/imagenes")
def subir_imagen():
    image = request.files.get("imagen")

    if image is None or image.filename == "":
        return json_data({
            "success": False,
            "message": "Debe seleccionar una imagen."
        }, 400)

    safe_name = secure_filename(image.filename)
    extension = os.path.splitext(safe_name)[1].lower()

    if extension not in (".png", ".jpg", ".jpeg", ".gif", ".webp"):
        return json_data({
            "success": False,
            "message": "Formato de imagen no permitido."
        }, 400)

    owner_slug = secure_filename(current_owner()) or "global"
    upload_folder = os.path.join(
        current_app.static_folder,
        "uploads",
        owner_slug
    )
    os.makedirs(upload_folder, exist_ok=True)

    stored_name = f"{uuid4().hex}{extension}"

    route_path = f"static/uploads/{owner_slug}"
    route_business = RutaImagenBusiness()
    route = route_business.get_by_path(route_path)

    if route is None:
        route_result = None

        for attempt in range(5):
            description = f"Imagenes cargadas {owner_slug}"

            if attempt > 0:
                description = f"{description} {uuid4().hex[:8]}"

            new_route = RutaImagen()
            new_route.set_descripcion(description)
            new_route.set_ruta(route_path)
            route_result = route_business.save(new_route)

            if route_result.get_success():
                route = new_route
                break

            route = route_business.get_by_path(route_path)

            if route is not None:
                break

        if route is None:
            return error_json(
                (
                    route_result.get_message()
                    if route_result is not None
                    else "No fue posible registrar la ruta de imagen."
                ),
                500
            )

    if route is None:
        return error_json(
            "La imagen se cargo, pero no fue posible registrar su ruta.",
            500
        )

    image.save(os.path.join(upload_folder, stored_name))

    return json_data({
        "success": True,
        "message": "Imagen cargada correctamente.",
        "data": {
            "id_ruta_imagen": route.get_id_ruta() if route else None,
            "nombre_imagen": stored_name,
            "url": f"/static/uploads/{owner_slug}/{stored_name}"
        }
    })


@api_bp.get("/partidas/<int:id_partida>/estado")
def estado_partida(id_partida):
    business = PartidaBusiness()
    partida = business.get_by_id(id_partida)
    pregunta = game_question_to_dict(
        business.get_current_question(id_partida),
        include_answer=session.get("judge_authenticated") is True
    )
    solicitudes = current_question_requests(
        serialize_any(business.get_word_requests(id_partida)),
        pregunta
    )

    return json_data({
        "partida": partida_to_dict(partida),
        "participantes": serialize_any(business.get_waiting_room_status(id_partida)),
        "pregunta": pregunta,
        "solicitudes": solicitudes,
        "ranking": serialize_any(business.get_live_ranking(partida.get_codigo_partida()) if partida else None),
        "timer": serialize_any(business.get_timer_status(id_partida))
    })
