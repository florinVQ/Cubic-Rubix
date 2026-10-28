"""The C++ engine and the Python engine must print exactly the same unfolded cubes."""
import random
import shutil
import subprocess
from pathlib import Path

import pytest

from cubix.export import render_text
from cubix.notation import format_step, parse_step
from cubix.session import Session

CPP_SOURCE = Path(__file__).resolve().parent.parent / "cpp" / "rubik_engine.cpp"

pytestmark = pytest.mark.skipif(shutil.which("g++") is None, reason="g++ is not installed")


@pytest.fixture(scope="module")
def engine(tmp_path_factory):
    binary = tmp_path_factory.mktemp("cpp") / "rubik_engine"
    subprocess.run(["g++", "-std=c++17", "-O1", "-Wall", "-Wextra", "-o", str(binary), str(CPP_SOURCE)], check=True)
    return binary


def run_engine(engine, script: str) -> subprocess.CompletedProcess:
    return subprocess.run([str(engine)], input=script, capture_output=True, text=True)


@pytest.mark.parametrize("size", [2, 3, 5, 8])
def test_random_scrambles_print_identically(engine, size):
    session = Session(size, random.Random(100 + size))
    session.scramble(25)
    script = f"{size}\n" + "\n".join(format_step(record.step) for record in session.history) + "\n"

    result = run_engine(engine, script)

    assert result.returncode == 0, result.stderr
    assert result.stdout == render_text(size, session.initial_faces, session.history)


def test_handwritten_script_with_comments_and_wide_layers(engine):
    script = "3\n# first\nrow 2 right x3 + col 3 up x2\nrows 1-2 left\n"
    result = run_engine(engine, script.replace("rows", "row"))

    session = Session(3)
    session.apply_step(parse_step("row 2 right x3 + col 3 up x2"))
    session.apply_step(parse_step("row 1-2 left"))
    assert result.stdout == render_text(3, session.initial_faces, session.history)


@pytest.mark.parametrize("bad_script", ["3\nrow 4 right\n", "3\nrow 1 up\n", "9\n", "3\nspin 1 right\n", ""])
def test_bad_scripts_fail_with_a_message(engine, bad_script):
    result = run_engine(engine, bad_script)
    assert result.returncode == 1
    assert result.stderr.startswith("Eroare:")
