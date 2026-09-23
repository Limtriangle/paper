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
sed -i '1i \\providecommand{\\DeclareUnicodeCharacter}[2]{}' "$STAGE/main.tex"

cd "$STAGE"
echo "==> tectonic build"
tectonic -X compile main.tex --keep-logs --keep-intermediates ${TECTONIC_ARGS:-}
cp "$STAGE/main.pdf" "$PDF"
cp "$STAGE/main.log" "$OUT/main.log" 2>/dev/null || true
echo "==> wrote $PDF ($(python3 - "$PDF" <<'EOF'
import sys, re
data = open(sys.argv[1], 'rb').read()
m = re.findall(rb'/Type\s*/Page[^s]', data)
print(f"{len(m)} pages")
EOF
))"
