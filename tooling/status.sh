#!/usr/bin/env bash
# One-screen dashboard for master's sweep: phase, git, results, GPUs, running jobs.
PAPER=${PAPER:-/home/work/research/paper}
RESEARCH=${RESEARCH:-/home/work/research}
cd "$PAPER" || exit 1
echo "=== $(date '+%Y-%m-%d %H:%M') ==="
echo "--- phase (ralph/STATUS.md)"
grep -m1 -iE '^\*\*phase' ralph/STATUS.md 2>/dev/null || sed -n '1,6p' ralph/STATUS.md 2>/dev/null
echo "--- git"
git status --short | head -10
echo "  HEAD $(git log -1 --format='%h %s' 2>/dev/null)  unpushed: $(git log origin/main..HEAD --oneline 2>/dev/null | wc -l)"
echo "--- results: $(ls ralph/results/*.json 2>/dev/null | wc -l) JSON | RESULTS.md rows: $(grep -c '^| 20' ralph/RESULTS.md 2>/dev/null)"
echo "--- paper: \\ph $(grep -roE '\\ph\{' writing/section writing/tables 2>/dev/null | wc -l) | \\phm $(grep -roE '\\phm\{' writing/section writing/tables 2>/dev/null | wc -l) | pdf $(stat -c '%y' writing-main.pdf 2>/dev/null | cut -c1-16)"
echo "--- inbox open questions: $(awk '/^## Open questions/{f=1;next} /^## /{f=0} f && /^- \[ \]/' ralph/INBOX.md 2>/dev/null | wc -l)"
echo "--- gpus"
nvidia-smi --query-gpu=index,utilization.gpu,memory.used,memory.total --format=csv,noheader 2>/dev/null | sed 's/^/  /'
echo "--- running jobs (status.json state=running)"
for s in "$RESEARCH"/outputs/*/*/*/status.json; do
    [ -f "$s" ] || continue
    if grep -q '"running"' "$s" 2>/dev/null; then echo "  $(dirname "$s" | sed "s|$RESEARCH/outputs/||")"; fi
done
