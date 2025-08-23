#!/bin/bash

set -eux

# Find security issues in Python code
bandit -r src
