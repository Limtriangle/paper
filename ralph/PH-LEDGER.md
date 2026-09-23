# PH-LEDGER — every provisional value in the paper, and what it waits on

**Owner:** `writing`. Regenerate the measured half with `python3 tooling/verify-phm.py --ledger`.
List the invented half with `grep -rnoE '\\ph\{[^}]*\}' writing/section writing/tables`.

| Macro | Meaning | Rule at the milestone audit |
|---|---|---|
| `\ph{}` | **INVENTED.** No measurement exists. | Land the real number (→ `\phm{}` + spec entry) or **delete the sentence**. |
| `\phm{}` | **MEASURED.** `ralph/phm-spec.json` binds it to a JSON key. | Verified by key; **unwrap** at the end (`tooling/unwrap-phm.sh`). Never delete. |

## `\ph{}` — invented, waiting on

*(none — Phase 0, no claims yet)*

## `\phm{}` — measured (from `verify-phm.py --ledger`)

*(none)*
