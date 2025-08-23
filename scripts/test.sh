#!/bin/bash

set -eux

pytest  --cov-branch --cov-report term-missing:skip-covered --cov-report xml:coverage-reports/coverage.xml --cov=app tests/
