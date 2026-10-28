"""Step-by-step exports of the unfolded cube: plain text (numbers) and HTML (colours)."""
from __future__ import annotations

from html import escape

from .cube import Face, Faces
from .notation import format_step
from .session import FACE_NAMES, StepRecord

BAND_FACES = (Face.FRONT, Face.RIGHT, Face.BACK, Face.LEFT)
FACE_COLORS = {
    Face.UP: "#f3f3ef", Face.FRONT: "#2db872", Face.RIGHT: "#e5484d",
    Face.BACK: "#3e7bfa", Face.LEFT: "#f5923e", Face.DOWN: "#f6cb4d",
}


def render_text(size: int, initial_faces: Faces, records: list[StepRecord]) -> str:
    """Same layout as the C++ engine's output; tests keep the two byte-identical."""
    sections = [f"Starea initiala a cubului Rubik {size}x{size}x{size}:\n{render_net_text(initial_faces, size)}"]
    sections += [
        f"Pasul {record.number}: {format_step(record.step)}\n{render_net_text(record.faces, size)}"
        for record in records
    ]
    return "\n".join(sections)


def render_net_text(faces: Faces, size: int) -> str:
    indent = " " * (2 * size + 4)
    top = [indent + line for line in _face_block(faces[Face.UP], size)]
    middle = [
        " ".join(block[line] for block in (_face_block(faces[face], size) for face in BAND_FACES))
        for line in range(size + 2)
    ]
    bottom = [indent + line for line in _face_block(faces[Face.DOWN], size)]
    return "\n".join(top + middle + bottom) + "\n"


def _face_block(matrix: list[list[int]], size: int) -> list[str]:
    border = " ".join("*" * (size + 2))
    rows = ["* " + "".join(f"{value} " for value in row) + "*" for row in matrix]
    return [border, *rows, border]


def render_html(size: int, initial_faces: Faces, records: list[StepRecord]) -> str:
    cards = [_html_card("Starea inițială", "", initial_faces, None, size)]
    previous = initial_faces
    for record in records:
        cards.append(_html_card(f"Pasul {record.number}", format_step(record.step), record.faces, previous, size))
        previous = record.faces
    return _HTML_PAGE.format(
        title=f"Cub Rubik {size}×{size}×{size}",
        colors="".join(f"--c{face.value}:{color};" for face, color in FACE_COLORS.items()),
        cards="\n".join(cards),
    )


def _html_card(title: str, notation: str, faces: Faces, previous: Faces | None, size: int) -> str:
    def block(face: Face, column: int, row: int) -> str:
        cells = "".join(
            f'<i class="cell{" changed" if previous and previous[face][r][c] != value else ""}" '
            f'style="--v:var(--c{value})"></i>'
            for r, line in enumerate(faces[face])
            for c, value in enumerate(line)
        )
        return (
            f'<div class="block" style="grid-column:{column};grid-row:{row}" title="{FACE_NAMES[face]}">{cells}</div>'
        )

    blocks = [block(Face.UP, 1, 1)]
    blocks += [block(face, column, 2) for column, face in enumerate(BAND_FACES, start=1)]
    blocks.append(block(Face.DOWN, 1, 3))
    subtitle = f"<code>{escape(notation)}</code>" if notation else ""
    return (
        f'<section class="card"><header><h2>{escape(title)}</h2>{subtitle}</header>'
        f'<div class="net" style="--n:{size}">{"".join(blocks)}</div></section>'
    )


_HTML_PAGE = """<!doctype html>
<html lang="ro"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<style>
:root{{color-scheme:light dark;{colors}--bg:#f5f5f3;--card:#fff;--ink:#16171b;--muted:#6c6f78;--line:rgba(20,22,30,.1)}}
@media (prefers-color-scheme:dark){{:root{{--bg:#0c0d10;--card:#15161a;--ink:#ececee;--muted:#8b8e97;--line:rgba(255,255,255,.09)}}}}
body{{margin:0;padding:48px 24px;background:var(--bg);color:var(--ink);font:15px/1.5 "Segoe UI Variable Text","Segoe UI",Inter,system-ui,sans-serif}}
h1{{max-width:960px;margin:0 auto 32px;font-size:28px;font-weight:600;letter-spacing:-.02em}}
.card{{max-width:960px;margin:0 auto 20px;padding:24px 28px;background:var(--card);border:1px solid var(--line);border-radius:20px;break-inside:avoid}}
header{{display:flex;flex-wrap:wrap;gap:6px 16px;align-items:baseline;margin-bottom:18px}}
h2{{margin:0;font-size:17px;font-weight:600}}
code{{color:var(--muted);font-size:13px}}
.net{{display:grid;grid-template-columns:repeat(4,max-content);grid-template-rows:repeat(3,max-content);gap:10px;justify-content:start}}
.block{{display:grid;grid-template-columns:repeat(var(--n),22px);gap:3px}}
.cell{{width:22px;height:22px;border-radius:5px;background:var(--v);box-shadow:inset 0 0 0 1px rgba(0,0,0,.14)}}
.cell.changed{{outline:2px solid var(--ink);outline-offset:1px}}
p.note{{max-width:960px;margin:24px auto 0;color:var(--muted);font-size:13px}}
</style></head><body>
<h1>{title}</h1>
{cards}
<p class="note">Căsuțele conturate sunt cele schimbate față de pasul anterior.</p>
</body></html>
"""
