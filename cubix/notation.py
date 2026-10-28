"""Plain-text notation for steps, shared with the C++ engine.

    row 2 right x3 + col 1-2 up x2

Layers are 1-based; `1-2` means two adjacent layers; `xN` is optional (default 1);
`+` joins the moves of a single step.
"""
from __future__ import annotations

import re

from .cube import Direction, Move, Step

_MOVE_PATTERN = re.compile(r"^(row|col)\s+(\d+)(?:-(\d+))?\s+(right|left|up|down)(?:\s+x(\d+))?$")


def format_move(move: Move) -> str:
    axis = "row" if move.direction.moves_rows else "col"
    layers = str(move.layer + 1) if move.width == 1 else f"{move.layer + 1}-{move.layer + move.width}"
    return f"{axis} {layers} {move.direction.value} x{move.times}"


def format_step(step: Step) -> str:
    return " + ".join(format_move(move) for move in step.moves)


def parse_move(text: str) -> Move:
    match = _MOVE_PATTERN.match(text.strip().lower())
    if not match:
        raise ValueError(f"cannot read move: {text!r}")
    axis, first, last, direction_name, times = match.groups()
    direction = Direction(direction_name)
    if direction.moves_rows != (axis == "row"):
        raise ValueError(f"a {axis} cannot move {direction_name}: {text!r}")
    first_layer = int(first)
    width = int(last) - first_layer + 1 if last else 1
    return Move(direction, first_layer - 1, width, int(times) if times else 1)


def parse_step(text: str) -> Step:
    return Step(tuple(parse_move(part) for part in text.split("+")))
