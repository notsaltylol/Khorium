#!/usr/bin/env bash
set -e

source .venv/bin/activate
Khorium --port 10000 --host 0.0.0.0
