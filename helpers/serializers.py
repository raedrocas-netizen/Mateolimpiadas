from helpers.performance import measure_serialization


def image_path_to_url(path):
    if not path:
        return ""

    normalized = str(path).replace("\\", "/")

    static_marker = "/static/"

    if static_marker in normalized:
        return normalized[normalized.index(static_marker):]

    if normalized.startswith("/static/"):
        return normalized

    if normalized.startswith("static/"):
        return f"/{normalized}"

    return normalized


def stored_image_to_url(route_path, image_name):
    if not route_path or not image_name:
        return ""

    return image_path_to_url(
        f"{str(route_path).rstrip('/')}/{image_name}"
    )


def game_question_to_dict(question, include_answer=False):
    with measure_serialization():
        if question is None:
            return None

        payload = dict(question)
        payload["imagen"] = stored_image_to_url(
            payload.get("ruta_pregunta"),
            payload.get("nombre_imagen_pregunta")
        )

        if include_answer:
            payload["imagen_respuesta"] = stored_image_to_url(
                payload.get("ruta_respuesta"),
                payload.get("nombre_imagen_respuesta")
            )
            return payload

        for key in (
                "respuesta_correcta",
                "nombre_imagen_respuesta",
                "ruta_respuesta",
                "descripcion_ruta_respuesta"
        ):
            payload.pop(key, None)

        return payload


def business_result_to_dict(result):
    with measure_serialization():
        return {
            "success": result.get_success(),
            "message": result.get_message(),
            "data": serialize_any(result.get_data())
        }


def materia_to_dict(materia):
    if materia is None or not hasattr(materia, "get_id_materia"):
        return None

    return {
        "id_materia": materia.get_id_materia(),
        "nombre": materia.get_nombre()
    }


def cuestionario_to_dict(cuestionario):
    if cuestionario is None or not hasattr(cuestionario, "get_id_cuestionario"):
        return None

    return {
        "id_cuestionario": cuestionario.get_id_cuestionario(),
        "nombre": cuestionario.get_nombre(),
        "materia": materia_to_dict(cuestionario.get_materia()),
        "area": cuestionario.get_area(),
        "estado": cuestionario.get_estado(),
        "fecha_creacion": cuestionario.get_fecha_creacion()
    }


def ruta_imagen_to_dict(ruta):
    if ruta is None or not hasattr(ruta, "get_id_ruta"):
        return None

    return {
        "id_ruta": ruta.get_id_ruta(),
        "descripcion": ruta.get_descripcion(),
        "ruta": ruta.get_ruta()
    }


def pregunta_to_dict(pregunta):
    if pregunta is None or not hasattr(pregunta, "get_id_pregunta"):
        return None

    return {
        "id_pregunta": pregunta.get_id_pregunta(),
        "cuestionario": cuestionario_to_dict(pregunta.get_cuestionario()),
        "enunciado": pregunta.get_enunciado(),
        "ruta_imagen": ruta_imagen_to_dict(pregunta.get_ruta_imagen()),
        "nombre_imagen": pregunta.get_nombre_imagen(),
        "imagen": image_path_to_url(pregunta.get_full_image_path())
    }


def respuesta_to_dict(respuesta):
    if respuesta is None or not hasattr(respuesta, "get_id_respuesta"):
        return None

    return {
        "id_respuesta": respuesta.get_id_respuesta(),
        "pregunta": pregunta_to_dict(respuesta.get_pregunta()),
        "descripcion": respuesta.get_descripcion(),
        "ruta_imagen": ruta_imagen_to_dict(respuesta.get_ruta_imagen()),
        "nombre_imagen": respuesta.get_nombre_imagen(),
        "imagen": image_path_to_url(respuesta.get_full_image_path())
    }


def partida_to_dict(partida):
    if partida is None or not hasattr(partida, "get_id_partida"):
        return None

    return {
        "id_partida": partida.get_id_partida(),
        "codigo_partida": partida.get_codigo_partida(),
        "nombre": partida.get_nombre(),
        "area": partida.get_area(),
        "tiempo_por_pregunta": partida.get_tiempo_por_pregunta(),
        "puntos_correcta": partida.get_puntos_correcta(),
        "penalizacion_incorrecta": partida.get_penalizacion_incorrecta(),
        "estado": partida.get_estado(),
        "pregunta_actual": partida.get_pregunta_actual(),
        "fecha_creacion": partida.get_fecha_creacion(),
        "tiempo_restante_actual": partida.get_tiempo_restante_actual(),
        "tiempo_agotado": partida.get_tiempo_agotado()
    }


def serialize_any(value):
    with measure_serialization():
        if isinstance(value, list):
            return [serialize_any(item) for item in value]

        if isinstance(value, tuple):
            return [serialize_any(item) for item in value]

        if isinstance(value, dict):
            return {
                key: serialize_any(item)
                for key, item in value.items()
            }

        for converter in (
                materia_to_dict,
                cuestionario_to_dict,
                pregunta_to_dict,
                respuesta_to_dict,
                partida_to_dict,
                ruta_imagen_to_dict
        ):
            converted = converter(value)
            if converted is not None:
                return converted

        return value
