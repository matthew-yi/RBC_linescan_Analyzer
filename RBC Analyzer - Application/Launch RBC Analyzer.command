#!/bin/zsh
cd -- "${0:A:h}"
if [[ -x .venv/bin/python ]]; then
  .venv/bin/python app/rbc_app.py
else
  python3 app/rbc_app.py
fi
