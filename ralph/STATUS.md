# STATUS.md — master's dashboard

**Phase:** 0 — topic selection. **All Phase 0 inputs exist** (codebase JSON, related.md, candidates.md). **Gate 0 waits for the author** (`[human] topic confirmed: <#>` in INBOX.md). No study runs; GPUs idle by design.

## Gates
| Gate | State | Evidence |
|---|---|---|
| 0 — topic (author's call) | open | needs ralph/results/phase0_codebase.json (experiment), ralph/phase0_related.md (writing), ralph/phase0_candidates.md (master), then `[human] topic confirmed: <#>` in INBOX.md |
| A — instrument | ready: smoke exported, rule-9 audit green, test guard (open+list) green, adapters lossless; verdict stamped at Gate 0 with the protocol hash | ralph/results/baseline__smoke_v1.json |
| B / C | undefined until Gate 0 | |
| D — final | pending | |

## Agents
| Agent | Doing | Since |
|---|---|---|
| master | candidates C1–C6 written and ranked; recommendation C1 in INBOX; **Gate 0 waits for the author**; sweeping, judging prompts, reconciling hours when cost.smoke lands | 2026-09-23 18:40 |
| experiment | Phase 0 deliverables DONE (phase0_codebase.json, smoke + export green, rule-9 audit green, cost 9.1 h/run). Adapters + listing guard delivered (commit 0f0ed67). **Holding until Gate 0.** All 4 GPUs idle by design | 2026-09-23 19:20 UTC |
| writing | Phase 0 deliverables DONE (phase0_related.md, custom.bib 28 verified, pushed 2042e4f). Next: related-work appendix prose (no claims) + gen-table spec scaffold for C1 | 2026-09-23 19:45 UTC |

## Next actions
- master: Gate 0 open, waiting for `[human] topic confirmed: <#>` in INBOX (the only wait). On confirmation: fill HVI-PLAN.md §0–§8 from phase0_candidates.md + phase0_codebase.json, then dispatch the post-Gate-0 openings. Meanwhile: reconcile candidate hours with cost.smoke; keep workers on instrument work; sweep every ~30 min.
- experiment: after the smoke run, validate export_results.py + verify-phm.py by planting a wrong number (rule 9), then nothing else until Gate 0.
- writing (dispatched 2026-09-23 ~20:10 UTC, also sent by pane): (a) correct phase0_related.md §1.3 + gap 5 against phase0_codebase.json — VGG perceptual applies range_norm x→(x+1)/2 before ImageNet normalisation, so H,V land in [0,1] and RGB in [0.5,1]; the oddity is RGB-side. (b) Every uncited claim in phase0_related.md gets a verified bib key or an explicit "unverified" mark (24.7401 on RTX 4070; FusionNet as NTIRE 2025 winner; Bread, SwinIR, GLARE, FourLLIE, BRISQUE, Mamba; DICM/LIME/MEF/NPE/VV). (c) Note in §3 that the old paper's "k sits in the inverse" contradicts the code (no gradient through the inverse). Then instrument work only: related-work appendix prose in writing/section/related_works.tex (verified keys only, no claims); scaffold writing/tables/spec.json for C1 (rows sRGB/HSV/YCbCr/HVI-noCk/HVI; columns PSNR, SSIM, LPIPS, CIEDE2000 as mean±SD over 3 seeds, ungated primary; second table gated + GT-mean) pointing at not-yet-existing keys so gen-table.py --check reports missing instead of crashing; build + audit green; commit; push; report paths + one line.

## Log
- 2026-09-23 18:45 UTC comms outage found and fixed: herdr_sync `send` used a nonexistent subcommand; no master text reached workers until now (they ran on personas). Approvals were unaffected. Timestamps in DECISIONS before this point were estimates ~1 h ahead of the clock.
- 2026-09-23 scaffold created; project reset to Phase 0 (topic to be chosen from scratch, HVI-CIDNet related).
- 2026-09-23 19:45 experiment delivered phase0_codebase.json + 4 instrument runs (smoke, 2 determinism replicates, strict smoke). Cost: 26.2 s/epoch, 9.1 h per 1000-epoch run, 9.8 GiB peak. Candidates v2 with reconciled hours.
- 2026-09-23 18:40 master: phase0_candidates.md v1 (C1–C6) + INBOX recommendation (C1, pivot C3). Gate 0 now waits for the author.
- 2026-09-23 18:00 master opening sequence: topology installed to ~/.config/herdr-mgr, permission mode live, watcher armed, both workers dispatched with Phase 0 tasks.
