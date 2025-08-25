#!/bin/bash

set -eux

ruff check --config ruff.toml --select I src tests --exit-zero

ruff check --config ruff.toml src tests --exit-zero
