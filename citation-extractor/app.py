"""Flask web app: paste a case, get its citations.

Run:  python app.py   (then open http://127.0.0.1:5000)
"""

from __future__ import annotations

import os

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


if __name__ == "__main__":
    app.run(host=os.environ.get("HOST", "127.0.0.1"), port=int(os.environ.get("PORT", 5000)),
            debug=bool(os.environ.get("FLASK_DEBUG")))
