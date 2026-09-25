"""run_analysis — apply the FROZEN analysis_c1.py to the ladder arms whose planned seeds are all complete,
and write the decision into the run directory so export_results.py merges it (writing's key contract).

    python3 auto-research/run_analysis.py      # -> outputs/s1/loss_ladder_v1/analysis_s1/decision.json (+ s2 when its run exists)
                                               #    then export_results.py --run s1/loss_ladder_v1 (and s2)

Why a wrapper: analysis_c1.py is frozen (HVI-PLAN S-8), so it is imported unchanged (sha256 recorded) and only
its inputs are chosen here:
  * an arm enters only when ALL its planned seeds have a final eval15 read (L0 uses its ladder seeds 42-46,
    not the extra Gate A seeds 47-49);
  * INTERIM Holm: the pre-registered family is the four ladder contrasts; while some are not yet computable,
    their p-values are padded with 1.0. This can only make the adjusted p of the computed contrasts larger
    (more conservative) than the final all-four Holm. Every decision is labelled interim until all four exist.
Called by ladder_queue.py after every job completion.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import hvilib as H  # noqa: E402
import analysis_c1 as A  # noqa: E402

PLANNED = {"s1": {"L0": [42, 43, 44, 45, 46], "L1": [42, 43, 44, 45, 46], "L2": [42, 43, 44, 45, 46],
                  "L3": [42, 43, 44, 45, 46], "L4": [42, 43, 44, 45, 46]},
           "s2": {"A0": [42, 43, 44, 45, 46], "A1": [42, 43, 44, 45, 46], "A2": list(range(42, 50)),
                  "A3": list(range(42, 50)), "A4": [42, 43, 44, 45, 46]}}
RUN = {"s1": ("s1", "loss_ladder_v1"), "s2": ("s2", "rep_ladder_v1")}
M_FAMILY = 4


def complete_arms(runs, ladder, planned=None):
    out = {}
    for arm, seeds in (planned or PLANNED)[ladder].items():
        key = arm if arm in runs else A.LADDERS[ladder]["alias"].get(arm, arm)   # own entries first, else alias (S2 A0 = S1 L2)
        have = runs.get(key, {})
        if all(s in have for s in seeds):
            out[key] = {s: have[s] for s in seeds}
    return out


ORACLE_RE = __import__("re").compile(r"^oracle_(?:gateA_)?(?P<arm>[A-Z]\d?)_seed(?P<seed>\d+)$")


def oracle_adapter(oracle_path, dest):
    """Master ruling 2026-09-25: label-join adapter. The frozen selection_bias() looks up '<arm>_seed<s>';
    oracle entries are 'oracle_<arm>_seed<s>' / 'oracle_gateA_L0_seed<s>' (L0 = gateA). Writes a relabelled copy."""
    od = H.json_load(oracle_path)
    ent = {}
    for lab, e in od.get("entries", {}).items():
        m = ORACLE_RE.match(lab)
        if m:
            key = f"{m['arm']}_seed{m['seed']}"
            H.require(key not in ent, f"two oracle entries map to {key}")
            ent[key] = e
    H.json_save(dest, {**{k: v for k, v in od.items() if k != "entries"}, "entries": ent,
                       "adapter": "relabelled by run_analysis.oracle_adapter", "source_sha256": H.sha256_file(oracle_path)})
    return dest


def s3(runs):
    """analysis_s3 over arms whose planned seeds all have a final read AND an oracle entry (L0 at its ladder seeds)."""
    oracle = H.PAPER / "ralph" / "results" / "final_eval__oracle.json"
    if not oracle.is_file():
        return None
    tmp = H.OUTPUTS / "queue" / "oracle_relabelled.json"
    oracle_adapter(oracle, tmp)
    have = set(H.json_load(tmp)["entries"])
    sel = {}
    for ladder in ("s1", "s2"):
        for arm, seeds in PLANNED[ladder].items():
            if arm in sel or arm in A.LADDERS[ladder]["alias"]:
                continue
            if arm in runs and all(s in runs[arm] and f"{arm}_seed{s}" in have for s in seeds):
                sel[arm] = {s: runs[arm][s] for s in seeds}
    dec = A.selection_bias(sel, tmp)
    test = H.PAPER / "ralph" / "results" / "final_eval__test.json"
    out = {"run_id": "s3__selection_bias_v1", "analysis": {"analysis_s3": {"decision": dec}},
           "written_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "analysis_script": "auto-research/analysis_c1.py (frozen, imported unchanged)",
           "analysis_sha256": H.sha256_file(HERE / "analysis_c1.py"), "wrapper_sha256": H.sha256_file(Path(__file__)),
           "arms_included": {a: sorted(v) for a, v in sel.items()}, "status": "partial" if len(sel) < 9 else "complete",
           "sources": {test.name: H.sha256_file(test), oracle.name: H.sha256_file(oracle)},
           "notes": "oracle numbers are never used to rank arms"}
    H.json_save(H.PAPER / "ralph" / "results" / "s3__selection_bias_v1.json", out)
    print("s3 arms", sorted(sel), {a: round(v["oracle_minus_final_mean"], 3) for a, v in dec.items() if isinstance(v, dict) and "oracle_minus_final_mean" in v})
    return out


def wrapper_selftest():
    """Re-run the planted-effect / planted-null synthetic test THROUGH the wrapper (arm filter + interim Holm)
    and compare its rule outputs with the frozen analysis on the same data."""
    base = {"psnr": 27.7, "hue_bottom": 0.05, "de_bottom": 0.0, "stress_slope": 0.0}
    effects = {"A0": dict(base), "A1": dict(base),
               "A2": dict(base, psnr=27.1, hue_bottom=0.07, de_bottom=1.0, stress_slope=0.04),
               "A3": dict(base, psnr=27.1, hue_bottom=0.07, de_bottom=1.0),
               "A4": dict(base, psnr=26.95, hue_bottom=0.07, de_bottom=1.0)}
    runs = {}
    for lab, e in A.synthetic(effects)["entries"].items():
        m = A.LABEL_RE.match(lab); runs.setdefault(m["arm"], {})[int(m["seed"])] = e
    keys = ("mean", "sd", "p", "p_holm", "ci_holm", "verdict")
    direct = A.analyse(runs, "s2")
    planned5 = {"s2": {a: [42, 43, 44, 45, 46] for a in effects}}
    orig = A.holm
    A.holm = lambda pv: orig(list(pv) + [1.0] * (M_FAMILY - len(pv)))[:len(pv)]
    try:
        via = A.analyse(complete_arms(runs, "s2", planned5), "s2")
        partial = A.analyse(complete_arms({a: runs[a] for a in ("A0", "A1", "A2")}, "s2", planned5), "s2")
    finally:
        A.holm = orig
    same = all(direct["contrasts"][k][x] == via["contrasts"][k][x] for k in direct["contrasts"] for x in keys)
    cons = all(partial["contrasts"][k]["p_holm"] >= direct["contrasts"][k]["p_holm"] for k in ("A0-A1", "A0-A2"))
    # adapter check on a synthetic oracle file
    tmp_in, tmp_out = H.OUTPUTS / "queue" / "_st_oracle_in.json", H.OUTPUTS / "queue" / "_st_oracle_out.json"
    H.json_save(tmp_in, {"entries": {"oracle_gateA_L0_seed42": {"max_psnr_gtmean": 27.0}, "oracle_A2_seed43": {"max_psnr_gtmean": 26.0}}})
    mapped = sorted(H.json_load(oracle_adapter(tmp_in, tmp_out))["entries"])
    tmp_in.unlink(); tmp_out.unlink()
    return {"written_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "wrapper_sha256": H.sha256_file(Path(__file__)),
            "analysis_sha256": H.sha256_file(HERE / "analysis_c1.py"),
            "all_four_contrasts": {"rule_outputs_identical_to_frozen": same,
                                   "verdicts": {k: via["contrasts"][k]["verdict"] for k in via["contrasts"]}},
            "interim_two_contrasts": {"p_holm_ge_final": cons,
                                      "p_holm": {k: partial["contrasts"][k]["p_holm"] for k in ("A0-A1", "A0-A2")},
                                      "verdicts": {k: partial["contrasts"][k].get("verdict") for k in ("A0-A1", "A0-A2")}},
            "oracle_adapter": {"mapped_keys": mapped, "ok": mapped == ["A2_seed43", "L0_seed42"]},
            "pass": bool(same and cons and mapped == ["A2_seed43", "L0_seed42"])}


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        r = wrapper_selftest()
        p = H.PAPER / "ralph" / "results" / "phase0_analysis_selftest.json"
        d = H.json_load(p)
        d["wrapper_selftest"] = r
        H.json_save(p, d)
        print(json.dumps(r, indent=1))
        return
    test = H.PAPER / "ralph" / "results" / "final_eval__test.json"
    runs, _ = A.load_entries(test)
    orig_holm = A.holm
    A.holm = lambda pv: orig_holm(list(pv) + [1.0] * (M_FAMILY - len(pv)))[:len(pv)]   # interim, conservative
    try:
        for ladder in ("s1", "s2"):
            study, run = RUN[ladder]
            rd = H.OUTPUTS / study / run
            if not rd.is_dir():
                continue
            sel = complete_arms(runs, ladder)
            dec = A.analyse(sel, ladder)
            computed = [k for k, c in dec["contrasts"].items() if "mean" in c]
            dec.update({"written_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                        "analysis_script": "auto-research/analysis_c1.py (frozen, imported unchanged)",
                        "analysis_sha256": H.sha256_file(HERE / "analysis_c1.py"),
                        "wrapper_sha256": H.sha256_file(Path(__file__)),
                        "arms_included": {a: sorted(v) for a, v in sel.items()},
                        "interim": len(computed) < M_FAMILY,
                        "holm_family": f"{M_FAMILY} pre-registered contrasts; missing p padded with 1.0 while interim (conservative)",
                        "sources": {test.name: H.sha256_file(test)},
                        "test15": "final-checkpoint reads by final_eval_test.py; no selection"})
            (rd / f"analysis_{ladder}").mkdir(exist_ok=True)
            H.json_save(rd / f"analysis_{ladder}" / "decision.json", dec)
            subprocess.run([sys.executable, str(H.PAPER / "tooling" / "export_results.py"), "--run", f"{study}/{run}"],
                           capture_output=True, text=True, timeout=600)
            print(ladder, "arms", sorted(sel), "|", {k: (round(c["mean"], 3), c["verdict"]) if "mean" in c else c.get("status")
                                                     for k, c in dec["contrasts"].items()}, "| interim", dec["interim"])
    finally:
        A.holm = orig_holm
    s3(runs)


if __name__ == "__main__":
    main()
