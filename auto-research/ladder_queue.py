"""ladder_queue — ordered job queue for the S1/S2 ladders (master dispatch 2026-09-24): one training job per
free GPU, never more; on each completion export + the single final eval15 read + RESULTS.md row +
one-line report to master; one --oracle pass per seed after ALL seeds of that arm have finished.

    python3 auto-research/ladder_queue.py --init      # write outputs/queue/queue.json from the dispatch order
    python3 auto-research/ladder_queue.py --run       # daemon loop (start with setsid nohup ... &)
    python3 auto-research/ladder_queue.py --status

Rules: never kills anything; a failed job is relaunched ONCE with --job-suffix _retry1 (persona §7);
A1 waits until the five L2 runs are complete, then k_fixed = median of their final k (metrics.csv, last
row) is written into the queue state and the A1 manifest; GPU 0 is left to the running Gate A seed 46
until it completes; "free GPU" = nvidia-smi memory used < 1500 MiB and no job of ours assigned to it.
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import hvilib as H  # noqa: E402

QDIR = H.OUTPUTS / "queue"
STATE = QDIR / "queue.json"
EVENTS = QDIR / "events.log"
PY = sys.executable

# (study, run, arm, seeds) in dispatch order
ORDER = [("s1", "loss_ladder_v1", "L2", [42, 43, 44, 45, 46]),
         ("gateA", "a0_l0_v2", "L0", [47, 48, 49]),
         ("s1", "loss_ladder_v1", "L1", [42, 43, 44, 45, 46]),
         ("s1", "loss_ladder_v1", "L3", [42, 43, 44, 45, 46]),
         ("s1", "loss_ladder_v1", "L4", [42, 43, 44, 45, 46]),
         ("s2", "rep_ladder_v1", "A2", [42, 43, 44, 45, 46, 47, 48, 49]),
         ("s2", "rep_ladder_v1", "A3", [42, 43, 44, 45, 46, 47, 48, 49]),
         ("s2", "rep_ladder_v1", "A4", [42, 43, 44, 45, 46]),
         ("s2", "rep_ladder_v1_a1", "A1", [42, 43, 44, 45, 46])]   # own run: its manifest records k_fixed
LAUNCH_ARGS = ["--epochs", "1000", "--val-every", "5", "--snapshot-every", "10"]
LABEL = {"gateA": "gateA_{arm}_seed{seed}"}   # others: <arm>_seed<s>


def log(msg):
    QDIR.mkdir(parents=True, exist_ok=True)
    line = f"{time.strftime('%Y-%m-%dT%H:%M:%S')} {msg}"
    with EVENTS.open("a") as f:
        f.write(line + "\n")
    print(line, flush=True)


def send(msg):
    try:
        subprocess.run([PY, str(H.PAPER / "herdr" / "herdr_sync.py"), "send", "master", msg], timeout=60,
                       capture_output=True, text=True)
    except Exception as ex:  # noqa: BLE001
        log(f"send failed: {ex}")


def job_dir(j):
    return H.OUTPUTS / j["study"] / j["run"] / (f"{j['arm']}_seed{j['seed']}" + j.get("suffix", ""))


def label(j):
    return LABEL.get(j["study"], "{arm}_seed{seed}").format(**j)


def state_of(j):
    p = job_dir(j) / "status.json"
    return H.json_load(p).get("state") if p.is_file() else None


def gpu_free():
    out = subprocess.check_output(["nvidia-smi", "--query-gpu=index,memory.used", "--format=csv,noheader,nounits"], text=True)
    return {int(i): int(u) < 1500 for i, u in (l.split(",") for l in out.strip().splitlines())}


def init():
    jobs = [{"study": s, "run": r, "arm": a, "seed": x, "state": "queued", "gpu": None, "suffix": ""}
            for s, r, a, seeds in ORDER for x in seeds]
    H.json_save(STATE, {"created_at": time.time(), "jobs": jobs, "k_fixed_A1": None, "oracle_done": [], "notes": []})
    log(f"queue initialised with {len(jobs)} jobs")


def final_k_median_L2(jobs):
    ks = []
    for j in jobs:
        if j["arm"] == "L2" and state_of(j) == "complete":
            rows = H.csv_rows(job_dir(j) / "metrics.csv")
            ks.append(float(rows[-1]["k"]))
    return statistics.median(ks) if len(ks) == 5 else None


def launch(j, gpu, st):
    args = [PY, str(HERE / "hvi_baseline.py"), "--launch", "--study", j["study"], "--run", j["run"],
            "--arm", j["arm"], "--gpu", str(gpu), "--seed", str(j["seed"])] + LAUNCH_ARGS
    if j["arm"] == "A1":
        args += ["--k-fixed", str(st["k_fixed_A1"])]
    if j.get("suffix"):
        args += ["--job-suffix", j["suffix"]]
    r = subprocess.run(args, capture_output=True, text=True, timeout=1800)
    ok = "LAUNCHED" in r.stdout
    j["state"], j["gpu"], j["launched_at"] = ("running" if ok else "launch_failed"), gpu, time.time()
    if ok and j["study"] == "gateA" and j["run"] == "a0_l0_v2":
        annotate_v2_manifest()
    line = [l for l in r.stdout.splitlines() if "LAUNCHED" in l]
    log((line[0] if line else f"LAUNCH FAILED {j['arm']}_seed{j['seed']}: {r.stderr[-300:]}"))
    if not ok:
        j["error"] = (r.stdout + r.stderr)[-1000:]
    return ok


def annotate_v2_manifest():
    """Master requirement (2026-09-24): v2 seeds 47-49 pool with v1 only if the manifest records (a) an
    identical config and (b) the CPU equivalence result of the v2 code vs the v1 code. Both computed, not asserted."""
    mp = H.OUTPUTS / "gateA" / "a0_l0_v2" / "manifest.json"
    if not mp.is_file():
        return
    m = H.json_load(mp)
    if "pooling_with_v1" in m:
        return
    v1 = H.json_load(H.OUTPUTS / "gateA" / "a0_l0_v1" / "manifest.json")["protocol"]
    v2 = dict(m["protocol"])
    added = {k: v2[k] for k in v2 if k not in v1}          # fields that did not exist in v1 (e.g. k_fixed=None)
    diff = {k: {"v1": v1[k], "v2": v2.get(k)} for k in v1 if v1[k] != v2.get(k)}
    eq_p = H.PAPER / "ralph" / "results" / "gateA__v2_equivalence.json"
    eq = H.json_load(eq_p) if eq_p.is_file() else {"pass": False, "error": "equivalence JSON missing"}
    m["pooling_with_v1"] = {"config_identical_to_v1": not diff, "protocol_diff": diff, "fields_added_since_v1": added,
                            "code_equivalence": {"pass": eq.get("pass"), "max_abs_diff": eq.get("max_abs_diff"),
                                                 "v1_commit": eq.get("v1_code", {}).get("commit"), "v2_commit": eq.get("v2_code", {}).get("commit"),
                                                 "file": str(eq_p), "sha256": (H.sha256_file(eq_p) if eq_p.is_file() else None)},
                            "poolable": bool(not diff and eq.get("pass"))}
    H.json_save(mp, m)
    log(f"gateA/a0_l0_v2 manifest annotated: config_identical={not diff} code_equivalence={eq.get('pass')} poolable={m['pooling_with_v1']['poolable']}")


def finish(j, st):
    """export + single final read + RESULTS row + report; called once per completed job."""
    run = f"{j['study']}/{j['run']}"
    subprocess.run([PY, str(HERE / "k_summary.py")], capture_output=True, text=True, timeout=600)   # per-arm k stats -> s1 analysis_k
    for r in {run, "s1/loss_ladder_v1"}:
        subprocess.run([PY, str(H.PAPER / "tooling" / "export_results.py"), "--run", r], capture_output=True, text=True, timeout=600)
    lab = label(j)
    entries = H.json_load(H.PAPER / "ralph" / "results" / "final_eval__test.json")["entries"] if (H.PAPER / "ralph" / "results" / "final_eval__test.json").is_file() else {}
    if lab not in entries:
        r = subprocess.run([PY, str(HERE / "final_eval_test.py"), "--ckpt", str(job_dir(j) / "last.pt"), "--label", lab,
                            "--gpu", str(j["gpu"])], capture_output=True, text=True, timeout=1800,
                           env=dict(os.environ, CUDA_VISIBLE_DEVICES=str(j["gpu"])))
        if "TEST SPLIT READ" not in r.stdout:
            log(f"FINAL READ FAILED {lab}: {r.stderr[-300:]}")
            j["final_read"] = "failed"
            return
    entries = H.json_load(H.PAPER / "ralph" / "results" / "final_eval__test.json")["entries"]
    m = entries[lab]["metrics"]
    ex = H.json_load(H.PAPER / "ralph" / "results" / f"{j['study']}__{j['run']}.json")["jobs"][job_dir(j).name]
    row = (f"| {time.strftime('%Y-%m-%d')} | {j['study']}__{j['run']} ({job_dir(j).name}) | — | {j['arm']} seed {j['seed']} complete: "
           f"val best {ex['best']['psnr']:.2f} dB ep {ex['best']['epoch']} / last {ex['last']['psnr']:.2f}; eval15 final ({lab}): "
           f"raw {m['psnr']:.2f}, GT-mean {m['psnr_gtmean']:.2f}, SSIM {m['ssim']:.3f}, LPIPS {m['lpips']:.3f} | ralph/results/{j['study']}__{j['run']}.json, final_eval__test.json |\n")
    with (H.PAPER / "ralph" / "RESULTS.md").open("a") as f:
        f.write(row)
    j["final_read"] = "done"
    subprocess.run([PY, str(HERE / "run_analysis.py")], capture_output=True, text=True, timeout=1800,
                   env=dict(os.environ, CUDA_VISIBLE_DEVICES=""))   # frozen analysis on complete arms (after this job's read)
    msg = (f"experiment[queue]: {j['arm']} seed {j['seed']} COMPLETE ({run}): eval15 final raw {m['psnr']:.2f} / GT-mean {m['psnr_gtmean']:.2f} "
           f"/ SSIM {m['ssim']:.3f} / LPIPS {m['lpips']:.3f}; val best {ex['best']['psnr']:.2f}; exported + RESULTS row appended (uncommitted).")
    log(msg)
    send(msg)


def oracle_start(j, gpu, st):
    """Non-blocking (2026-09-25): the daemon loop keeps handling completions and launches meanwhile."""
    lab = "oracle_" + label(j)
    logf = QDIR / f"{lab}.log"
    p = subprocess.Popen([PY, str(HERE / "final_eval_test.py"), "--oracle", "--job", str(job_dir(j)), "--label", lab,
                          "--gpu", str(gpu)], stdout=logf.open("w"), stderr=subprocess.STDOUT,
                         env=dict(os.environ, CUDA_VISIBLE_DEVICES=str(gpu)), start_new_session=True)
    st.setdefault("oracle_running", {})[lab] = {"pid": p.pid, "gpu": gpu, "started": time.time(), "log": str(logf)}
    log(f"oracle {lab}: started on GPU {gpu} pid {p.pid}")


def oracle_poll(st):
    """Finished oracle processes -> done if their label is in final_eval__oracle.json, else FAILED."""
    running = st.setdefault("oracle_running", {})
    of = H.PAPER / "ralph" / "results" / "final_eval__oracle.json"
    for lab, info in list(running.items()):
        if Path(f"/proc/{info['pid']}").exists():
            try:
                if Path(f"/proc/{info['pid']}/stat").read_text().rsplit(")", 1)[1].split()[0] != "Z":
                    continue
            except OSError:
                pass
            try:
                os.waitpid(info["pid"], os.WNOHANG)
            except ChildProcessError:
                pass
        ok = of.is_file() and lab in H.json_load(of).get("entries", {})
        st["oracle_done"].append(lab if ok else f"FAILED:{lab}")
        del running[lab]
        log(f"oracle {lab}: {'done' if ok else 'FAILED (see ' + info['log'] + ')'}")


def tick(st):
    jobs = st["jobs"]
    # 1. completions
    for j in jobs:
        if j["state"] == "running":
            s = state_of(j)
            if s == "complete":
                j["state"] = "complete"
                log(f"complete {j['arm']}_seed{j['seed']}{j.get('suffix', '')} on GPU {j['gpu']}")
                finish(j, st)
            elif s == "failed":
                if not j.get("suffix"):
                    log(f"FAILED {j['arm']}_seed{j['seed']} on GPU {j['gpu']} -> one retry (_retry1)")
                    j["state"], j["suffix"] = "queued", "_retry1"
                else:
                    j["state"] = "failed"
                    log(f"FAILED twice {j['arm']}_seed{j['seed']} -> marked failed, reported")
                    send(f"experiment[queue]: {j['arm']} seed {j['seed']} FAILED twice; marked failed; see {job_dir(j)}/error.txt")
    # 2. poll running oracle passes (they are started in step 5, only on GPUs no training job can use)
    oracle_poll(st)
    # 3. A1 gate: k_fixed from the five L2 runs
    if st["k_fixed_A1"] is None:
        k = final_k_median_L2(jobs)
        if k is not None:
            st["k_fixed_A1"] = k
            st["notes"].append(f"k_fixed_A1 = median final k of L2 seeds 42-46 = {k:.4f}")
            log(st["notes"][-1]); send(f"experiment[queue]: A1 k_fixed = {k:.4f} (median final k of the five L2 runs)")
    # 4. launches: one per free GPU
    free = gpu_free()
    busy = {j["gpu"] for j in jobs if j["state"] == "running"} | {o["gpu"] for o in st.get("oracle_running", {}).values()}
    if not st.get("gpu0_released"):
        g0 = H.OUTPUTS / "gateA" / "a0_l0_v1" / "L0_seed46" / "status.json"
        if g0.is_file() and H.json_load(g0).get("state") in ("complete", "failed"):
            st["gpu0_released"] = True
            log("GPU 0 released (Gate A seed 46 terminal)")
    now = time.time()
    fs, stalls = st.setdefault("free_since", {}), st.setdefault("stalls", {})
    for g in sorted(free):
        key = str(g)
        if not free[g] or g in busy:
            fs.pop(key, None); continue
        fs.setdefault(key, now)
        reason = None
        if g == 0 and not st.get("gpu0_released"):
            reason = "GPU 0 reserved for Gate A seed 46 (not terminal yet)"
        elif (QDIR / f"hold_gpu{g}").exists():
            reason = f"hold file {QDIR / f'hold_gpu{g}'} present (experiment's eval passes)"
        else:
            nxt = next((j for j in jobs if j["state"] == "queued" and (j["arm"] != "A1" or st["k_fixed_A1"] is not None)), None)
            if nxt is None:
                reason = ("queue empty" if not any(j["state"] == "queued" for j in jobs)
                          else "only A1 jobs queued and k_fixed_A1 not yet available (L2 runs incomplete)")
            else:
                ok = launch(nxt, g, st)
                busy.add(g)
                if ok:
                    fs.pop(key, None); stalls.pop(key, None); continue
                reason = f"last launch failed for {nxt['arm']}_seed{nxt['seed']}: {nxt.get('error', '')[-200:]}"
        # stall visibility (master 2026-09-24): free > 5 min and nothing launched -> reason in events.log + queue.json
        if now - fs[key] > 300 and now - stalls.get(key, {}).get("logged_at", 0) > 600:
            stalls[key] = {"free_for_s": int(now - fs[key]), "reason": reason, "logged_at": now,
                           "at": time.strftime("%Y-%m-%dT%H:%M:%S")}
            log(f"STALL GPU {g}: free for {int((now - fs[key]) / 60)} min, nothing launched: {reason}")
    # 5. oracle passes: per arm once ALL its seeds are complete; only on a GPU no training job could take
    launchable = any(j["state"] == "queued" and (j["arm"] != "A1" or st["k_fixed_A1"] is not None) for j in jobs)
    if not launchable:
        free = gpu_free()
        busy = {j["gpu"] for j in jobs if j["state"] == "running"} | {o["gpu"] for o in st.get("oracle_running", {}).values()}
        idle = [g for g in sorted(free) if free[g] and g not in busy and (g != 0 or st.get("gpu0_released"))
                and not (QDIR / f"hold_gpu{g}").exists()]
        pending = []
        for arm in sorted({j["arm"] for j in jobs}):
            js = [j for j in jobs if j["arm"] == arm]
            if all(j["state"] == "complete" for j in js):
                pending += [j for j in js if ("oracle_" + label(j)) not in st["oracle_done"]
                            and f"FAILED:oracle_{label(j)}" not in st["oracle_done"]
                            and ("oracle_" + label(j)) not in st.get("oracle_running", {})]
        for g, j in zip(idle, pending):
            oracle_start(j, g, st)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    m = ap.add_mutually_exclusive_group(required=True)
    m.add_argument("--init", action="store_true")
    m.add_argument("--run", action="store_true")
    m.add_argument("--status", action="store_true")
    ap.add_argument("--interval", type=int, default=60)
    a = ap.parse_args()
    if a.init:
        H.require(not STATE.exists(), f"{STATE} exists; refusing to overwrite")
        init(); return
    st = H.json_load(STATE)
    if a.status:
        for j in st["jobs"]:
            print(f"{j['study']}/{j['run']} {j['arm']}_seed{j['seed']}{j.get('suffix', '')}: {j['state']} gpu={j['gpu']}")
        print("k_fixed_A1", st["k_fixed_A1"], "| oracles", len(st["oracle_done"]))
        return
    log(f"queue daemon started pid {os.getpid()}")
    while True:
        try:
            st = H.json_load(STATE)
            tick(st)
            H.json_save(STATE, st)
            if not st.get("oracle_running") and all(j["state"] in ("complete", "failed", "launch_failed") for j in st["jobs"]) and \
               all(("oracle_" + label(j)) in st["oracle_done"] or f"FAILED:oracle_{label(j)}" in st["oracle_done"]
                   for j in st["jobs"] if j["state"] == "complete"):
                log("queue finished"); send("experiment[queue]: all ladder jobs and oracle passes finished"); return
        except Exception as ex:  # noqa: BLE001
            log(f"tick error: {ex!r}")
        time.sleep(a.interval)


if __name__ == "__main__":
    main()
