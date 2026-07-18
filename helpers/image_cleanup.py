import logging
import os
from pathlib import Path


logger = logging.getLogger(__name__)


def resolve_upload_file(static_folder, route_path, image_name):
    """Resolve one stored image without ever escaping static/uploads."""
    if not static_folder or not route_path or not image_name:
        return None

    image_name = str(image_name)
    if Path(image_name).name != image_name or image_name in (".", ".."):
        return None

    uploads_root = (Path(static_folder) / "uploads").resolve()
    stored_route = Path(str(route_path).replace("\\", "/"))

    if stored_route.is_absolute():
        candidate = stored_route / image_name
    else:
        candidate = Path(static_folder).parent / stored_route / image_name

    resolved_candidate = candidate.resolve()

    try:
        common_root = Path(os.path.commonpath((uploads_root, resolved_candidate)))
    except ValueError:
        return None

    if common_root != uploads_root or resolved_candidate == uploads_root:
        return None

    return resolved_candidate


def remove_image_if_unreferenced(
        static_folder,
        id_ruta,
        image_name,
        route_business=None
):
    """Delete an orphan image after its database association was updated."""
    if not id_ruta or not image_name:
        return False

    if route_business is None:
        from logical_business.ruta_imagen_business import RutaImagenBusiness
        route_business = RutaImagenBusiness()

    question_uses, answer_uses = route_business.get_attachment_usage_counts(
        id_ruta,
        image_name
    )

    if question_uses is None or answer_uses is None:
        logger.warning(
            "No se eliminó la imagen porque no se pudieron comprobar sus referencias."
        )
        return False

    if question_uses or answer_uses:
        return False

    route = route_business.get_by_id(id_ruta)
    if route is None:
        logger.warning(
            "No se eliminó la imagen huérfana: ruta %s inexistente.",
            id_ruta
        )
        return False

    image_path = resolve_upload_file(
        static_folder,
        route.get_ruta(),
        image_name
    )
    if image_path is None:
        logger.warning(
            "Se rechazó una ruta de imagen insegura: ruta=%s, archivo=%s.",
            route.get_ruta(),
            image_name
        )
        return False

    try:
        image_path.unlink(missing_ok=True)
        return True
    except OSError:
        logger.exception(
            "No fue posible eliminar la imagen huérfana %s.",
            image_path
        )
        return False


def cleanup_replaced_image(
        static_folder,
        update_succeeded,
        old_route_id,
        old_image_name,
        new_route_id,
        new_image_name,
        remover=remove_image_if_unreferenced
):
    """Run orphan cleanup only after a successful association update."""
    if not update_succeeded:
        return False

    if (old_route_id, old_image_name) == (new_route_id, new_image_name):
        return False

    try:
        return remover(
            static_folder,
            old_route_id,
            old_image_name
        )
    except Exception:
        logger.exception(
            "Falló la limpieza de una imagen reemplazada; la actualización se conserva."
        )
        return False
