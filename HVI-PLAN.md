# HVI-PLAN.md — project spec (the source of truth)

> Status: **PHASE 0 — topic not yet chosen.** Scope: a bachelor's thesis paper related to
> HVI-CIDNet (Yan et al., CVPR 2025: low-light enhancement in the HVI color space). ICML
> format, English, 4-page body + appendix. Until §0 is filled and the author has written
> `[human] topic confirmed` in `ralph/INBOX.md`, nothing in §4–§8 is binding and no study
> runs.

## 0. The one question

*(empty — filled at Gate 0)*

TL;DR (one sentence, guidelines §3.1): *(empty)*

## Phase 0 — how the topic gets chosen

Owner: `master`, with the author. Output: §0, §4, §5, §6, §8 of this file, written
**before** any experiment runs (the upstream method: generate the plan first, with a paper
story for every outcome, then run).

1. **Ground truth first.** `experiment` reads the upstream code and reports, as a file
   (`ralph/results/phase0_codebase.json`), what HVI-CIDNet actually does: the HVI transform,
   the two-branch architecture, the loss terms and weights, the training protocol in the
   repo's configs, the datasets its README uses, the released checkpoints, and what one
   training run costs on one RTX 2080 Ti (measured with a 1-epoch smoke run). `writing`
   reads the HVI-CIDNet paper and its closest related work and writes
   `ralph/phase0_related.md`: what the paper claims, what it ablates, what it leaves open.
2. **Candidate questions.** `master` writes 4–6 candidates in `ralph/phase0_candidates.md`.
   Each candidate has: the one-sentence question; why it is open (cite the gap from step 1);
   the claim we would make if it works; the claim we would make if it fails (a negative
   result must still be a thesis); the minimal experiment that decides it; its GPU cost in
   2080 Ti-hours against the ~4-GPU budget; and the risk that the answer is trivial.
   Candidate families worth considering (not a list to copy): color-space design
   (what the HVI transform buys over HSV/LAB/YCbCr under an identical network), the
   dual-space objective (which terms matter, with seed spread), robustness (noise, JPEG,
   real-world unpaired data, other datasets), efficiency (width/depth/latency trade-off on
   consumer GPUs), failure modes of the polar chroma mapping near black, or a targeted
   modification with a pre-registered success criterion.
3. **Recommendation.** `master` ranks them by (decidability with our compute) × (size of the
   open gap) × (survives a negative result), writes the ranking and the recommended pick
   into `ralph/INBOX.md` under `## Open questions`, and logs it in DECISIONS.md.
4. **Gate 0 — the author's call.** The author edits INBOX.md: `[human] topic confirmed: <#>`
   (or names a different one). Master then fills §0–§8 below, `writing` writes the full
   4-page draft with `\ph{}` values, `experiment` writes the study scripts. Only then does
   Gate A open.

While Phase 0 is open, `experiment` may only do **instrument work**: make the upstream repo
train and evaluate end to end (1-epoch smoke run, one GPU), fix the run-directory convention
so `tooling/export_results.py` ingests it, and measure cost. `writing` keeps the skeleton
compiling and prepares the related-work appendix and the verified bibliography.

## 1. Rules of claim (from writing-guidelines §2 and the integrity floor)

- Assertive in framing, never in facts. No SOTA, no "first", no "significant" without a
  number and a spread.
- Every number in the paper is a `\phm{}` bound to a JSON key, or it is deleted.
- A difference smaller than the seed-to-seed sample SD is reported as *no measurable
  difference*, with the spread. Never by sign. Three seeds before any mean is cited.
- Checkpoint selection by validation only. The test split is read once, by one script, at
  the end, and the table that reports it says so.

## 2. Run-directory convention (what `export_results.py` expects)

```
/home/work/research/outputs/<study>/<run>/manifest.json        protocol + script sha256 + upstream commit + split sha256
/home/work/research/outputs/<study>/<run>/<job>/config.json     variant, seed, width, weights, gpu, torch, "test": "NEVER READ"
/home/work/research/outputs/<study>/<run>/<job>/status.json     {"state": "running"|"complete"|"failed"}
/home/work/research/outputs/<study>/<run>/<job>/metrics.csv     per-epoch: epoch, loss, val_psnr, ...
/home/work/research/outputs/<study>/<run>/<job>/validation_summary.csv   rows checkpoint=best|last, metric columns
```
Jobs never overwrite or resume in place (`mkdir(exist_ok=False)`). A protocol change is a
new script hash and a new run name.

## 3. Frozen protocol

*(empty — fixed at Gate 0 from the upstream configs plus whatever the question needs.
Defaults inherited from the upstream repo unless the plan says otherwise: its dataset
splits, crop size, batch size, optimizer, schedule, and loss weights; FP32 on RTX 2080 Ti.)*

## 4. Studies and claims

*(empty — each claim is written first; the experiment exists to support or refute it.)*

## 5. Gates

| Gate | Needs | PASS default | FAIL default |
|---|---|---|---|
| **0 — topic** | `phase0_codebase.json`, `phase0_related.md`, `phase0_candidates.md`, `[human] topic confirmed` in INBOX.md | fill §0–§8; open Gate A | — (the author decides) |
| **A — instrument** | upstream trains + evaluates end to end; export ingests the smoke run; protocol hash pinned | launch the first study | fix the instrument; nothing else runs |
| **B / C** | *(set at Gate 0)* | | |
| **D — final** | final-eval JSON; `verify-phm.py` 0 unbacked; `writing-audit.sh --final` PASS | submit-ready | delete unbacked claims; submit-ready |

## 6. Storyline

*(empty — five moves: background, problem, approach, results, conclusion; intro follows the
style guide's 7-move arc; lead figure is a results figure.)*

## 7. Provisional values (for `\ph{}` only)

*(empty)*

## 8. Pivots (pre-committed; master logs which one fired)

*(empty — one pivot per outcome of each study, including "no effect" and "budget runs
out". A negative result with three seeds is a thesis.)*
