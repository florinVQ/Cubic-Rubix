import json
import random
import threading
import urllib.error
import urllib.request

import pytest

from cubix.cube import Direction, Move, Step
from cubix.export import render_html, render_text
from cubix.notation import parse_step
from cubix.server import CubixServer
from cubix.session import Origin, Session


def test_compound_step_counts_as_one_step_but_animates_every_quarter_turn():
    session = Session(3)
    result = session.apply_step(parse_step("row 2 right x3 + col 3 up x2"))
    assert len(session.history) == 1
    assert result.record.number == 1
    assert len(result.frames) == 5


def test_invalid_step_leaves_the_cube_untouched():
    session = Session(3)
    bad = Step((Move(Direction.RIGHT, 0), Move(Direction.UP, 5)))
    with pytest.raises(ValueError):
        session.apply_step(bad)
    assert session.cube.is_solved()
    assert session.history == []


@pytest.mark.parametrize("size", [2, 3, 5, 8])
def test_solve_undoes_a_scramble_step_by_step(size):
    session = Session(size, random.Random(size))
    scrambled = session.scramble(15)
    assert not session.cube.is_solved()
    solved = session.solve()
    assert session.cube.is_solved()
    # A scramble can pass through the solved state by chance; undo then starts from there.
    assert 0 < len(solved) <= len(scrambled)
    assert all(result.record.origin is Origin.SOLVE for result in solved)
    assert session.solve() == []


def test_frames_carry_the_matrices_after_each_quarter_turn():
    session = Session(3)
    result = session.apply_step(parse_step("row 1 right x2"))
    assert result.frames[0].faces != result.frames[1].faces
    assert result.frames[-1].faces == result.record.faces


def test_text_export_lists_every_step_with_its_number():
    session = Session(3)
    session.apply_step(parse_step("row 1 right x1"))
    session.apply_step(parse_step("col 2 up x2 + row 3 left x1"))
    text = render_text(session.size, session.initial_faces, session.history)
    assert "Starea initiala" in text
    assert "Pasul 1: row 1 right x1" in text
    assert "Pasul 2: col 2 up x2 + row 3 left x1" in text


def test_html_export_has_one_card_per_step_plus_the_initial_state():
    session = Session(3)
    session.scramble(4)
    html = render_html(session.size, session.initial_faces, session.history)
    assert html.count('class="card"') == 5


@pytest.fixture
def api():
    server = CubixServer(("127.0.0.1", 0), Session(3, random.Random(1)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_address[1]}"

    def call(path, body=None):
        request = urllib.request.Request(
            base + path, data=json.dumps(body).encode() if body is not None else None,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request) as response:
                return response.status, response.read()
        except urllib.error.HTTPError as error:
            return error.code, error.read()

    yield call
    server.shutdown()
    server.server_close()


def test_api_step_scramble_solve_and_export(api):
    status, raw = api("/api/step", {"moves": [{"direction": "right", "layer": 0, "times": 3}]})
    assert status == 200
    payload = json.loads(raw)
    assert len(payload["steps"][0]["frames"]) == 3
    assert len(payload["state"]["stickers"]) == 6 * 9

    api("/api/scramble", {"count": 5})
    status, raw = api("/api/solve", {})
    solve_steps = len(json.loads(raw)["steps"])
    assert status == 200 and 0 < solve_steps <= 6

    status, raw = api("/api/export?format=txt")
    assert status == 200 and raw.decode().count("Pasul ") == 1 + 5 + solve_steps


def test_api_rejects_bad_input_and_path_traversal(api):
    assert api("/api/step", {"moves": [{"direction": "sideways", "layer": 0}]})[0] == 400
    assert api("/api/step", {"moves": []})[0] == 400
    assert api("/api/reset", {"size": 99})[0] == 400
    assert api("/../cubix/cube.py")[0] == 404
    assert api("/")[0] == 200
