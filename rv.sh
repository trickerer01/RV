#!/usr/bin/env sh
exec "${PYTHON:-python3}" -Werror -Xdev "$(dirname "$(realpath "$0")")/rv/__main__.py" "$@"
