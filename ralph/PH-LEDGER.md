# PH-LEDGER — every provisional value in the paper, and what it waits on

**Owner:** `writing`. Regenerate the measured half with `python3 tooling/verify-phm.py --ledger`.
List the invented half with `grep -rnoE '\\ph\{[^}]*\}' writing/section writing/tables`.

| Macro | Meaning | Rule at the milestone audit |
|---|---|---|
| `\ph{}` | **INVENTED.** No measurement exists. | Land the real number (→ `\phm{}` + spec entry) or **delete the sentence**. |
| `\phm{}` | **MEASURED.** `ralph/phm-spec.json` binds it to a JSON key. | Verified by key; **unwrap** at the end (`tooling/unwrap-phm.sh`). Never delete. |

## `\ph{}` — invented, waiting on

| value | file | waits on |
|---|---|---|
| 0.3 dB, 0.02 LPIPS (NO_PERC_HVI vs FULL) | abstract, introduction, experiments, conclusion | S1 analysis JSON, 3 seeds |
| 0.6 dB, 0.03 LPIPS, 4× params (W18→W36) | abstract, introduction, experiments, conclusion | S2 analysis JSON, 3 seeds (params key exists already) |
| 0.1 dB (W30→W36, other HVI terms) | experiments | S2 / S1 analysis |
| 0.2 dB seed SD at W18 | experiments | S2 analysis, 3 seeds |
| 0.4 dB (RGB_ONLY vs FULL) | experiments | S1 analysis |

## `\phm{}` — measured (from `verify-phm.py --ledger`)

Tables `width_table.tex` and `prefilter_table.tex` are generated; their spec entries are
produced by `python3 tooling/gen-table.py --spec-entries` and merged into `phm-spec.json`.
