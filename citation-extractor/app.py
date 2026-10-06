"""Flask web app: paste a case, get its citations.

Run:  python app.py   (opens http://127.0.0.1:8765 in your browser)
"""

from __future__ import annotations

import os
import socket
import threading
import webbrowser

from flask import Flask, Response, jsonify, request, send_from_directory

from citeextract import analyze, courtlistener
from citeextract.exporters import export

HERE = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, static_folder=os.path.join(HERE, "static"), static_url_path="/static")
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024


@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.get("/api/sample")
def sample():
    return send_from_directory(os.path.join(HERE, "samples"), "sample_opinion.txt", mimetype="text/plain")


@app.get("/api/config")
def config():
    return jsonify({"server_token": bool(courtlistener.default_token())})


@app.post("/api/analyze")
def analyze_route():
    payload = request.get_json(silent=True) or {}
    text = payload.get("text") or ""
    if not text.strip():
        return jsonify({"error": "Paste the text of a case (or upload a file) first."}), 400
    token = (payload.get("token") or "").strip() or None
    try:
        result = analyze(text, lookup=bool(payload.get("lookup")), token=token)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify(result)


@app.post("/api/export/<fmt>")
def export_route(fmt: str):
    result = request.get_json(silent=True)
    if not isinstance(result, dict) or "authorities" not in result:
        return jsonify({"error": "Send the analysis result as the JSON body."}), 400
    result.setdefault("unresolved", [])
    result.setdefault("text", "")
    try:
        filename, mimetype, content = export(result, fmt)
    except KeyError:
        return jsonify({"error": f"Unknown export format: {fmt}"}), 404
    return Response(content, mimetype=mimetype,
                    headers={"Content-Disposition": f'attachment; filename="{filename}"'})


def _free_port(host: str, start: int) -> int:
    """First free port from `start`. (macOS's AirPlay Receiver squats on 5000,
    which shows up as a blank page, so we avoid it.)"""
    for port in range(start, start + 50):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind((host, port))
                return port
            except OSError:
                continue
    raise SystemExit(f"No free port found between {start} and {start + 49}.")


if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ["PORT"]) if os.environ.get("PORT") else _free_port(host, 8765)
    url = f"http://{host}:{port}"
    print(f"\nCitation Extractor is running at {url}")
    print("Leave this window open while you use it. Close it (or press Control+C) to stop.\n")
    if not os.environ.get("NO_BROWSER"):
        threading.Timer(1.5, webbrowser.open, args=[url]).start()
    app.run(host=host, port=port, debug=bool(os.environ.get("FLASK_DEBUG")))
