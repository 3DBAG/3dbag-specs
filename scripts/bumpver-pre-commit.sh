#!/usr/bin/env sh
set -eu

uv lock --quiet
git add --update -- uv.lock
