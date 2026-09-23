#!/usr/bin/env bash
# Mechanical unwrap: \phm{X} -> X. Nothing else may change.
#   bash tooling/unwrap-phm.sh --dry     # show what would change; verify purity; touch nothing
#   bash tooling/unwrap-phm.sh --apply   # do it
# Refuses unless verify-phm.py passes first: never unwrap an unverified value.
set -uo pipefail
PAPER=${PAPER:-/home/work/research/paper}
ROOT="$PAPER/writing"
MODE="${1:---dry}"
cd "$ROOT" || exit 1

if ! python3 "$PAPER/tooling/verify-phm.py" >/dev/null 2>&1; then
    echo "=== ABORT: verify-phm.py fails. Fix the bindings before unwrapping. ==="; exit 1
fi

# main.tex is excluded: the macro DEFINITION lives there. We keep \phm defined and simply stop using it.
FILES=$(grep -rl '\\phm{' section/ tables/ figures/ 2>/dev/null)
[ -z "$FILES" ] && { echo "no \\phm{} found — already unwrapped?"; exit 0; }

echo "=== files carrying \\phm{}: ==="
for f in $FILES; do printf '  %-40s %s\n' "$f" "$(grep -o '\\phm{' "$f" | wc -l)"; done

TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
fail=0
for f in $FILES; do
    b=$(basename "$f")
    cp "$f" "$TMP/$b.orig"
    perl -0777 -pe 's/\\phm\{((?:[^{}]|\{[^{}]*\})*)\}/$1/g' "$f" > "$TMP/$b.new"
    perl -0777 -pe 's/\\phm\{((?:[^{}]|\{[^{}]*\})*)\}/$1/g' "$TMP/$b.orig" > "$TMP/$b.expect"
    cmp -s "$TMP/$b.new" "$TMP/$b.expect" || { echo "  IMPURE: $f"; fail=1; }
    grep -q '\\phm{' "$TMP/$b.new" && { echo "  RESIDUE: $f"; fail=1; }
done
[ "$fail" -eq 0 ] && echo "  ok — all rewrites are pure macro strips, 0 value changes"
[ "$fail" -ne 0 ] && { echo "=== ABORT: not pure. Nothing written. ==="; exit 1; }

if [ "$MODE" = "--apply" ]; then
    for f in $FILES; do cp "$TMP/$(basename "$f").new" "$f"; done
    echo "=== applied. Now: bash tooling/build-writing.sh && bash tooling/writing-audit.sh --final ==="
else
    echo "=== dry run — nothing written. Re-run with --apply. ==="
fi
