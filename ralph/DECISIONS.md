# DECISIONS.md — every decision, one line, with the why

Format: `<ISO time> | <who> | <decision> | <why> | <evidence path>`
Gate verdicts: `GATE <name>: PASS|FAIL|PIVOT-x`. Human answers carry `[human]`.

2026-09-24T17:00 | scaffold | Adopt writing-driven-autoresearch harness; ICML template, English; repo github.com/Limtriangle/paper; herdr 3-pane topology | author's choice | CLAUDE.md
2026-09-24T17:00 | scaffold | Repo lives in /home/work/research/paper with /home/work/paper as symlink | /home/work is wiped on session end; research/ is the persistent vfolder | bootstrap.sh
2026-09-24T17:00 | scaffold | verify-phm.py is spec-driven (ralph/phm-spec.json), not hardcoded | upstream hardcoded Depth-AR keys; a spec keeps rule 6 (verify by key) without editing the tool per claim | tooling/verify-phm.py
2026-09-24T18:00 | [human] | Discard the earlier studies (loss ablation / width / prefilter) and their exported results; choose the thesis topic from scratch, HVI-CIDNet related | author's decision | HVI-PLAN.md §Phase 0
2026-09-24T18:00 | scaffold | Gate 0 (topic) is the one gate the author calls; team does instrument work only until then | the topic is the author's, and idle GPUs must not tempt the team into an unplanned study | HVI-PLAN.md §5
2026-09-23T18:00 | master | herdr topology installed from herdr/topology.json; permission mode live; watcher under Monitor | workers hang on prompts without it | herdr/permission-policy.md
2026-09-23T18:02 | master | Approved writing's read-only `cat`/`ls` over writing/ + ralph/ (classifier false positive on shell expansion) | policy: auto-approve reads inside project dirs | herdr/permission-policy.md
2026-09-23T18:05 | master | Phase 0 dispatch: experiment → phase0_codebase.json + 1-epoch LOLv1 smoke on GPU 0 + export ingest + cost.smoke; writing → phase0_related.md + verified custom.bib; master → candidates after both land | plan §Phase 0 steps 1–3; instrument work only until Gate 0 | HVI-PLAN.md §Phase 0
2026-09-23T18:12 | master | Approved writing's WebFetch of arxiv.org (bib verification); will approve DBLP/Semantic Scholar/arXiv reads on sight, plain Yes only | citation verification is required by integrity floor rule 5; a fetch is a read, not an install | herdr/permission-policy.md
2026-09-23T18:40 | master | phase0_candidates.md v1 written (C1–C6, ranked); recommendation C1 (+C2, +C5, pivot C3) posted to INBOX | plan §Phase 0 steps 2–3; drafted before phase0_codebase.json to save wall-clock, hours to be reconciled when cost.smoke lands | ralph/phase0_candidates.md
