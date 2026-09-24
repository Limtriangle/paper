# STATUS.md — master's dashboard

**Phase:** 0 — topic selection. The author's method criteria (INBOX line 18) produced M1–M5 and T1–T6; red-teams R3–R6 rejected T1, T3, T4, T6 as methods; the fine-tune loop was built and found valid only for release-compatible components. **Current recommendation: the C1 nested ladder (Part II) + T3's zero-training oracle-decomposition chapter.** **Gate 0 still waits for the author.**

## Gates
| Gate | State | Evidence |
|---|---|---|
| 0 — topic (author's call) | open | needs ralph/results/phase0_codebase.json (experiment), ralph/phase0_related.md (writing), ralph/phase0_candidates.md (master), then `[human] topic confirmed: <#>` in INBOX.md |
| A — instrument | READY: smoke exported, rule-9 audit green, test guard (open+list) green, scene split, 7 arms preflight green; verdict stamped at Gate 0 with the protocol hash | ralph/results/baseline__smoke_v1.json |
| B / C | undefined until Gate 0 | |
| D — final | pending | |

## Agents
| Agent | Doing | Since |
|---|---|---|
| master | Candidates v10: C1 ladder first again (+ T3 oracle-decomposition chapter), T1/T3/T4/T6 rejected as methods by R3–R6; recommendation in INBOX; **Gate 0 waits for the author**; scratch A0/A2 ≈ 4.5 h left | 2026-09-24 03:50 UTC |
| writing | ALL Phase 0 work done (ff56879: check/audit fail on missing src, custom.bib 112 verified, related.md §5, appendix). **Holding for Gate 0.** Build + audit green | 2026-09-23 23:35 UTC |

## Next actions
- Candidates v10 posted (recommend C1 ladder + optional T3 chapter); Gate 0 waits for `[human] topic confirmed: <#>`. Experiment: fine-tune loop + ranking check (4 runs). Writing holds.
- master: Gate 0 open, waiting for `[human] topic confirmed: <#>` in INBOX (the only wait). On confirmation: fill HVI-PLAN.md §0–§8 from phase0_candidates.md + phase0_codebase.json, then dispatch the post-Gate-0 openings. Meanwhile: reconcile candidate hours with cost.smoke; keep workers on instrument work; sweep every ~30 min.
- experiment: after the smoke run, validate export_results.py + verify-phm.py by planting a wrong number (rule 9), then nothing else until Gate 0.
- writing (after reset): make `gen-table.py --check` exit nonzero on a MISSING src unless `--allow-missing`; make `writing-audit.sh --final` fail on any MISSING src or `--` cell in an \input'd table; then finish the 12 comparator bib verifications. Earlier dispatch (done except bib):  (a) correct phase0_related.md §1.3 + gap 5 against phase0_codebase.json — VGG perceptual applies range_norm x→(x+1)/2 before ImageNet normalisation, so H,V land in [0,1] and RGB in [0.5,1]; the oddity is RGB-side. (b) Every uncited claim in phase0_related.md gets a verified bib key or an explicit "unverified" mark (24.7401 on RTX 4070; FusionNet as NTIRE 2025 winner; Bread, SwinIR, GLARE, FourLLIE, BRISQUE, Mamba; DICM/LIME/MEF/NPE/VV). (c) Note in §3 that the old paper's "k sits in the inverse" contradicts the code (no gradient through the inverse). Then instrument work only: related-work appendix prose in writing/section/related_works.tex (verified keys only, no claims); scaffold writing/tables/spec.json for C1 (rows sRGB/HSV/YCbCr/HVI-noCk/HVI; columns PSNR, SSIM, LPIPS, CIEDE2000 as mean±SD over 3 seeds, ungated primary; second table gated + GT-mean) pointing at not-yet-existing keys so gen-table.py --check reports missing instead of crashing; build + audit green; commit; push; report paths + one line.

## Log
- 2026-09-23 22:45 UTC reset wake-up: no Gate 0 answer; author's survey (ralph/related/) + red-team confirmation in INBOX; workers resumed on Next actions.
- 2026-09-23 19:25 UTC Claude Code session limit at 96%, resets 22:40 UTC. Workers commit early and hold; master sweeps cheaply. Resume after reset: writing → corrections + appendix + C1 spec scaffold (Next actions); experiment → scene-disjoint split + arm wiring (Next actions); master → wait for Gate 0.
- 2026-09-23 18:45 UTC comms outage found and fixed: herdr_sync `send` used a nonexistent subcommand; no master text reached workers until now (they ran on personas). Approvals were unaffected. Timestamps in DECISIONS before this point were estimates ~1 h ahead of the clock.
- 2026-09-23 scaffold created; project reset to Phase 0 (topic to be chosen from scratch, HVI-CIDNet related).
- 2026-09-23 19:45 experiment delivered phase0_codebase.json + 4 instrument runs (smoke, 2 determinism replicates, strict smoke). Cost: 26.2 s/epoch, 9.1 h per 1000-epoch run, 9.8 GiB peak. Candidates v2 with reconciled hours.
- 2026-09-23 18:40 master: phase0_candidates.md v1 (C1–C6) + INBOX recommendation (C1, pivot C3). Gate 0 now waits for the author.
- 2026-09-23 18:00 master opening sequence: topology installed to ~/.config/herdr-mgr, permission mode live, watcher armed, both workers dispatched with Phase 0 tasks.
