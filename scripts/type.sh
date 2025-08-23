#!/bin/bash

set -eux

mypy --config-file mypy.ini src
