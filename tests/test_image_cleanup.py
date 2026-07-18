import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from data_representation.ruta_imagen import RutaImagen
from helpers.image_cleanup import (
    cleanup_replaced_image,
    remove_image_if_unreferenced,
    resolve_upload_file,
)


class FakeRouteBusiness:

    def __init__(self, route, counts=(0, 0)):
        self.route = route
        self.counts = counts
        self.usage_calls = []

    def get_attachment_usage_counts(self, id_ruta, image_name):
        self.usage_calls.append((id_ruta, image_name))
        return self.counts

    def get_by_id(self, id_ruta):
        return self.route


class ImageCleanupTests(unittest.TestCase):

    def setUp(self):
        self.static_folder = Path.cwd() / "static"

    def make_route(self, route_path="static/uploads"):
        route = RutaImagen()
        route.set_id_ruta(7)
        route.set_ruta(route_path)
        return route

    def test_shared_file_is_preserved(self):
        business = FakeRouteBusiness(self.make_route(), counts=(1, 1))

        with patch("pathlib.Path.unlink") as unlink:
            removed = remove_image_if_unreferenced(
                self.static_folder,
                7,
                "shared.png",
                business
            )

        self.assertFalse(removed)
        unlink.assert_not_called()
        self.assertEqual(business.usage_calls, [(7, "shared.png")])

    def test_orphan_file_can_be_removed(self):
        business = FakeRouteBusiness(self.make_route())

        with patch("pathlib.Path.unlink") as unlink:
            removed = remove_image_if_unreferenced(
                self.static_folder,
                7,
                "orphan.png",
                business
            )

        self.assertTrue(removed)
        unlink.assert_called_once_with(missing_ok=True)

    def test_database_reference_check_failure_preserves_file(self):
        business = FakeRouteBusiness(self.make_route(), counts=(None, None))

        with (
                patch("pathlib.Path.unlink") as unlink,
                self.assertLogs("helpers.image_cleanup", level="WARNING")
        ):
            removed = remove_image_if_unreferenced(
                self.static_folder,
                7,
                "kept.png",
                business
            )

        self.assertFalse(removed)
        unlink.assert_not_called()

    def test_manipulated_file_name_cannot_escape_uploads(self):
        business = FakeRouteBusiness(self.make_route())

        with (
                patch("pathlib.Path.unlink") as unlink,
                self.assertLogs("helpers.image_cleanup", level="WARNING")
        ):
            removed = remove_image_if_unreferenced(
                self.static_folder,
                7,
                "../../outside.png",
                business
            )

        self.assertFalse(removed)
        unlink.assert_not_called()

    def test_manipulated_route_cannot_escape_uploads(self):
        business = FakeRouteBusiness(
            self.make_route("static/uploads/../../")
        )

        with (
                patch("pathlib.Path.unlink") as unlink,
                self.assertLogs("helpers.image_cleanup", level="WARNING")
        ):
            removed = remove_image_if_unreferenced(
                self.static_folder,
                7,
                "outside.png",
                business
            )

        self.assertFalse(removed)
        unlink.assert_not_called()

    def test_resolver_accepts_only_files_inside_uploads(self):
        expected = self.static_folder / "uploads" / "judge" / "image.png"

        resolved = resolve_upload_file(
            self.static_folder,
            "static/uploads/judge",
            "image.png"
        )

        self.assertEqual(resolved, expected.resolve())


class ReplacedImageCleanupTests(unittest.TestCase):

    def test_failed_update_never_starts_physical_cleanup(self):
        remover = Mock()

        removed = cleanup_replaced_image(
            "static",
            False,
            7,
            "kept.png",
            None,
            "",
            remover
        )

        self.assertFalse(removed)
        remover.assert_not_called()

    def test_unchanged_association_does_not_start_cleanup(self):
        remover = Mock()

        removed = cleanup_replaced_image(
            "static",
            True,
            7,
            "kept.png",
            7,
            "kept.png",
            remover
        )

        self.assertFalse(removed)
        remover.assert_not_called()

    def test_cleanup_error_does_not_break_successful_update(self):
        remover = Mock(side_effect=OSError("disk unavailable"))

        with self.assertLogs("helpers.image_cleanup", level="ERROR"):
            removed = cleanup_replaced_image(
                "static",
                True,
                7,
                "old.png",
                None,
                "",
                remover
            )

        self.assertFalse(removed)
        remover.assert_called_once_with("static", 7, "old.png")


if __name__ == "__main__":
    unittest.main()
