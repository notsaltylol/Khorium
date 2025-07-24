#!/usr/bin/env bash
set -e

# Build and install the Vue components
cd vue-components
npm i
npm run build
cd -

pip install uv;
uv sync;
