#!/usr/bin/env bash
# url_to_md.sh <url>  — convert a URL to Markdown on stdout via Microsoft markitdown.
#
# Resolution order:
#   1. `markitdown` already on PATH
#   2. `uvx` / `uv`  — auto-fetches Python 3.10+ AND markitdown (cached after 1st run)
#   3. fail (exit 127) and print one-line bootstrap options
#
# markitdown needs Python 3.10+; the uv path makes an older system Python irrelevant.
# Set MARKITDOWN_SPEC=markitdown[all] for URLs that point at PDF/Word/Excel/PPT.
# Self-check (no network, no deps):  url_to_md.sh --selfcheck
set -euo pipefail

SPEC="${MARKITDOWN_SPEC:-markitdown}"

# Echo which engine is available (markitdown|uvx|uv), or nothing if none.
emit_engine() {
  if command -v markitdown >/dev/null 2>&1; then printf 'markitdown\n'
  elif command -v uvx       >/dev/null 2>&1; then printf 'uvx\n'
  elif command -v uv        >/dev/null 2>&1; then printf 'uv\n'
  fi
}

convert() {
  local url="$1"
  case "$(emit_engine)" in
    markitdown) exec markitdown "$url" ;;
    uvx)        exec uvx --quiet --from "$SPEC" markitdown "$url" ;;
    uv)         exec uv tool run --quiet --from "$SPEC" markitdown "$url" ;;
    *)
      cat >&2 <<'EOF'
weblink-capture: no markitdown runtime found. Pick one, then re-run:
  pip3 install --user uv     # recommended: uv fetches Python 3.10+ AND markitdown (cached)
  pipx install markitdown    # if you have pipx
  pip install markitdown     # only works on Python 3.10+
EOF
      exit 127 ;;
  esac
}

# ponytail: shell dispatch is simple; this is the one runnable check it leaves behind.
if [ "${1:-}" = "--selfcheck" ]; then
  e="$(emit_engine)"
  case "$e" in markitdown|uvx|uv|"") ;; *) echo "FAIL: bad engine '$e'" >&2; exit 1 ;; esac
  [ -n "$SPEC" ] || { echo "FAIL: empty SPEC" >&2; exit 1; }
  # no-arg must be a usage error, not a silent success
  if "$0" >/dev/null 2>&1; then echo "FAIL: no-arg should error" >&2; exit 1; fi
  echo "ok: engine='${e:-none}' spec='$SPEC'"
  exit 0
fi

[ "$#" -ge 1 ] && [ -n "${1:-}" ] || { echo "usage: url_to_md.sh <url>" >&2; exit 2; }
convert "$1"
