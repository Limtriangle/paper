# permission-policy.md — how master judges workers' permission prompts

Read before every `approve` / `deny`. Mode: `python3 herdr/herdr_sync.py mode` (start in
`dryrun`, switch to `live` once the first few judgments look right).

## In-scope project dirs
- `/home/work/paper` (= `/home/work/research/paper`)
- `/home/work/research` (studies, outputs, datasets, venv)

## AUTO-APPROVE (plain "Yes", never "don't ask again")
- Any read (`cat`, `ls`, `grep`, `find`, `head`, `python3 -c` that only prints) anywhere under the in-scope dirs.
- Edits/writes inside the agent's own territory (CLAUDE.md ownership table).
- `bash tooling/*.sh`, `python3 tooling/*.py`, `python3 herdr/herdr_sync.py …`.
- `git add/commit/pull --rebase/push` in `/home/work/paper` (writing only).
- `nvidia-smi`, `CUDA_VISIBLE_DEVICES=N python3 auto-research/*.py …` (experiment only).
- `tectonic`, `uv`, `pip install` into the venv.
- Host-classifier false positives on harmless shell expansion inside read-only commands.

## ESCALATE (leave waiting, write to ralph/INBOX.md)
- Anything touching paths outside the in-scope dirs.
- `rm -r` of any `outputs/<study>/<run>` directory, or of `ralph/results/`.
- Any command that reads the test split outside `auto-research/final_eval*.py`.
- Network installs of new software not already in bootstrap.sh.

## DENY
- `git push --force`, `git reset --hard`, `git clean -fd`.
- Killing processes the agent did not launch.
- Writing under `writing/**/*.tex` by anyone but writing; under `ralph/results/` by anyone but experiment.

## AUTO-DISMISS (Escape)
- "How is Claude doing this session?" feedback prompts.

## Idle nudge
- after 20 min without output while jobs are not running: "status? if blocked, log it in DECISIONS.md and continue with the next item in STATUS.md"
