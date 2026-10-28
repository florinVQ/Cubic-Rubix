# Cubix – Rubik's cube simulator

A Python app (standard library only) with a local web interface, plus the improved C++ engine.
Romanian version: `README.ro.md`.

## Run
```
python app.py            # opens http://127.0.0.1:8765  (options: --port N, --no-browser)
python -m pytest         # tests (needs pytest; the parity test also needs g++)
```

## Features
- **3D cube**: drag to tilt it; press the arrows around the front face to turn a row or column.
- **V (rotation speed)** in degrees per second; **Pause** stops between turns.
- **Layers per move**: 1 or 2 adjacent rows/columns.
- **Composed step**: collect several moves (e.g. 3x Row 2 → and 2x Column 3 ↑); they count as ONE step.
- **Unfolded cube** in colour, updated on every turn; moved cells slide from their old position to the new one.
- **How the matrices swap**: shows the 1–6 values in the matrices, the face cycle and the pairs `Front[r][c] → Right[r][c]`.
- **Export**: colour `.html` and `.txt` (same layout as the original MatriceDesfasurata.txt), each step numbered.
- **Auto-resolve**: undoes the recorded steps, newest first; each undone step is still one step.
  It is not a general solver: it solves what was scrambled through the app.

Cube sizes 2×2 up to 8×8.

## C++ engine
`cpp/rubik_engine.cpp` uses the same logic and prints the same text as the `.txt` export.
```
g++ -std=c++17 -O2 -o rubik_engine cpp/rubik_engine.cpp
./rubik_engine examples/exemplu.txt MatriceDesfasurata.txt
```
Script format: first line is the cube size; every following line is one step, with moves joined by `+`
(`row 2 right x3 + col 3 up x2`); layers are 1-based, `row 1-2 left` turns two layers; `#` starts a comment.

Fixes compared to the original program:
- the "two consecutive rows" checks used `||` instead of `&&`, so they always refused;
- turning an outer layer now also rotates the face it touches;
- moves are validated before anything changes.

## Layout
- `cubix/cube.py` – model and permutations (one list of cell transfers drives both the matrices and the UI)
- `cubix/session.py` – history, scramble, auto-resolve
- `cubix/export.py` – txt and html export
- `cubix/server.py` – local API
- `web/` – interface
- `tests/` – the engine is checked against an independent physical 3D model, and against the C++ output
