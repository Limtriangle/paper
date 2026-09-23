# STATUS.md — master's dashboard

**Phase:** 0 — topic selection. Team launched 2026-09-23 18:00 in herdr session `ralph`. `HVI-PLAN.md` §0 is empty; no study runs.

## Gates
| Gate | State | Evidence |
|---|---|---|
| 0 — topic (author's call) | open | needs ralph/results/phase0_codebase.json (experiment), ralph/phase0_related.md (writing), ralph/phase0_candidates.md (master), then `[human] topic confirmed: <#>` in INBOX.md |
| A — instrument | pending | smoke run under the run-dir convention + export ingest; can be satisfied during Phase 0 |
| B / C | undefined until Gate 0 | |
| D — final | pending | |

## Agents
| Agent | Doing | Since |
|---|---|---|
| master | opening sequence done; watcher live; 3 subagents scouting (upstream code, literature gap, writing rules) to draft `ralph/phase0_candidates.md` | 2026-09-23 18:05 |
| experiment | phase0_codebase.json + 1-epoch smoke run on GPU 0 (LOLv1) + export ingest + cost.smoke | 2026-09-23 18:05 |
| writing | phase0_related.md + verified custom.bib; skeleton stays green | 2026-09-23 18:05 |

## Next actions
- master: when phase0_codebase.json and phase0_related.md exist → write phase0_candidates.md (4–6 candidates, ranked) → INBOX recommendation → wait for `[human] topic confirmed` (only thing that waits). Meanwhile keep workers on instrument work; sweep every ~30 min.
- experiment: after the smoke run, validate export_results.py + verify-phm.py by planting a wrong number (rule 9), then nothing else until Gate 0.
- writing: after phase0_related.md, prepare the related-work appendix prose (no claims) and the gen-table spec scaffolding.

## Log
- 2026-09-23 scaffold created; project reset to Phase 0 (topic to be chosen from scratch, HVI-CIDNet related).
- 2026-09-23 18:00 master opening sequence: topology installed to ~/.config/herdr-mgr, permission mode live, watcher armed, both workers dispatched with Phase 0 tasks.
