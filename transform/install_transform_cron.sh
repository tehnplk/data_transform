#!/usr/bin/env bash
set -euo pipefail
( crontab -l 2>/dev/null | grep -v 'run_all_transforms.sh' ; echo '*/30 * * * * $HOME/transform/run_all_transforms.sh' ) | crontab -
crontab -l | tail -n 5
