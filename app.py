"""Starts the Cubix Rubik simulator and opens it in the browser:  python app.py [--port 8765] [--no-browser]"""
import argparse
import threading
import webbrowser

from cubix.server import CubixServer
from cubix.session import Session

DEFAULT_PORT = 8765


def main() -> None:
    parser = argparse.ArgumentParser(description="Cubix Rubik simulator")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()

    server = CubixServer(("127.0.0.1", args.port), Session())
    url = f"http://127.0.0.1:{server.server_address[1]}/"
    print(f"Cubix ruleaza pe {url}  (Ctrl+C pentru oprire)")
    if not args.no_browser:
        threading.Timer(0.4, webbrowser.open, args=(url,)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nOprit.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
