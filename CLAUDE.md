# CLAUDE.md — orchestration root

This directory (`/home/work/paper`, physically `/home/work/research/paper`) is the
**orchestration root** for a writing-driven, three-agent research loop that produces a
bachelor's thesis paper (ICML format, English) on **HVI-CIDNet low-light image
enhancement** — the dual-space (RGB + HVI) loss, model width, and input prefilter studies
already running in `/home/work/research`.

**`HVI-PLAN.md` is the spec.** Read it before any research or writing decision. It holds the
research question, the claims, the gates, the pre-committed pivots for every outcome
(including negative ones), and the paper storyline. The persona files under `harness/` are
the operating manuals; the plan is the source of truth.

The method is adapted from
[writing-driven-autoresearch](https://github.com/happyhappy-jun/writing-driven-autoresearch)
(Ralphthon@ICML 2026 winner). Its original personas and tooling are kept verbatim under
`harness/upstream/` for reference; **do not run those** — they hardcode another project.

## The three agents

Each runs as a Claude Code pane in the herdr session `ralph`, all with cwd `/home/work/paper`.
Read the persona file for whichever role you are before doing anything.

| Agent | Persona | Owns | Never touches |
|---|---|---|---|
| `master` | `harness/master.md` | gates, decisions, shared state (`ralph/`), the audit | doesn't run experiments or edit LaTeX |
| `experiment` | `harness/experiment.md` | `auto-research/`, `/home/work/research/`, all 4 GPUs, all training/eval, `ralph/results/*.json`, `writing/figures/*.pdf` | `writing/**/*.tex` — not one character |
| `writing` | `harness/writing.md` | `writing/` (all `.tex`, `.bib`, captions, the build), `ralph/PH-LEDGER.md` | never runs a model or touches a GPU |

Also read: `harness/writing-guidelines.md` (process), `harness/writing-style-guide.md` (form).

**The human is asynchronous.** The author (Byungjun's harness said "there is no human"; here
there is one, but they are not watching). They read `ralph/DECISIONS.md` and `ralph/STATUS.md`
and answer through `ralph/INBOX.md`. **Never call `AskUserQuestion`; never end a turn waiting
for input.** Apply the pre-committed default from your persona or the plan, log the decision
with its reason in `ralph/DECISIONS.md`, and keep moving. If a question truly needs the human,
write it under `## Open questions` in `ralph/INBOX.md` and continue with something else.

## Shared state — the contract between agents

Everything crossing an agent boundary goes through a **file**, never through chat.

```
ralph/STATUS.md        phase, gates, what each agent is doing        (master writes)
ralph/DECISIONS.md     every decision + why, timestamped             (master writes; others append proposals)
ralph/RESULTS.md       one row per completed run -> its JSON         (experiment appends)
ralph/INBOX.md         human <-> agents: open questions, answers     (anyone appends)
ralph/PH-LEDGER.md     every \ph / \phm value and what backs it      (writing writes)
ralph/phm-spec.json    machine-readable \phm -> JSON-key binding     (writing writes, verify-phm.py reads)
ralph/results/*.json   experiment output                             (experiment writes; writing READS DIRECTLY)
```

**`writing` reads result JSON from disk, never a number relayed through chat.** Numbers get
corrupted every time they are retyped; the file is the truth. Never invent, round in your
favor, or quietly retry a disappointing number — a measured negative result is a **success**
here (the plan has a pivot for it).

## Commands

```bash
bash tooling/build-writing.sh          # writing/ -> writing-main.pdf (tectonic)
bash tooling/writing-audit.sh          # definition-of-done as code; --final also fails on any \ph{}
python3 tooling/verify-phm.py          # every \phm{} verified BY KEY against ralph/results/*.json
python3 tooling/gen-table.py --check   # tables regenerated from JSON, never typed; --write to apply
bash tooling/unwrap-phm.sh --dry       # \phm{X} -> X, purity-checked; --apply to do it
python3 tooling/export_results.py      # /home/work/research/outputs/** -> ralph/results/*.json
bash tooling/status.sh                 # phase, git state, result counts, GPU occupancy
python3 herdr/herdr_sync.py status     # who is idle / working / blocked
python3 herdr/herdr_sync.py send <agent> "<one line>"
```

## Hardware reality

- **This host (main1)**: 4× NVIDIA GeForce RTX 2080 Ti, 11 GB each, `sm_75`, **no bf16**,
  FP32 training is the protocol. 15 CPU cores, 125 GB RAM. CUDA 12.8 toolkit.
- Python: `/home/work/research/env/hvi` (venv over the NGC system torch 2.7). It is
  activated by `paper/env.sh` (sourced from `~/.bashrc`).
- **No sudo. No SLURM.** `experiment` assigns GPUs itself via explicit `CUDA_VISIBLE_DEVICES`
  per job; at most one training job per GPU.
- **`/home/work` is ephemeral** (wiped when the compute session ends). Only
  `/home/work/research` persists. This repo, the Claude config, and every tool live there;
  `bash /home/work/research/paper/bootstrap.sh` restores the links after a reset.
- No Overleaf. The paper repo is `git@github.com:Limtriangle/paper.git`, branch `main`.

## The integrity floor — not negotiable, not tradeable for time

1. Provisional numbers live only inside `\ph{}` in the LaTeX source. **A `\ph{}` value never
   ships as measured.** Either the real number lands (and the wrapper becomes `\phm{}` bound
   to a JSON key in `ralph/phm-spec.json`), or the sentence is deleted.
2. `\phm{}` = measured. Every one is verified **by key, never by value** with
   `tooling/verify-phm.py`. Unwrap only after it passes.
3. Tables are generated by `tooling/gen-table.py` from result JSON and never hand-edited.
   Bold marks the best value per column whoever attains it — typography is a claim.
4. The test split (`test15`) is **never read** by any training or selection code. Every job
   config carries `"test15": "NEVER READ"`; a run that violates this is discarded.
5. No hallucinated citations. A BibTeX entry that cannot be verified is cut.
6. Never `git push --force`, never `git reset --hard`. The history is the audit trail.
