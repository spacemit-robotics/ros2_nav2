#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
module_root="$(cd "$script_dir/.." && pwd)"
artifact_dir="${SROBOTIS_TEST_ARTIFACT_DIR:-${SROBOTIS_OUTPUT_ROOT:-$PWD/output}/test/pr/middleware__ros2__planning__nav2/modules/middleware__ros2__planning__nav2}"
log_dir="$artifact_dir/logs"
log_file="$log_dir/nav2_zmq_timeout.log"

mkdir -p "$log_dir"
exec > >(tee "$log_file") 2>&1

echo "[info] module_root=$module_root"
echo "[info] artifact_dir=$artifact_dir"

python3 "$script_dir/check_nav2_logic.py" zmq-timeout "$module_root"

echo "ALL TESTS PASSED: nav2-zmq-timeout"