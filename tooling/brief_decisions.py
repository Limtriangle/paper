#!/usr/bin/env python3
"""List every DECISIONS.md line taken while the author was away (from 2026-09-25T20:30 UTC), for ralph/AUTHOR_BRIEF.md §6."""
import re, sys
START = "2026-09-25T20:30"
lines = [l.rstrip("\n") for l in open("ralph/DECISIONS.md", encoding="utf-8") if re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2} \|", l)]
out = [l for l in lines if l[:16] >= START]
who = lambda l: l.split(" | ")[1].strip()
print(f"{len(out)} decisions since {START} UTC ({sum(1 for l in out if who(l)=='master')} by master, {sum(1 for l in out if who(l).startswith('[human'))} human notes)")
for l in out:
    ts, w, decision = l.split(" | ")[0], who(l), l.split(" | ")[2]
    print(f"- {ts} [{w}] {decision[:220]}{'…' if len(decision)>220 else ''}")
