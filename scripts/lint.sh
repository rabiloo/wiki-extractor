#!/bin/bash

set -eux

ruff check --config ruff.toml --select I src tests

ruff check --config ruff.toml src tests
