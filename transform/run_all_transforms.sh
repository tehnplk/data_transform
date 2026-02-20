#!/usr/bin/env bash
set -euo pipefail
# Run through dispatcher which handles pending data only
/usr/bin/python3 "$HOME/transform/dispatcher.py"
