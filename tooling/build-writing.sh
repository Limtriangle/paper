#!/usr/bin/env bash
# Build writing/ -> writing-main.pdf with Tectonic (XeTeX engine, no TeX Live needed).
#
# Layout is Overleaf-style: main.tex in writing/icml2024/, section/tables/figures at the
# writing/ root and \input'ed by root-relative paths. Tectonic resolves \input relative to
# the main file, so we build in a flattened staging copy, exactly like upstream.
set -euo pipefail

PAPER=${PAPER:-/home/work/research/paper}
ROOT="$PAPER/writing"
OUT="$PAPER/writing-build"
PDF="$PAPER/writing-main.pdf"
STAGE="$OUT/stage"

command -v tectonic >/dev/null || { echo "tectonic not on PATH — run bootstrap.sh"; exit 1; }

rm -rf "$STAGE"; mkdir -p "$STAGE"
cp -r "$ROOT"/section "$ROOT"/tables "$ROOT"/figures "$STAGE"/
cp "$ROOT"/icml2024/* "$STAGE"/
# \DeclareUnicodeCharacter is a pdfLaTeX/inputenc command, undefined in XeTeX.
{ printf '%s\n' '\providecommand{\DeclareUnicodeCharacter}[2]{}'; cat "$STAGE/main.tex"; } > "$STAGE/main.tex.tmp"
mv "$STAGE/main.tex.tmp" "$STAGE/main.tex"

cd "$STAGE"
echo "==> tectonic build"
tectonic -X compile main.tex --keep-logs --keep-intermediates ${TECTONIC_ARGS:-}
cp "$STAGE/main.pdf" "$PDF"
cp "$STAGE/main.log" "$OUT/main.log" 2>/dev/null || true
if command -v pdfinfo >/dev/null; then
    echo "==> wrote $PDF ($(pdfinfo "$PDF" | awk '/^Pages:/{print $2}') pages)"
else
    echo "==> wrote $PDF"
fi
