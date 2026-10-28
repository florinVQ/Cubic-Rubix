"""Where each matrix cell physically sits on the cube.

Cubie coordinates: x grows to the right, y downwards, z towards the viewer (front is z = size - 1).
The matrices are the faces as seen from outside the cube; Back is seen from behind.
"""
from __future__ import annotations

from .cube import Face

FACE_NORMALS: dict[Face, tuple[int, int, int]] = {
    Face.UP: (0, -1, 0),
    Face.DOWN: (0, 1, 0),
    Face.FRONT: (0, 0, 1),
    Face.BACK: (0, 0, -1),
    Face.RIGHT: (1, 0, 0),
    Face.LEFT: (-1, 0, 0),
}


def sticker_position(face: Face, row: int, col: int, size: int) -> tuple[int, int, int]:
    last = size - 1
    return {
        Face.FRONT: (col, row, last),
        Face.BACK: (last - col, row, 0),
        Face.RIGHT: (last, row, last - col),
        Face.LEFT: (0, row, col),
        Face.UP: (col, 0, row),
        Face.DOWN: (col, last, last - row),
    }[face]


def all_stickers(size: int) -> list[dict]:
    return [
        {"face": face.key, "row": row, "col": col, **dict(zip("xyz", sticker_position(face, row, col, size)))}
        for face in Face
        for row in range(size)
        for col in range(size)
    ]
