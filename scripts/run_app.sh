#!/usr/bin/env bash
set -e

source .venv/bin/activate
export PYTHONPATH=src
streamlit run app.py