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


def complete_arms(runs, ladder):
    out = {}
    for arm, seeds in PLANNED[ladder].items():
        src = A.LADDERS[ladder]["alias"].get(arm, arm)
        have = runs.get(src, {})
        if all(s in have for s in seeds):
            out[arm if arm not in A.LADDERS[ladder]["alias"] else src] = {s: have[s] for s in seeds}
    return out


def main():
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


if __name__ == "__main__":
    main()
