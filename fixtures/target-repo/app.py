"""Tiny toy Flask app with two deliberately planted bugs, used as the
reproduction target for SlopShield's sandboxed repro step.

Bug 1 (reflected XSS): /greet echoes the `name` query param straight into
HTML with no escaping.

Bug 2 (path traversal): /read joins the `file` query param onto DATA_DIR
with no sanitization, so `../secret_admin.txt` escapes the data directory.
"""
import os

from flask import Flask, request

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")


@app.route("/greet")
def greet():
    name = request.args.get("name", "world")
    return f"<h1>Hello {name}</h1>"


@app.route("/read")
def read():
    filename = request.args.get("file", "public.txt")
    path = os.path.join(DATA_DIR, filename)
    with open(path, "r") as f:
        return f.read()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
