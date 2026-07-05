import os
import sys

from PIL import Image
from PIL import ImageDraw

if __package__ in (None, ""):
    sys.path.insert(
        0,
        os.path.dirname(
            os.path.dirname(
                os.path.abspath(__file__)
            )
        )
    )

import helper.super_global as sg
import helper.styles as styles


ICON_SIZE = styles.BUTTON_ICON_SOURCE_SIZE
WHITE = styles.BUTTON_ICON_WHITE_RGBA
TRANSPARENT = styles.BUTTON_ICON_TRANSPARENT_RGBA


def _new_icon():
    return Image.new(
        "RGBA",
        (ICON_SIZE, ICON_SIZE),
        TRANSPARENT
    )


def _save(image, file_name):
    image.save(
        os.path.join(
            sg.ICON_PATH,
            file_name
        )
    )


def _draw_play(draw):
    draw.polygon(
        [(8, 5), (8, 19), (19, 12)],
        fill=WHITE
    )


def create_info_icon():

    image = _new_icon()
    draw = ImageDraw.Draw(image)
    draw.ellipse(
        (3, 3, 21, 21),
        outline=WHITE,
        width=2
    )
    draw.ellipse(
        (11, 6, 13, 8),
        fill=WHITE
    )
    draw.rounded_rectangle(
        (11, 10, 13, 18),
        radius=1,
        fill=WHITE
    )
    _save(
        image,
        "info.png"
    )
    return image


def create_icons():
    os.makedirs(
        sg.ICON_PATH,
        exist_ok=True
    )

    icons = {}

    image = _new_icon()
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle(
        (4, 6, 20, 18),
        radius=3,
        outline=WHITE,
        width=2
    )
    draw.line((8, 12, 16, 12), fill=WHITE, width=2)
    draw.line((12, 8, 12, 16), fill=WHITE, width=2)
    icons["generate_code.png"] = image

    image = _new_icon()
    draw = ImageDraw.Draw(image)
    draw.rectangle((5, 6, 19, 18), outline=WHITE, width=2)
    draw.line((8, 10, 16, 10), fill=WHITE, width=2)
    draw.line((8, 14, 13, 14), fill=WHITE, width=2)
    draw.ellipse((15, 13, 21, 19), outline=WHITE, width=2)
    icons["generate_game.png"] = image

    image = _new_icon()
    draw = ImageDraw.Draw(image)
    draw.rectangle((4, 7, 18, 19), outline=WHITE, width=2)
    draw.polygon([(10, 10), (10, 16), (16, 13)], fill=WHITE)
    icons["open_game.png"] = image

    image = _new_icon()
    draw = ImageDraw.Draw(image)
    draw.line((5, 8, 17, 8), fill=WHITE, width=2)
    draw.polygon([(17, 5), (21, 8), (17, 11)], fill=WHITE)
    draw.line((19, 16, 7, 16), fill=WHITE, width=2)
    draw.polygon([(7, 13), (3, 16), (7, 19)], fill=WHITE)
    icons["change_status.png"] = image

    image = _new_icon()
    draw = ImageDraw.Draw(image)
    draw.ellipse(
        (6, 6, 18, 18),
        outline=WHITE,
        width=3
    )
    draw.ellipse(
        (10, 10, 14, 14),
        fill=WHITE
    )

    for x1, y1, x2, y2 in (
            (11, 2, 13, 7),
            (11, 17, 13, 22),
            (2, 11, 7, 13),
            (17, 11, 22, 13),
            (5, 5, 8, 8),
            (16, 16, 19, 19),
            (16, 5, 19, 8),
            (5, 16, 8, 19)
    ):
        draw.rectangle(
            (x1, y1, x2, y2),
            fill=WHITE
        )

    icons["settings.png"] = image

    image = _new_icon()
    draw = ImageDraw.Draw(image)
    draw.line((7, 7, 17, 17), fill=WHITE, width=3)
    draw.line((17, 7, 7, 17), fill=WHITE, width=3)
    icons["cancel.png"] = image

    image = _new_icon()
    draw = ImageDraw.Draw(image)
    _draw_play(draw)
    icons["start.png"] = image

    image = _new_icon()
    draw = ImageDraw.Draw(image)
    draw.rectangle((7, 6, 10, 18), fill=WHITE)
    draw.rectangle((14, 6, 17, 18), fill=WHITE)
    icons["pause.png"] = image

    image = _new_icon()
    draw = ImageDraw.Draw(image)
    _draw_play(draw)
    icons["resume.png"] = image

    image = _new_icon()
    draw = ImageDraw.Draw(image)
    draw.polygon([(5, 6), (5, 18), (14, 12)], fill=WHITE)
    draw.rectangle((16, 6, 19, 18), fill=WHITE)
    icons["next.png"] = image

    image = _new_icon()
    draw = ImageDraw.Draw(image)
    draw.line((7, 4, 7, 20), fill=WHITE, width=2)
    draw.polygon(
        [
            (8, 5),
            (18, 7),
            (18, 14),
            (8, 12)
        ],
        fill=WHITE
    )
    draw.line((5, 20, 16, 20), fill=WHITE, width=2)
    icons["finish.png"] = image

    image = _new_icon()
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((8, 3, 16, 14), radius=4, outline=WHITE, width=2)
    draw.arc((5, 10, 19, 20), 20, 160, fill=WHITE, width=2)
    draw.line((12, 18, 12, 21), fill=WHITE, width=2)
    draw.line((9, 21, 15, 21), fill=WHITE, width=2)
    icons["give_word.png"] = image

    image = _new_icon()
    draw = ImageDraw.Draw(image)
    draw.line((5, 13, 10, 18), fill=WHITE, width=3)
    draw.line((10, 18, 20, 6), fill=WHITE, width=3)
    icons["correct.png"] = image

    image = _new_icon()
    draw = ImageDraw.Draw(image)
    draw.line((7, 7, 17, 17), fill=WHITE, width=3)
    draw.line((17, 7, 7, 17), fill=WHITE, width=3)
    icons["incorrect.png"] = image

    image = _new_icon()
    draw = ImageDraw.Draw(image)
    draw.ellipse((5, 5, 19, 17), outline=WHITE, width=2)
    draw.polygon([(9, 16), (7, 21), (14, 17)], fill=WHITE)
    icons["requests.png"] = image

    image = _new_icon()
    draw = ImageDraw.Draw(image)
    draw.line((4, 20, 21, 20), fill=WHITE, width=2)
    draw.rectangle((5, 12, 8, 19), fill=WHITE)
    draw.rectangle((10, 8, 14, 19), fill=WHITE)
    draw.rectangle((16, 4, 20, 19), fill=WHITE)
    icons["statistics.png"] = image

    image = _new_icon()
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle(
        (6, 6, 18, 18),
        radius=2,
        fill=WHITE
    )
    icons["stop.png"] = image

    image = _new_icon()
    draw = ImageDraw.Draw(image)

    for points in (
            ((3, 9), (3, 3), (9, 3)),
            ((15, 3), (21, 3), (21, 9)),
            ((3, 15), (3, 21), (9, 21)),
            ((15, 21), (21, 21), (21, 15))
    ):
        draw.line(
            points,
            fill=WHITE,
            width=2,
            joint="curve"
        )

    icons["fullscreen.png"] = image

    for file_name, image in icons.items():
        _save(
            image,
            file_name
        )

    create_info_icon()


if __name__ == "__main__":
    create_icons()
