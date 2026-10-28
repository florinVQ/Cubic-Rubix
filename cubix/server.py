"""Local HTTP server: serves the web UI and a small JSON API over one shared session."""
from __future__ import annotations

import json
import mimetypes
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .export import render_html, render_text
from .serialize import action_to_json, state_to_json, step_from_json
from .session import DEFAULT_SCRAMBLE_STEPS, Session

WEB_ROOT = Path(__file__).resolve().parent.parent / "web"
EXPORT_FORMATS = {
    "txt": ("text/plain; charset=utf-8", "MatriceDesfasurata.txt", render_text),
    "html": ("text/html; charset=utf-8", "MatriceDesfasurata.html", render_html),
}
# Windows registries sometimes map .js to text/plain, which breaks ES modules.
MIME_OVERRIDES = {".js": "text/javascript", ".css": "text/css", ".html": "text/html", ".svg": "image/svg+xml"}


class CubixServer(ThreadingHTTPServer):
    def __init__(self, address: tuple[str, int], session: Session) -> None:
        super().__init__(address, CubixHandler)
        self.session = session
        self.lock = threading.Lock()


class CubixHandler(BaseHTTPRequestHandler):
    server: CubixServer

    def do_GET(self) -> None:
        url = urlparse(self.path)
        if url.path == "/api/state":
            return self._with_session(lambda session: self._send_json(state_to_json(session)))
        if url.path == "/api/export":
            return self._with_session(lambda session: self._send_export(session, parse_qs(url.query)))
        self._send_static(url.path)

    def do_POST(self) -> None:
        routes = {
            "/api/reset": self._reset,
            "/api/step": self._step,
            "/api/scramble": self._scramble,
            "/api/solve": self._solve,
        }
        handler = routes.get(urlparse(self.path).path)
        if handler is None:
            return self._send_error(HTTPStatus.NOT_FOUND, "unknown endpoint")
        try:
            body = self._read_json()
            self._with_session(lambda session: self._send_json(handler(session, body)))
        except (ValueError, TypeError) as error:
            self._send_error(HTTPStatus.BAD_REQUEST, str(error))

    def _reset(self, session: Session, body: dict) -> dict:
        session.reset(int(body.get("size", session.size)))
        return action_to_json(session, [])

    def _step(self, session: Session, body: dict) -> dict:
        return action_to_json(session, [session.apply_step(step_from_json(body.get("moves")))])

    def _scramble(self, session: Session, body: dict) -> dict:
        return action_to_json(session, session.scramble(int(body.get("count", DEFAULT_SCRAMBLE_STEPS))))

    def _solve(self, session: Session, body: dict) -> dict:
        return action_to_json(session, session.solve())

    def _with_session(self, action) -> None:
        with self.server.lock:
            action(self.server.session)

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        if not length:
            return {}
        try:
            body = json.loads(self.rfile.read(length))
        except json.JSONDecodeError as error:
            raise ValueError("request body is not valid JSON") from error
        if not isinstance(body, dict):
            raise ValueError("request body must be a JSON object")
        return body

    def _send_export(self, session: Session, query: dict) -> None:
        content_type, filename, render = EXPORT_FORMATS.get(query.get("format", ["html"])[0], (None, None, None))
        if render is None:
            return self._send_error(HTTPStatus.BAD_REQUEST, "format must be txt or html")
        payload = render(session.size, session.initial_faces, session.history).encode("utf-8")
        self._send(HTTPStatus.OK, content_type, payload, {"Content-Disposition": f'attachment; filename="{filename}"'})

    def _send_static(self, url_path: str) -> None:
        relative = "index.html" if url_path in ("", "/") else url_path.lstrip("/")
        target = (WEB_ROOT / relative).resolve()
        if not target.is_relative_to(WEB_ROOT) or not target.is_file():
            return self._send_error(HTTPStatus.NOT_FOUND, "not found")
        content_type = MIME_OVERRIDES.get(target.suffix) or mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        self._send(HTTPStatus.OK, content_type, target.read_bytes())

    def _send_json(self, payload: dict) -> None:
        self._send(HTTPStatus.OK, "application/json", json.dumps(payload).encode("utf-8"))

    def _send_error(self, status: HTTPStatus, message: str) -> None:
        self._send(status, "application/json", json.dumps({"error": message}).encode("utf-8"))

    def _send(self, status: HTTPStatus, content_type: str, payload: bytes, headers: dict | None = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        for name, value in (headers or {}).items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format: str, *args) -> None:  # keep the console quiet
        pass
