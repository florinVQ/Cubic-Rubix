"""The matrix engine is checked against an independent physical model: stickers rotated in 3D."""
import itertools
import random

import pytest

from cubix.cube import Cube, Direction, Face, Move, Step
from cubix.geometry import FACE_NORMALS, sticker_position
from cubix.notation import format_step, parse_step

Vector = tuple[int, int, int]


def rotate_about_y(vector: Vector, sign: int) -> Vector:
    x, y, z = vector  # CSS rotateY(+90): the front goes to the right
    return (sign * z, y, -sign * x)


def rotate_about_x(vector: Vector, sign: int) -> Vector:
    x, y, z = vector  # CSS rotateX(+90): the front goes up
    return (x, -sign * z, sign * y)


def centered(position: Vector, size: int) -> Vector:
    return tuple(2 * value - (size - 1) for value in position)


class PhysicalCube:
    """Sticker colour keyed by (doubled centred position, outward normal)."""

    def __init__(self, size: int) -> None:
        self.size = size
        self.stickers = {
            (centered(sticker_position(face, row, col, size), size), FACE_NORMALS[face]): face.value
            for face in Face
            for row in range(size)
            for col in range(size)
        }

    def turn(self, direction: Direction, layers: tuple[int, ...]) -> None:
        rotate = rotate_about_y if direction.moves_rows else rotate_about_x
        sign = 1 if direction.is_forward else -1
        axis_index = 1 if direction.moves_rows else 0
        selected = {2 * layer - (self.size - 1) for layer in layers}
        self.stickers = {
            (rotate(position, sign), rotate(normal, sign)) if position[axis_index] in selected else (position, normal): color
            for (position, normal), color in self.stickers.items()
        }

    def as_matrices(self) -> dict[Face, list[list[int]]]:
        return {
            face: [
                [
                    self.stickers[(centered(sticker_position(face, row, col, self.size), self.size), FACE_NORMALS[face])]
                    for col in range(self.size)
                ]
                for row in range(self.size)
            ]
            for face in Face
        }


ALL_TURNS = list(itertools.product(Direction, [1, 2]))


@pytest.mark.parametrize("size", [2, 3, 4, 5])
def test_every_single_turn_matches_physical_model(size):
    for direction, width in ALL_TURNS:
        for layer in range(size - width + 1):
            cube, physical = Cube(size), PhysicalCube(size)
            layers = tuple(range(layer, layer + width))
            cube.apply_quarter_turn(direction, layers)
            physical.turn(direction, layers)
            assert cube.faces == physical.as_matrices(), (direction, layers)


@pytest.mark.parametrize("size", [3, 6, 8])
def test_random_sequences_match_physical_model(size):
    rng = random.Random(size)
    cube, physical = Cube(size), PhysicalCube(size)
    for _ in range(60):
        direction, width = rng.choice(ALL_TURNS)
        layers = tuple(range(rng_layer := rng.randrange(size - width + 1), rng_layer + width))
        cube.apply_quarter_turn(direction, layers)
        physical.turn(direction, layers)
    assert cube.faces == physical.as_matrices()


def test_four_quarter_turns_restore_the_cube():
    for direction, layer in itertools.product(Direction, range(3)):
        cube = Cube(3)
        for _ in range(4):
            cube.apply_quarter_turn(direction, (layer,))
        assert cube.is_solved()


def test_opposite_direction_undoes_a_turn():
    cube = Cube(4)
    cube.apply_quarter_turn(Direction.RIGHT, (1,))
    assert not cube.is_solved()
    cube.apply_quarter_turn(Direction.LEFT, (1,))
    assert cube.is_solved()


def test_step_inverse_restores_the_cube():
    step = parse_step("row 2 right x3 + col 1-2 up x2 + row 1 left x1")
    cube = Cube(5)
    for current in (step, step.inverse()):
        for move in current.moves:
            for _ in range(move.times):
                cube.apply_quarter_turn(move.direction, move.layers)
    assert cube.is_solved()


def test_notation_round_trip():
    text = "row 2-3 right x3 + col 1 down x2"
    assert format_step(parse_step(text)) == text
    assert parse_step("col 4 up").moves == (Move(Direction.UP, 3),)


@pytest.mark.parametrize("bad", ["row 1 up", "diag 1 right", "row right", "row 1 right x0y"])
def test_notation_rejects_nonsense(bad):
    with pytest.raises(ValueError):
        parse_step(bad)


def test_move_outside_the_cube_is_rejected():
    with pytest.raises(ValueError):
        Step((Move(Direction.RIGHT, 2, width=2),)).validate(3)
    with pytest.raises(ValueError):
        Cube(9)
