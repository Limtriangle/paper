#!/usr/bin/env bash
# Launch (or revive) the three-agent team in herdr session "ralph":
#   ┌──────────────── master ────────────────┐
#   │ experiment          │ writing          │
#   └──────────────────────────────────────────┘
# Each pane runs Claude Code in /home/work/paper with its persona as the opening prompt.
#
#   bash herdr/start-team.sh            # create panes + start agents
#   bash herdr/start-team.sh --no-agents  # panes only (e.g. before `claude` is logged in)
#   herdr --session ralph               # attach (ctrl+b q detaches)
set -euo pipefail
PAPER=${PAPER:-/home/work/research/paper}
SESSION=ralph
START_AGENTS=1; [ "${1:-}" = "--no-agents" ] && START_AGENTS=0
H="herdr --session $SESSION"

command -v herdr >/dev/null || { echo "herdr not on PATH — run bootstrap.sh"; exit 1; }
command -v claude >/dev/null || { echo "claude not on PATH — run bootstrap.sh"; exit 1; }

# Make sure the session's server is up (idempotent).
$H server --daemon >/dev/null 2>&1 || true
sleep 1

pane_by_label() { # label -> pane id, or empty
    $H pane list --json 2>/dev/null | python3 -c '
import json, sys
label = sys.argv[1]
for line in sys.stdin:
    line = line.strip()
    if not line.startswith("{"): continue
    try: panes = json.loads(line)["result"]["panes"]
    except Exception: continue
    for p in panes:
        if p.get("label") == label: print(p["id"]); sys.exit(0)
' "$1"
}

first_pane() {
    $H pane list --json 2>/dev/null | python3 -c '
import json, sys
for line in sys.stdin:
    line = line.strip()
    if not line.startswith("{"): continue
    try: panes = json.loads(line)["result"]["panes"]
    except Exception: continue
    if panes: print(panes[0]["id"]); sys.exit(0)
'
}

if [ -z "$(pane_by_label master)" ]; then
    echo "==> building layout"
    $H workspace create --cwd "$PAPER" --label ralph >/dev/null 2>&1 || true
    sleep 1
    M=$(first_pane)
    [ -n "$M" ] || { echo "no pane found after workspace create; run 'herdr --session $SESSION' once interactively"; exit 1; }
    $H pane rename "$M" master
    E=$($H pane split "$M" --direction down --ratio 0.55 --json | python3 -c 'import json,sys; print(json.load(sys.stdin)["result"]["pane"]["id"])')
    $H pane rename "$E" experiment
    W=$($H pane split "$E" --direction right --ratio 0.5 --json | python3 -c 'import json,sys; print(json.load(sys.stdin)["result"]["pane"]["id"])')
    $H pane rename "$W" writing
else
    echo "==> layout exists"
fi

if [ "$START_AGENTS" -eq 1 ]; then
    for role in master experiment writing; do
        P=$(pane_by_label $role)
        echo "==> starting $role in pane $P"
        $H pane run "$P" "cd $PAPER && source env.sh && claude --permission-mode acceptEdits \"You are $role. Read CLAUDE.md, then harness/$role.md, then HVI-PLAN.md, and begin your opening sequence. Never wait for a human.\""
        sleep 2
    done
fi
echo "==> attach with: herdr --session $SESSION    (ctrl+b q to detach)"
$H pane list
