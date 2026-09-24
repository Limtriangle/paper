# STATUS.md — master's dashboard

**Phase:** 1 — **Gate 0 PASSED 2026-09-24 04:51 UTC** (INBOX line 29): thesis = C1 nested HVI representation ladder + loss ladder, advisor framing "under which conditions and by how much does HVI-CIDNet's effect reproduce". Plan §0–§8 filled. **Gate A open:** A0 × 5 seeds under the full upstream loss must reproduce raw 23.3–24.3 dB with σ ≤ 0.5 before any other arm.

## Gates
| Gate | State | Evidence |
|---|---|---|
| 0 — topic | **PASS** 2026-09-24 04:51 UTC | INBOX line 29 |
| A — instrument + reproduction | **OPEN, launched** | A0-L0 seeds 42–46 from scratch; verdict = mean raw eval15 PSNR ∈ [23.3, 24.3] and σ ≤ 0.5 |
| B — loss ladder S1 (25 runs) | pending | HVI-PLAN.md §4–§5 |
| C — representation ladder S2 (20 runs) | pending | HVI-PLAN.md §4–§5 |
| D — final | pending | |

## Agents
| Agent | Doing | Since |
|---|---|---|
| master | Plan filled and committed; Gate A launched; both workers dispatched per §Opening; sweeping every 30 min while jobs run | 2026-09-24 05:05 UTC |
| writing | ALL Phase 0 work done (ff56879: check/audit fail on missing src, custom.bib 112 verified, related.md §5, appendix). **Holding for Gate 0.** Build + audit green | 2026-09-23 23:35 UTC |

## Next actions
- master: sweep every 30 min; call Gate A when the five A0-L0 final-eval JSONs exist; then dispatch S1/S2 waves of 4 (order: L1, L2, L3, L4 seeds first, then A1–A4); audit writing's draft before the first milestone push.
- experiment: Gate A runs; keep GPUs full (one job each); export on completion; never read eval15 outside final_eval_test.py.
- writing: draft → build green → commit → push; then the gen-table specs for S1/S2/S3 tables pointing at the not-yet-existing keys.

## Log
- 2026-09-24 04:51 UTC GATE 0 PASS (author). 05:05 plan filled, Gate A launched, workers dispatched.
- 2026-09-23 22:45 UTC reset wake-up: no Gate 0 answer; author's survey (ralph/related/) + red-team confirmation in INBOX; workers resumed on Next actions.
- 2026-09-23 19:25 UTC Claude Code session limit at 96%, resets 22:40 UTC. Workers commit early and hold; master sweeps cheaply. Resume after reset: writing → corrections + appendix + C1 spec scaffold (Next actions); experiment → scene-disjoint split + arm wiring (Next actions); master → wait for Gate 0.
- 2026-09-23 18:45 UTC comms outage found and fixed: herdr_sync `send` used a nonexistent subcommand; no master text reached workers until now (they ran on personas). Approvals were unaffected. Timestamps in DECISIONS before this point were estimates ~1 h ahead of the clock.
- 2026-09-23 scaffold created; project reset to Phase 0 (topic to be chosen from scratch, HVI-CIDNet related).
- 2026-09-23 19:45 experiment delivered phase0_codebase.json + 4 instrument runs (smoke, 2 determinism replicates, strict smoke). Cost: 26.2 s/epoch, 9.1 h per 1000-epoch run, 9.8 GiB peak. Candidates v2 with reconciled hours.
- 2026-09-23 18:40 master: phase0_candidates.md v1 (C1–C6) + INBOX recommendation (C1, pivot C3). Gate 0 now waits for the author.
- 2026-09-23 18:00 master opening sequence: topology installed to ~/.config/herdr-mgr, permission mode live, watcher armed, both workers dispatched with Phase 0 tasks.
