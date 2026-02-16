#!/usr/bin/env bash

set -e

# Default command is pytest with coverage
pytest_cmd="pytest --cov=chuscraper --cov-report=xml"

chrome_executable=$(uv run python -c "from chuscraper.core.config import find_executable;print(find_executable())")
echo "Chrome executable: $chrome_executable"

chrome_version=$(uv run python -c "import os, subprocess, sys; path = r'$chrome_executable'; print(subprocess.run([path, '--version'], capture_output=True, text=True).stdout.strip()) if os.name != 'nt' else print('SKIP: Windows chrome.exe may not return version')")
echo "Chrome version: $chrome_version"

set -x
uv run $pytest_cmd "$@"
