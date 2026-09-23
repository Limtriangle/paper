#!/usr/bin/env bash
# Definition-of-done for writing/, as code (harness/writing.md §7).
#   bash tooling/writing-audit.sh          # audit only
#   bash tooling/writing-audit.sh --final  # also FAIL on any surviving \ph{}
set -uo pipefail

PAPER=${PAPER:-/home/work/research/paper}
ROOT="$PAPER/writing"
PDF="$PAPER/writing-main.pdf"
LOG="$PAPER/writing-build/main.log"
FINAL=0; [ "${1:-}" = "--final" ] && FINAL=1
fails=0

red()  { printf '\033[31mFAIL\033[0m %s\n' "$1"; fails=$((fails+1)); }
grn()  { printf '\033[32m ok \033[0m %s\n' "$1"; }
warn() { printf '\033[33mwarn\033[0m %s\n' "$1"; }

cd "$ROOT" || exit 1
echo "=== writing audit ==="

# 1. Build is green, no undefined citations/references.
if [ -f "$LOG" ]; then
    u=$(grep -ciE 'undefined (citation|reference)|Citation .* undefined|Reference .* undefined' "$LOG" || true)
    [ "$u" -eq 0 ] && grn "0 undefined citations/references" || red "$u undefined citation/reference warnings (see $LOG)"
else
    red "no build log — run tooling/build-writing.sh"
fi

# 2. No foreign-paper leftovers (the template's previous occupants). A leftover reads as a
#    finished, plausible claim about a project we are not running.
FOREIGN='\b(depth-ar|n-gram|ngram|speculative|drafting|gumbel|qwen|layer skip|stand)\b'
if grep -rniE "$FOREIGN" section/ tables/ figures/ 2>/dev/null | grep -q .; then
    red "foreign-paper leftovers:"; grep -rniE "$FOREIGN" section/ tables/ figures/ | sed 's/^/       /'
else
    grn "no foreign-paper leftovers"
fi

# 3. Citation hygiene.
c=$(grep -ro '\\cite{' section/ tables/ 2>/dev/null | wc -l)
[ "$c" -eq 0 ] && grn "no bare \\cite{} (all \\citep/\\citet)" || red "$c bare \\cite{}"

# 4. Cross-reference hygiene.
if grep -rqE '(Figure|Table|Section|Eq\.?)~?\\ref' section/ tables/ 2>/dev/null; then
    red "hand-typed Figure/Table~\\ref — use \\Cref"
else
    grn "all cross-refs use \\Cref"
fi

# 5. Macros used instead of literals.
if grep -rn 'HVI-CIDNet' section/ tables/ 2>/dev/null | grep -v 'mname' | grep -vE '^\s*%' | grep -q .; then
    warn "literal 'HVI-CIDNet' in prose (should be \\mname):"
    grep -rn 'HVI-CIDNet' section/ tables/ | grep -v 'mname' | sed 's/^/       /'
else
    grn "\\mname used everywhere (no literal method name)"
fi

# 6. Overclaims.
if grep -rniE 'state[- ]of[- ]the[- ]art|\bSOTA\b|lossless|first (ever|to)|outperforms all' section/ tables/ figures/ 2>/dev/null | grep -q .; then
    red "forbidden claim (SOTA / lossless / first-ever):"
    grep -rniE 'state[- ]of[- ]the[- ]art|\bSOTA\b|lossless|first (ever|to)|outperforms all' section/ tables/ figures/ | sed 's/^/       /'
else
    grn "no SOTA/lossless/first-ever claims"
fi
k=$(grep -ric 'to our knowledge' section/ 2>/dev/null | awk -F: '{s+=$2} END{print s+0}')
[ "$k" -le 1 ] && grn "'to our knowledge' used $k time(s) (max 1)" || red "'to our knowledge' used $k times (max 1)"

# 6b. False hardware claims: only RTX 2080 Ti exists on this host.
if grep -rniE 'a100|v100|h100|3090|4090|a6000|titan' section/ tables/ figures/ 2>/dev/null | grep -q .; then
    red "false hardware claim (only RTX 2080 Ti exists):"
    grep -rniE 'a100|v100|h100|3090|4090|a6000|titan' section/ tables/ figures/ | sed 's/^/       /'
else
    grn "no false hardware claims"
fi

# 6c. Em-dashes banned in the paper body.
if grep -rn -- '—' section/ tables/ figures/ 2>/dev/null | grep -q .; then
    warn "em-dash in paper source:"; grep -rn -- '—' section/ tables/ figures/ | head -5 | sed 's/^/       /'
else
    grn "no em-dashes"
fi

# 7. Visible filler + page limit (needs pdftotext; skipped with a warning if absent).
if command -v pdftotext >/dev/null && [ -f "$PDF" ]; then
    if [ "$(pdftotext "$PDF" - 2>/dev/null | grep -ciE 'placeholder|lipsum|lorem|TODO|AUTHORERR|\?\?')" -gt 0 ]; then
        red "visible filler/placeholder/?? in PDF:"
        pdftotext "$PDF" - 2>/dev/null | grep -ioE 'placeholder|lipsum|lorem|TODO|AUTHORERR|\?\?' | sort | uniq -c | sed 's/^/       /'
    else
        grn "no visible filler in PDF"
    fi
    tail=$(sed -e 's/%.*//' -e 's/([^)]*Cref[^)]*)//g' -e 's/\\Cref{[^}]*}//g' \
               -e 's/\\[a-zA-Z]*//g' -e 's/[{}$\\]//g' section/conclusion.tex \
           | tr '\n' ' ' | tr -s ' ' | sed 's/[[:space:]]*$//' | sed 's/[.,]*$//' \
           | awk '{for(i=NF-5;i<=NF;i++) printf "%s%s", $i, (i<NF?" ":"")}')
    if [ -n "$tail" ]; then
        lastp=""
        for p in $(seq 1 "$(pdfinfo "$PDF" 2>/dev/null | awk '/^Pages:/{print $2}')"); do
            pdftotext -f "$p" -l "$p" "$PDF" - 2>/dev/null | tr '\n' ' ' | tr -s ' ' | grep -qF "$tail" && lastp=$p
        done
        if [ -z "$lastp" ]; then warn "could not locate the conclusion's last words in the PDF"
        elif [ "$lastp" -le 4 ]; then grn "body ends on p$lastp (<= 4)"
        else red "BODY OVERFLOWS: conclusion ends on p$lastp, not p<=4"; fi
    fi
else
    warn "pdftotext not installed — filler and 4-page checks skipped (python3 tooling/pdfpages.py gives page count)"
fi

# 8. No secrets.
if grep -rnE 'ghp_[A-Za-z0-9]{20,}|sk-ant-[A-Za-z0-9-]{20,}|olp_[A-Za-z0-9]+' "$PAPER" --exclude-dir=.git --exclude-dir=writing-build -l 2>/dev/null | grep -q .; then
    red "TOKEN IN REPO"
else
    grn "no tokens in repo"
fi

# 9. Provisional values: \ph{} invented vs \phm{} measured.
ph=$(grep -roE '\\ph\{'  section/ tables/ figures/ 2>/dev/null | wc -l)
phm=$(grep -roE '\\phm\{' section/ tables/ figures/ 2>/dev/null | wc -l)
if [ "$FINAL" -eq 1 ]; then
    if [ "$ph" -eq 0 ]; then grn "0 surviving \\ph{} — no unevidenced numbers"
    else
        red "$ph \\ph{} still wrapped — each is a claim with NO EVIDENCE. Land it or DELETE THE SENTENCE."
        grep -rnoE '\\ph\{[^}]*\}' section/ tables/ figures/ 2>/dev/null | head -12 | sed 's/^/       /'
    fi
    [ "$phm" -gt 0 ] && warn "$phm \\phm{} still wrapped — measured; UNWRAP (tooling/unwrap-phm.sh), never delete" || grn "0 surviving \\phm{}"
else
    grn "$ph \\ph{} unevidenced + $phm \\phm{} measured (see ralph/PH-LEDGER.md)"
fi

# 9b. Every \phm{} must match the JSON key it claims.
if out=$(python3 "$PAPER/tooling/verify-phm.py" 2>&1); then
    grn "$(printf '%s' "$out" | tail -1 | sed 's/^ *//')"
else
    red "\\phm{} verification failed:"; printf '%s\n' "$out" | tail -15 | sed 's/^/       /'
fi

# 9c. Generated tables match their JSON sources.
if [ -f "$ROOT/tables/spec.json" ]; then
    if out=$(python3 "$PAPER/tooling/gen-table.py" --check 2>&1); then grn "generated tables match JSON"
    else red "generated tables drifted from JSON (run gen-table.py --write):"; printf '%s\n' "$out" | tail -8 | sed 's/^/       /'; fi
fi

# 10. Pushed.
cd "$PAPER"
[ -z "$(git status --porcelain 2>/dev/null)" ] && grn "working tree clean" || warn "uncommitted changes"
[ -z "$(git log origin/main..HEAD --oneline 2>/dev/null)" ] && grn "pushed to origin" || warn "unpushed commits"

echo "=== $([ $fails -eq 0 ] && echo 'PASS' || echo "$fails FAILURE(S)") ==="
exit $fails
