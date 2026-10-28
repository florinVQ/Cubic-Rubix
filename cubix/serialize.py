"""Conversions between the session objects and the JSON the web UI speaks."""
from __future__ import annotations

from typing import Any

from .cube import Direction, Faces, Move, Step
from .geometry import all_stickers
from .notation import format_step
from .session import Session, StepRecord, StepResult, TurnFrame


def faces_to_json(faces: Faces) -> dict[str, list[list[int]]]:
    return {face.key: matrix for face, matrix in faces.items()}


def move_to_json(move: Move) -> dict[str, Any]:
    return {"direction": move.direction.value, "layer": move.layer, "width": move.width, "times": move.times}


def move_from_json(data: dict[str, Any]) -> Move:
    try:
        return Move(Direction(data["direction"]), int(data["layer"]), int(data.get("width", 1)), int(data.get("times", 1)))
    except (KeyError, ValueError, TypeError) as error:
        raise ValueError(f"invalid move: {data!r}") from error


def step_from_json(moves: list[dict[str, Any]]) -> Step:
    if not isinstance(moves, list):
        raise ValueError("moves must be a list")
    return Step(tuple(move_from_json(item) for item in moves))


def record_to_json(record: StepRecord) -> dict[str, Any]:
    return {
        "number": record.number,
        "label": format_step(record.step),
        "origin": record.origin.value,
        "moves": [move_to_json(move) for move in record.step.moves],
    }


def frame_to_json(frame: TurnFrame) -> dict[str, Any]:
    return {
        "direction": frame.direction.value,
        "layers": list(frame.layers),
        "transfers": [[[src[0].key, *src[1:]], [dst[0].key, *dst[1:]]] for src, dst in frame.transfers],
        "faces": faces_to_json(frame.faces),
        "description": frame.description,
    }


def result_to_json(result: StepResult) -> dict[str, Any]:
    return {"record": record_to_json(result.record), "frames": [frame_to_json(frame) for frame in result.frames]}


def state_to_json(session: Session) -> dict[str, Any]:
    return {
        "size": session.size,
        "faces": faces_to_json(session.cube.faces),
        "stickers": all_stickers(session.size),
        "history": [record_to_json(record) for record in session.history],
    }


def action_to_json(session: Session, results: list[StepResult]) -> dict[str, Any]:
    return {"steps": [result_to_json(result) for result in results], "state": state_to_json(session)}
