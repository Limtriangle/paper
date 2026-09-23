#!/usr/bin/env bash
# Launch (or revive) the three-agent team in herdr session "ralph":
#   ┌──────────────── master (w1:p1) ────────────────┐
#   │ experiment (w1:p2)     │ writing (w1:p3)       │
#   └─────────────────────────────────────────────────┘
# Each pane runs Claude Code in /home/work/paper with its persona as the opening prompt.
#
#   bash herdr/start-team.sh              # ensure server + layout, start any agent not running
#   bash herdr/start-team.sh --no-agents  # server + layout only (e.g. before `claude` is logged in)
#   bash herdr/start-team.sh --resume     # start agents with `claude --continue` instead of the opening prompt
#   herdr --session ralph                 # attach and watch (ctrl+b q detaches)
set -euo pipefail
PAPER=${PAPER:-/home/work/research/paper}
SESSION=ralph
MODE=start; case "${1:-}" in --no-agents) MODE=none;; --resume) MODE=resume;; esac
H="herdr --session $SESSION"

command -v herdr >/dev/null || { echo "herdr not on PATH — run bootstrap.sh"; exit 1; }
command -v claude >/dev/null || { echo "claude not on PATH — run bootstrap.sh"; exit 1; }

jget() { python3 -c 'import json,sys; d=json.load(sys.stdin); print(eval("d"+sys.argv[1]))' "$1"; }

# --- 1. headless server for the named session -------------------------------
if ! herdr session list --json | python3 -c 'import json,sys; s=[x for x in json.load(sys.stdin)["sessions"] if x["name"]==sys.argv[1]]; sys.exit(0 if s and s[0]["running"] else 1)' "$SESSION"; then
    echo "==> starting headless herdr server for session $SESSION"
    nohup herdr --session "$SESSION" server > "$HOME/.config/herdr/herdr-$SESSION.nohup.log" 2>&1 &
    for _ in 1 2 3 4 5 6 7 8 9 10; do sleep 1; $H pane list >/dev/null 2>&1 && break; done
fi

pane_by_label() { $H pane list | python3 -c '
import json, sys
for p in json.load(sys.stdin)["result"]["panes"]:
    if p.get("label") == sys.argv[1]: print(p["pane_id"]); break' "$1"; }

# --- 2. layout ---------------------------------------------------------------
M=$(pane_by_label master)
if [ -z "$M" ]; then
    echo "==> building layout"
    M=$($H workspace create --cwd "$PAPER" --label ralph | jget '["result"]["root_pane"]["pane_id"]')
    $H pane rename "$M" master >/dev/null
    E=$($H pane split "$M" --direction down --ratio 0.55 --cwd "$PAPER" --no-focus | jget '["result"]["pane"]["pane_id"]')
    $H pane rename "$E" experiment >/dev/null
    W=$($H pane split "$E" --direction right --ratio 0.5 --cwd "$PAPER" --no-focus | jget '["result"]["pane"]["pane_id"]')
    $H pane rename "$W" writing >/dev/null
else
    echo "==> layout exists"
fi

# --- 3. agents ---------------------------------------------------------------
if [ "$MODE" != "none" ]; then
    running=$($H agent list | python3 -c 'import json,sys; print(" ".join(a.get("name","") for a in json.load(sys.stdin)["result"]["agents"]))')
    for role in master experiment writing; do
        case " $running " in *" $role "*) echo "==> $role already running"; continue;; esac
        P=$(pane_by_label "$role")
        echo "==> starting $role in pane $P"
        if [ "$MODE" = resume ]; then
            $H agent start "$role" --kind claude --pane "$P" --timeout 60000 -- --continue || true
        else
            $H agent start "$role" --kind claude --pane "$P" --timeout 60000 -- --permission-mode acceptEdits \
                "You are $role. Read CLAUDE.md, then harness/$role.md, then HVI-PLAN.md, and begin your opening sequence. The human is asynchronous: never wait for input." || true
        fi
    done
fi
echo "==> attach with: herdr --session $SESSION    (ctrl+b q to detach)"
$H agent list | python3 -c '
import json, sys
agents = json.load(sys.stdin)["result"]["agents"]
print("  agents running: " + (", ".join(str(a.get("name")) + "@" + str(a.get("pane_id")) + "(" + str(a.get("status") or a.get("agent_status")) + ")" for a in agents) or "none"))'
python3 "$PAPER/herdr/herdr_sync.py" status 2>/dev/null | head -6
