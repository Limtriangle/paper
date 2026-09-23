# INBOX.md — human <-> agents

Agents append questions under **Open questions** (`- [ ]`). The author answers by editing
the line to `- [x] ... → <answer>`; master reads it on the next sweep and logs the answer
in DECISIONS.md with `[human]`. Agents never wait for an answer; they apply the plan's
default until one arrives. **Exception: Gate 0 (the topic) waits for the author.**

## Open questions
- [ ] (Gate 0) **Topic.** Candidates in `ralph/phase0_candidates.md` (six, ranked). **Master recommends C1** — *"With CIDNet, loss and protocol frozen, does training in HVI beat sRGB / HSV / YCbCr by more than the seed spread?"* — with C2 (seed variance + test-selection bias) as its built-in second study, C5 (noise/JPEG/domain robustness, eval-only) as the third, and C3 (density-k sweep + near-black failure) as the pre-committed pivot. ≈17 full runs, ~2 days on 4 GPUs. Close runner-up if you prefer a mechanism question: C3, the density-k sweep (18 runs) — k is the only learned part of HVI and has never been studied. Answer with `[human] topic confirmed: C1` (or another #, or your own question). Until then the team does instrument work only.

## Answers / notes from the author
- 2026-09-24 [human] The earlier studies are discarded. Start the topic from scratch; it must be related to HVI-CIDNet.
- 2026-09-24 [human] Top-tier literature pass done: `ralph/related/SURVEY.md` (narrative + gaps), `INDEX.md` (counts at its foot), `survey.bib`, slices A–F. writing: merge into custom.bib only after your own bibtex-verify pass; fill phase0_related.md §5 from it. master: SURVEY.md §1 maps each gap to C1–C6.
