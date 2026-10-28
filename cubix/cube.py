"""Rubik's cube model: six face matrices and the permutations that quarter turns apply to them.

Every turn is described as a list of (source cell -> destination cell) transfers. The same
list updates the matrices and tells the UI which cells swap places, so there is one source
of truth for "how a step changes the matrices".
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum, IntEnum

MIN_SIZE = 2
MAX_SIZE = 8
MAX_WIDTH = 2
MAX_TIMES = 9


class Face(IntEnum):
    """Face ids double as the initial sticker value of each face (1..6, as in the C++ original)."""

    UP = 1
    FRONT = 2
    RIGHT = 3
    BACK = 4
    LEFT = 5
    DOWN = 6

    @property
    def key(self) -> str:
        return self.name.lower()


class Direction(Enum):
    RIGHT = "right"
    LEFT = "left"
    UP = "up"
    DOWN = "down"

    @property
    def moves_rows(self) -> bool:
        return self in (Direction.RIGHT, Direction.LEFT)

    @property
    def is_forward(self) -> bool:
        return self in (Direction.RIGHT, Direction.UP)

    @property
    def opposite(self) -> Direction:
        return _OPPOSITE[self]


_OPPOSITE = {
    Direction.RIGHT: Direction.LEFT,
    Direction.LEFT: Direction.RIGHT,
    Direction.UP: Direction.DOWN,
    Direction.DOWN: Direction.UP,
}

Cell = tuple[Face, int, int]
Transfer = tuple[Cell, Cell]
Faces = dict[Face, list[list[int]]]


@dataclass(frozen=True)
class Move:
    """One or two adjacent layers turned `times` quarter turns in one direction."""

    direction: Direction
    layer: int
    width: int = 1
    times: int = 1

    @property
    def layers(self) -> tuple[int, ...]:
        return tuple(range(self.layer, self.layer + self.width))

    def inverse(self) -> Move:
        return replace(self, direction=self.direction.opposite)

    def validate(self, size: int) -> None:
        if not 1 <= self.width <= MAX_WIDTH:
            raise ValueError(f"width must be between 1 and {MAX_WIDTH}")
        if not 1 <= self.times <= MAX_TIMES:
            raise ValueError(f"times must be between 1 and {MAX_TIMES}")
        if self.layer < 0 or self.layer + self.width > size:
            raise ValueError(f"layers {self.layer + 1}..{self.layer + self.width} are outside a {size}x{size} cube")


@dataclass(frozen=True)
class Step:
    """Moves performed together. The UI and the exports count a whole step as one."""

    moves: tuple[Move, ...]

    def __post_init__(self) -> None:
        if not self.moves:
            raise ValueError("a step needs at least one move")

    def inverse(self) -> Step:
        return Step(tuple(move.inverse() for move in reversed(self.moves)))

    def validate(self, size: int) -> None:
        for move in self.moves:
            move.validate(size)


def quarter_turn_transfers(size: int, direction: Direction, layers: tuple[int, ...]) -> list[Transfer]:
    transfers: list[Transfer] = []
    for layer in layers:
        transfers += _ring_transfers(size, direction, layer)
        spinning_face = outer_face_turn(size, direction, layer)
        if spinning_face:
            face, clockwise = spinning_face
            transfers += _face_rotation_transfers(size, face, clockwise)
    return transfers


def outer_face_turn(size: int, direction: Direction, layer: int) -> tuple[Face, bool] | None:
    """The face that spins together with an outer layer, and whether it spins clockwise seen from outside."""
    if direction.moves_rows:
        face = Face.UP if layer == 0 else Face.DOWN if layer == size - 1 else None
        return (face, (face is Face.DOWN) == (direction is Direction.RIGHT)) if face else None
    face = Face.LEFT if layer == 0 else Face.RIGHT if layer == size - 1 else None
    return (face, (face is Face.RIGHT) == (direction is Direction.UP)) if face else None


def _ring_transfers(size: int, direction: Direction, layer: int) -> list[Transfer]:
    forward = _row_ring(size, layer) if direction.moves_rows else _column_ring(size, layer)
    return forward if direction.is_forward else [(dst, src) for src, dst in forward]


def _row_ring(size: int, row: int) -> list[Transfer]:
    """Turning a row to the right: Front -> Right -> Back -> Left -> Front."""
    ring = (Face.FRONT, Face.RIGHT, Face.BACK, Face.LEFT)
    return [
        ((face, row, col), (ring[(i + 1) % 4], row, col))
        for i, face in enumerate(ring)
        for col in range(size)
    ]


def _column_ring(size: int, col: int) -> list[Transfer]:
    """Turning a column up: Front -> Up -> Back -> Down -> Front (Back is seen from behind, hence mirrored)."""
    last = size - 1
    transfers: list[Transfer] = []
    for i in range(size):
        transfers += [
            ((Face.FRONT, i, col), (Face.UP, i, col)),
            ((Face.UP, i, col), (Face.BACK, last - i, last - col)),
            ((Face.BACK, last - i, last - col), (Face.DOWN, i, col)),
            ((Face.DOWN, i, col), (Face.FRONT, i, col)),
        ]
    return transfers


def _face_rotation_transfers(size: int, face: Face, clockwise: bool) -> list[Transfer]:
    last = size - 1
    return [
        ((face, a, b), (face, b, last - a) if clockwise else (face, last - b, a))
        for a in range(size)
        for b in range(size)
    ]


class Cube:
    def __init__(self, size: int) -> None:
        if not MIN_SIZE <= size <= MAX_SIZE:
            raise ValueError(f"size must be between {MIN_SIZE} and {MAX_SIZE}")
        self.size = size
        self.faces: Faces = solved_faces(size)

    def apply_quarter_turn(self, direction: Direction, layers: tuple[int, ...]) -> list[Transfer]:
        transfers = quarter_turn_transfers(self.size, direction, layers)
        before = copy_faces(self.faces)
        for (src_face, src_row, src_col), (dst_face, dst_row, dst_col) in transfers:
            self.faces[dst_face][dst_row][dst_col] = before[src_face][src_row][src_col]
        return transfers

    def is_solved(self) -> bool:
        return all(len({value for row in matrix for value in row}) == 1 for matrix in self.faces.values())


def solved_faces(size: int) -> Faces:
    return {face: [[face.value] * size for _ in range(size)] for face in Face}


def copy_faces(faces: Faces) -> Faces:
    return {face: [row[:] for row in matrix] for face, matrix in faces.items()}
