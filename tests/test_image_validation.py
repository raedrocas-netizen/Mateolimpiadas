import unittest
from io import BytesIO

from helpers.image_validation import (
    ALLOWED_IMAGE_EXTENSIONS,
    image_content_matches_extension,
    image_extension_allowed,
)


class ImageValidationTests(unittest.TestCase):

    @staticmethod
    def jpeg_bytes():
        return (
            b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00"
            b"image-data\xff\xd9"
        )

    def test_jfif_extension_accepts_jpeg_content(self):
        jpeg = BytesIO(self.jpeg_bytes())

        self.assertTrue(image_extension_allowed(".jfif"))
        self.assertTrue(image_content_matches_extension(jpeg, ".jfif"))
        self.assertEqual(jpeg.tell(), 0)

    def test_invalid_extension_remains_rejected(self):
        self.assertFalse(image_extension_allowed(".svg"))
        self.assertFalse(image_extension_allowed(".exe"))

    def test_extension_cannot_disguise_non_image_content(self):
        self.assertFalse(
            image_content_matches_extension(
                BytesIO(b"this is not a real image"),
                ".jpg"
            )
        )

    def test_content_must_match_declared_extension(self):
        self.assertFalse(
            image_content_matches_extension(
                BytesIO(self.jpeg_bytes()),
                ".png"
            )
        )

    def test_existing_formats_and_avif_remain_valid(self):
        samples = {
            ".png": (
                b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
                b"\x00\x00\x00\x01\x00\x00\x00\x01"
            ),
            ".gif": b"GIF89a\x01\x00\x01\x00",
            ".webp": b"RIFF\x08\x00\x00\x00WEBPVP8 ",
            ".avif": (
                b"\x00\x00\x00\x14ftypavif\x00\x00\x00\x00avif"
            ),
        }

        for extension, content in samples.items():
            with self.subTest(extension=extension):
                self.assertTrue(
                    image_content_matches_extension(
                        BytesIO(content),
                        extension
                    )
                )

    def test_allowed_extension_list_is_exact(self):
        self.assertEqual(
            ALLOWED_IMAGE_EXTENSIONS,
            (".png", ".jpg", ".jpeg", ".jfif", ".webp", ".gif", ".avif")
        )


if __name__ == "__main__":
    unittest.main()
