"""A cube plus its history of steps: applying, scrambling and auto-resolving."""
from __future__ import annotations

import random
from dataclasses import dataclass
from enum import Enum

from .cube import (
    MAX_TIMES,
    Cube,
    Direction,
    Face,
    Faces,
    Move,
    Step,
    Transfer,
    copy_faces,
    outer_face_turn,
    solved_faces,
)

MAX_SCRAMBLE_STEPS = 50
DEFAULT_SCRAMBLE_STEPS = 10
DOUBLE_LAYER_CHANCE = 0.25
MAX_SCRAMBLE_TURNS = 3

FACE_NAMES = {
    Face.UP: "Sus", Face.FRONT: "Față", Face.RIGHT: "Dreapta",
    Face.BACK: "Spate", Face.LEFT: "Stânga", Face.DOWN: "Jos",
}
DIRECTION_NAMES = {
    Direction.RIGHT: "dreapta", Direction.LEFT: "stânga", Direction.UP: "sus", Direction.DOWN: "jos",
}
RING_ORDER = {
    Direction.RIGHT: (Face.FRONT, Face.RIGHT, Face.BACK, Face.LEFT),
    Direction.LEFT: (Face.FRONT, Face.LEFT, Face.BACK, Face.RIGHT),
    Direction.UP: (Face.FRONT, Face.UP, Face.BACK, Face.DOWN),
    Direction.DOWN: (Face.FRONT, Face.DOWN, Face.BACK, Face.UP),
}


class Origin(str, Enum):
    MANUAL = "manual"
    SCRAMBLE = "scramble"
    SOLVE = "solve"


@dataclass(frozen=True)
class TurnFrame:
    """One quarter turn inside a step, with the matrices as they are right after it."""

    direction: Direction
    layers: tuple[int, ...]
    transfers: list[Transfer]
    faces: Faces
    description: str


@dataclass(frozen=True)
class StepRecord:
    number: int
    step: Step
    origin: Origin
    faces: Faces


@dataclass(frozen=True)
class StepResult:
    record: StepRecord
    frames: list[TurnFrame]


def describe_turn(size: int, direction: Direction, layers: tuple[int, ...]) -> str:
    axis = "Rând" if direction.moves_rows else "Coloană"
    layer_text = str(layers[0] + 1) if len(layers) == 1 else f"{layers[0] + 1}–{layers[-1] + 1}"
    ring = RING_ORDER[direction]
    cycle = " → ".join(FACE_NAMES[face] for face in (*ring, ring[0]))
    parts = [f"{axis} {layer_text} → {DIRECTION_NAMES[direction]}: {cycle}"]
    for layer in layers:
        spin = outer_face_turn(size, direction, layer)
        if spin:
            face, clockwise = spin
            parts.append(f"Fața {FACE_NAMES[face]} se rotește {'↻' if clockwise else '↺'}")
    return " · ".join(parts)


class Session:
    def __init__(self, size: int = 3, rng: random.Random | None = None) -> None:
        self.rng = rng or random.Random()
        self.reset(size)

    def reset(self, size: int) -> None:
        self.cube = Cube(size)
        self.initial_faces = solved_faces(size)
        self.history: list[StepRecord] = []
        self._undo_stack: list[Step] = []

    @property
    def size(self) -> int:
        return self.cube.size

    def apply_step(self, step: Step, origin: Origin = Origin.MANUAL) -> StepResult:
        step.validate(self.size)  # validate everything first so a bad step changes nothing
        frames = [
            self._turn(move.direction, move.layers)
            for move in step.moves
            for _ in range(move.times)
        ]
        record = StepRecord(len(self.history) + 1, step, origin, copy_faces(self.cube.faces))
        self.history.append(record)
        self._remember_for_undo(step, origin)
        return StepResult(record, frames)

    def scramble(self, step_count: int = DEFAULT_SCRAMBLE_STEPS) -> list[StepResult]:
        if not 1 <= step_count <= MAX_SCRAMBLE_STEPS:
            raise ValueError(f"step count must be between 1 and {MAX_SCRAMBLE_STEPS}")
        return [self.apply_step(self._random_step(), Origin.SCRAMBLE) for _ in range(step_count)]

    def solve(self) -> list[StepResult]:
        """Undo the recorded steps newest first; each undone step is again one step."""
        inverses = [step.inverse() for step in reversed(self._undo_stack)]
        return [self.apply_step(inverse, Origin.SOLVE) for inverse in inverses]

    def _turn(self, direction: Direction, layers: tuple[int, ...]) -> TurnFrame:
        transfers = self.cube.apply_quarter_turn(direction, layers)
        description = describe_turn(self.size, direction, layers)
        return TurnFrame(direction, layers, transfers, copy_faces(self.cube.faces), description)

    def _remember_for_undo(self, step: Step, origin: Origin) -> None:
        if origin is not Origin.SOLVE:
            self._undo_stack.append(step)
        if self.cube.is_solved():
            self._undo_stack.clear()

    def _random_step(self) -> Step:
        move_count = self.rng.choice((1, 1, 2))
        return Step(tuple(self._random_move() for _ in range(move_count)))

    def _random_move(self) -> Move:
        wide = self.size >= 3 and self.rng.random() < DOUBLE_LAYER_CHANCE
        width = 2 if wide else 1
        return Move(
            direction=self.rng.choice(list(Direction)),
            layer=self.rng.randrange(self.size - width + 1),
            width=width,
            times=self.rng.randint(1, min(MAX_SCRAMBLE_TURNS, MAX_TIMES)),
        )
