# STATUS.md — master's dashboard

**Phase:** 0 — topic selection. Team launched 2026-09-23 18:00 in herdr session `ralph`. `HVI-PLAN.md` §0 is empty; no study runs.

## Gates
| Gate | State | Evidence |
|---|---|---|
| 0 — topic (author's call) | open | needs ralph/results/phase0_codebase.json (experiment), ralph/phase0_related.md (writing), ralph/phase0_candidates.md (master), then `[human] topic confirmed: <#>` in INBOX.md |
| A — instrument | inputs exist (smoke run exported, script hash pinned); verdict deferred to Gate 0 because the protocol (val cadence, strict flag, adapters) is fixed there | ralph/results/baseline__smoke_v1.json |
| B / C | undefined until Gate 0 | |
| D — final | pending | |

## Agents
| Agent | Doing | Since |
|---|---|---|
| master | candidates C1–C6 written and ranked; recommendation C1 in INBOX; **Gate 0 waits for the author**; sweeping, judging prompts, reconciling hours when cost.smoke lands | 2026-09-23 18:40 |
| experiment | Phase 0 deliverables DONE (phase0_codebase.json, smoke + export green, cost 9.1 h/run). Now: rule-9 instrument validation + CPU-only color-space adapters for C1; no training | 2026-09-23 19:45 |
| writing | phase0_related.md + verified custom.bib; skeleton stays green | 2026-09-23 18:05 |

## Next actions
- master: Gate 0 open, waiting for `[human] topic confirmed: <#>` in INBOX (the only wait). On confirmation: fill HVI-PLAN.md §0–§8 from phase0_candidates.md + phase0_codebase.json, then dispatch the post-Gate-0 openings. Meanwhile: reconcile candidate hours with cost.smoke; keep workers on instrument work; sweep every ~30 min.
- experiment: after the smoke run, validate export_results.py + verify-phm.py by planting a wrong number (rule 9), then nothing else until Gate 0.
- writing: after phase0_related.md, prepare the related-work appendix prose (no claims) and the gen-table spec scaffolding.

## Log
- 2026-09-23 scaffold created; project reset to Phase 0 (topic to be chosen from scratch, HVI-CIDNet related).
- 2026-09-23 19:45 experiment delivered phase0_codebase.json + 4 instrument runs (smoke, 2 determinism replicates, strict smoke). Cost: 26.2 s/epoch, 9.1 h per 1000-epoch run, 9.8 GiB peak. Candidates v2 with reconciled hours.
- 2026-09-23 18:40 master: phase0_candidates.md v1 (C1–C6) + INBOX recommendation (C1, pivot C3). Gate 0 now waits for the author.
- 2026-09-23 18:00 master opening sequence: topology installed to ~/.config/herdr-mgr, permission mode live, watcher armed, both workers dispatched with Phase 0 tasks.
