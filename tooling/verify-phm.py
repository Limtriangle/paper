#!/usr/bin/env python3
"""Verify every \\phm{} in the paper against the result JSON key that backs it.

    python3 tooling/verify-phm.py            # exit 1 if any \\phm is unbacked or mismatched
    python3 tooling/verify-phm.py --ledger   # also print PH-LEDGER rows (markdown)

A \\phm{} claims "this number is MEASURED and a file proves it". This checks that claim,
BY KEY (never by value): the binding lives in ralph/phm-spec.json, written by `writing`:

    {"entries": [
      {"written": "21.36",
       "src":     "prefilter_study__ifilter_confirm50_v1.json",
       "key":     "jobs.B0_seed43.best.psnr",
       "only_in": ["experiments.tex"]},          # optional: restrict to these .tex files
      {"written": "$-0.04$", "src": "...__analysis.json", "key": "paired.psnr.mean_delta"}
    ]}

`key` is a dot path into the JSON (list indices are integers: "jobs.0.best.psnr").
A written value matches if, numerically, it equals the actual value rounded to the number
of decimals the paper wrote. Non-numeric written values must match str(actual) exactly.
Unlike upstream, nothing is hardcoded here: adding a claim = adding a spec entry.
"""
import json, re, sys, pathlib

PAPER = pathlib.Path(__import__("os").environ.get("PAPER", "/home/work/research/paper"))
R = PAPER / "ralph" / "results"
W = PAPER / "writing"
SPEC = PAPER / "ralph" / "phm-spec.json"

PHM_RE = re.compile(r"\\phm\{((?:[^{}]|\{[^{}]*\})*)\}")


def get(obj, path):
    for part in path.split("."):
        if isinstance(obj, list):
            obj = obj[int(part)]
        else:
            obj = obj[part]
    return obj


def parse_written(s):
    """'$-0.04$' -> -0.04 ; '21.36' -> 21.36 ; '12\\%' -> 12 ; returns (float|None, decimals)."""
    t = s.strip().replace("$", "").replace("\\%", "").replace("\\,", "").replace("+", "").replace("−", "-").replace("{", "").replace("}", "")
    t = t.replace("\\times", "").strip()
    m = re.fullmatch(r"-?\d+(?:\.(\d+))?", t)
    if not m:
        return None, None
    return float(t), (len(m.group(1)) if m.group(1) else 0)


def main():
    ledger = "--ledger" in sys.argv
    if not SPEC.exists():
        spec = {"entries": []}
    else:
        spec = json.load(open(SPEC))
    entries = spec.get("entries", [])

    # --- 1. every spec entry resolves and matches -------------------------------------
    cache, bad = {}, []
    resolved = []  # (written, src, key, actual, only_in, ok)
    for e in entries:
        src, key, written = e["src"], e["key"], e["written"]
        try:
            if src not in cache:
                cache[src] = json.load(open(R / src))
            actual = get(cache[src], key)
        except FileNotFoundError:
            bad.append(f"MISSING FILE  {src}  (for \\phm{{{written}}})"); continue
        except (KeyError, IndexError, ValueError, TypeError) as ex:
            bad.append(f"MISSING KEY   {src}:{key}  (for \\phm{{{written}}}): {ex}"); continue
        wv, dec = parse_written(written)
        if wv is None:
            ok = str(actual) == written.strip()
        else:
            try:
                ok = abs(round(float(actual), dec) - wv) < 10 ** (-dec) * 0.5001
            except (TypeError, ValueError):
                ok = False
        if not ok:
            bad.append(f"MISMATCH      \\phm{{{written}}} != {actual!r}   ({src}:{key})")
        resolved.append((written, src, key, actual, e.get("only_in"), ok))

    # --- 2. every \phm{} in the paper has a spec entry covering its file --------------
    uses = []
    for f in sorted(list((W / "section").glob("*.tex")) + list((W / "tables").glob("*.tex")) + list((W / "figures").glob("*.tex"))):
        for m in PHM_RE.finditer(f.read_text()):
            uses.append((f.name, m.group(1)))
    unbacked = []
    for fname, written in uses:
        cands = [r for r in resolved if r[0].strip() == written.strip() and (r[4] is None or fname in r[4])]
        if not cands:
            unbacked.append(f"UNBACKED      \\phm{{{written}}} in {fname} has no spec entry (by definition it is \\ph)")

    problems = bad + unbacked
    for p in problems:
        print(p)
    if ledger:
        print("\n| written | file | key | actual | ok |\n|---|---|---|---|---|")
        for w, s, k, a, o, ok in resolved:
            print(f"| `{w}` | `{s}` | `{k}` | `{a}` | {'✓' if ok else '✗'} |")
    n_ok = sum(1 for r in resolved if r[5])
    print(f"{n_ok}/{len(resolved)} spec entries verified, {len(uses)} \\phm uses in paper, "
          f"{len(unbacked)} unbacked, {len(bad)} mismatched/missing")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
