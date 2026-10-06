#!/bin/bash
# One-step launcher for Mac. In Terminal:  bash start-mac.command
cd "$(dirname "$0")" || exit 1
if ! command -v python3 >/dev/null 2>&1; then
  echo "Python isn't installed. Get it from https://www.python.org/downloads/ and try again."
  exit 1
fi
if [ ! -x .venv/bin/python ]; then
  echo "First run: setting things up (this takes a minute)..."
  python3 -m venv .venv || exit 1
fi
.venv/bin/python -m pip install -q --disable-pip-version-check -r requirements.txt || exit 1
.venv/bin/python -m pip install -q --disable-pip-version-check --no-deps eyecite==2.6.11 || exit 1
.venv/bin/python app.py
