# DECISIONS.md — every decision, one line, with the why

Format: `<ISO time> | <who> | <decision> | <why> | <evidence path>`
Gate verdicts: `GATE <name>: PASS|FAIL|PIVOT-x`. Human answers carry `[human]`.

2026-09-24T17:00 | scaffold | Adopt writing-driven-autoresearch harness; ICML template, English; repo github.com/Limtriangle/paper; herdr 3-pane topology | author's choice | HVI-PLAN.md
2026-09-24T17:00 | scaffold | Repo lives in /home/work/research/paper with /home/work/paper as symlink | /home/work is wiped on session end; research/ is the persistent vfolder | bootstrap.sh
2026-09-24T17:00 | scaffold | Thesis framed as a controlled study of the HVI-CIDNet recipe (S1 loss ablation, S2 width, S3 prefilter) | that is what the existing scripts measure; flagged [CONFIRM] in the plan | HVI-PLAN.md §0
2026-09-24T17:00 | scaffold | verify-phm.py is spec-driven (ralph/phm-spec.json), not hardcoded | upstream hardcoded Depth-AR keys; a spec keeps rule 6 (verify by key) without editing the tool per claim | tooling/verify-phm.py
