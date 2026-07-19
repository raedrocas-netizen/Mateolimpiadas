ALLOWED_IMAGE_EXTENSIONS = (
    ".png",
    ".jpg",
    ".jpeg",
    ".jfif",
    ".webp",
    ".gif",
    ".avif",
)


_IMAGE_FAMILY_BY_EXTENSION = {
    ".png": "png",
    ".jpg": "jpeg",
    ".jpeg": "jpeg",
    ".jfif": "jpeg",
    ".webp": "webp",
    ".gif": "gif",
    ".avif": "avif",
}


def image_extension_allowed(extension):
    return str(extension or "").lower() in ALLOWED_IMAGE_EXTENSIONS


def _read_image_probe(stream):
    original_position = stream.tell()

    try:
        stream.seek(0)
        header = stream.read(4096)
        stream.seek(0, 2)
        size = stream.tell()
        stream.seek(max(0, size - 64))
        trailer = stream.read(64)
        return header, trailer, size
    finally:
        stream.seek(original_position)


def _detect_image_family(header, trailer, size):
    if (
            len(header) >= 24
            and header.startswith(b"\x89PNG\r\n\x1a\n")
            and header[12:16] == b"IHDR"
            and int.from_bytes(header[16:20], "big") > 0
            and int.from_bytes(header[20:24], "big") > 0
    ):
        return "png"

    if (
            len(header) >= 10
            and header[:6] in (b"GIF87a", b"GIF89a")
            and int.from_bytes(header[6:8], "little") > 0
            and int.from_bytes(header[8:10], "little") > 0
    ):
        return "gif"

    if (
            len(header) >= 16
            and header[:4] == b"RIFF"
            and header[8:12] == b"WEBP"
            and header[12:16] in (b"VP8 ", b"VP8L", b"VP8X")
            and int.from_bytes(header[4:8], "little") + 8 <= size
    ):
        return "webp"

    if (
            len(header) >= 4
            and header[:3] == b"\xff\xd8\xff"
            and b"\xff\xd9" in trailer
    ):
        return "jpeg"

    if len(header) >= 16 and header[4:8] == b"ftyp":
        box_size = int.from_bytes(header[:4], "big")

        if 16 <= box_size <= min(len(header), size):
            brand_data = header[8:12] + header[16:box_size]
            brands = {
                brand_data[index:index + 4]
                for index in range(0, len(brand_data) - 3, 4)
            }

            if brands.intersection((b"avif", b"avis")):
                return "avif"

    return None


def image_content_matches_extension(stream, extension):
    normalized_extension = str(extension or "").lower()
    expected_family = _IMAGE_FAMILY_BY_EXTENSION.get(normalized_extension)

    if expected_family is None:
        return False

    try:
        header, trailer, size = _read_image_probe(stream)
    except (AttributeError, OSError, ValueError):
        return False

    return _detect_image_family(header, trailer, size) == expected_family
