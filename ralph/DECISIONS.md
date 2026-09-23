# DECISIONS.md — every decision, one line, with the why

Format: `<ISO time> | <who> | <decision> | <why> | <evidence path>`
Gate verdicts: `GATE <name>: PASS|FAIL|PIVOT-x`. Human answers carry `[human]`.

2026-09-24T17:00 | scaffold | Adopt writing-driven-autoresearch harness; ICML template, English; repo github.com/Limtriangle/paper; herdr 3-pane topology | author's choice | CLAUDE.md
2026-09-24T17:00 | scaffold | Repo lives in /home/work/research/paper with /home/work/paper as symlink | /home/work is wiped on session end; research/ is the persistent vfolder | bootstrap.sh
2026-09-24T17:00 | scaffold | verify-phm.py is spec-driven (ralph/phm-spec.json), not hardcoded | upstream hardcoded Depth-AR keys; a spec keeps rule 6 (verify by key) without editing the tool per claim | tooling/verify-phm.py
2026-09-24T18:00 | [human] | Discard the earlier studies (loss ablation / width / prefilter) and their exported results; choose the thesis topic from scratch, HVI-CIDNet related | author's decision | HVI-PLAN.md §Phase 0
2026-09-24T18:00 | scaffold | Gate 0 (topic) is the one gate the author calls; team does instrument work only until then | the topic is the author's, and idle GPUs must not tempt the team into an unplanned study | HVI-PLAN.md §5
