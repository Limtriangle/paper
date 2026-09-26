#!/usr/bin/env python3
"""Export raw HVI-CIDNet study runs into paper-citable result JSON.

    python3 tooling/export_results.py            # all runs under $RESEARCH/outputs
    python3 tooling/export_results.py --run s1/run_v1
    python3 tooling/export_results.py --summary  # print a table of what was exported

Input layout (written by hvi_*.py):
    $RESEARCH/outputs/<study>/<run>/manifest.json            (protocol, hashes)
    $RESEARCH/outputs/<study>/<run>/<job>/config.json
    $RESEARCH/outputs/<study>/<run>/<job>/status.json         {"state": complete|running|failed}
    $RESEARCH/outputs/<study>/<run>/<job>/validation_summary.csv   rows: checkpoint=best|last
    $RESEARCH/outputs/<study>/<run>/<job>/metrics.csv         per-epoch training curve
    $RESEARCH/outputs/<study>/<run>/analysis_*/{decision.json,seed_summary.csv,paired_metrics.csv}

Output: $PAPER/ralph/results/<study>__<run>.json
    {
      "run_id": "s1__run_v1", "study": ..., "run": ...,
      "exported_at": ISO, "status": "complete"|"partial",
      "protocol": <manifest.protocol or the manifest minus bulky fields>,
      "jobs": {"<job>": {"status", "config": {...subset...}, "epochs_trained",
                         "best": {psnr, ssim, lpips, delta_e00, ab_error, edge_*}, "last": {...},
                         "curve": {"n_epochs", "final_train_loss", "best_val_psnr_epoch"}}},
      "analysis": {<dir>: {"decision": {...}, "seed_summary": [...rows...]}},
      "sources": {"<relative path>": "sha256"}
    }

Rules: never writes a number it did not read from a file; a missing artifact leaves the key
absent; never touches test15; raw run directories are never modified.
"""
import argparse, csv, datetime, hashlib, json, os, pathlib, sys

PAPER = pathlib.Path(os.environ.get("PAPER", "/home/work/research/paper"))
RESEARCH = pathlib.Path(os.environ.get("RESEARCH", "/home/work/research"))
OUT = PAPER / "ralph" / "results"
CONFIG_KEYS = ("variant", "condition", "enabled_terms", "width", "channels", "heads", "seed",
               "parameters", "epochs_schedule", "epochs_trained", "step_limit", "val_limit",
               "weights", "crop", "batch", "batch_size", "lr", "amp", "script_sha256",
               "torch", "gpu", "CUDA_VISIBLE_DEVICES", "test15", "prefilter", "k")


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def num(x):
    try:
        f = float(x)
        return int(f) if f.is_integer() and "." not in str(x) else f
    except (TypeError, ValueError):
        return x


def read_csv(p):
    with open(p, newline="") as f:
        return [{k: num(v) for k, v in row.items()} for row in csv.DictReader(f)]


def export_job(jobdir, sources, rel):
    job = {}
    st = jobdir / "status.json"
    if st.exists():
        job["status"] = json.load(open(st)).get("state")
        sources[f"{rel}/status.json"] = sha(st)
    cfg = jobdir / "config.json"
    if cfg.exists():
        c = json.load(open(cfg))
        job["config"] = {k: c[k] for k in CONFIG_KEYS if k in c}
        if "epochs_trained" in c:
            job["epochs_trained"] = c["epochs_trained"]
        sources[f"{rel}/config.json"] = sha(cfg)
    vs = jobdir / "validation_summary.csv"
    if vs.exists():
        for row in read_csv(vs):
            ck = row.pop("checkpoint", None)
            if ck:
                job[ck] = {k: v for k, v in row.items() if not k.endswith("_n")}
                job[ck]["n_images"] = row.get("n")
        sources[f"{rel}/validation_summary.csv"] = sha(vs)
    mt = jobdir / "metrics.csv"
    if mt.exists():
        rows = read_csv(mt)
        if rows:
            vrows = [r for r in rows if isinstance(r.get("val_psnr"), (int, float))] or rows
            best = max(vrows, key=lambda r: r.get("val_psnr") if isinstance(r.get("val_psnr"), (int, float)) else float("-inf"))
            job["curve"] = {"n_epochs": len(rows),
                            "final_train_loss": rows[-1].get("loss"),
                            "final_val_psnr": rows[-1].get("val_psnr"),
                            "best_val_psnr": best.get("val_psnr"),
                            "best_val_psnr_epoch": best.get("epoch"),
                            "train_seconds_total": sum(r.get("train_seconds", 0) or 0 for r in rows)}
        sources[f"{rel}/metrics.csv"] = sha(mt)
    return job


def export_run(study, run):
    rundir = RESEARCH / "outputs" / study / run
    sources, jobs, analysis = {}, {}, {}
    out = {"run_id": f"{study}__{run}", "study": study, "run": run,
           "exported_at": datetime.datetime.now().isoformat(timespec="seconds"),
           "root": str(rundir)}
    man = rundir / "manifest.json"
    if man.exists():
        m = json.load(open(man))
        out["protocol"] = m.get("protocol", {k: v for k, v in m.items() if k not in ("variants",)})
        for k in ("variants", "widths", "conditions", "script_sha256", "width_protocol_sha256",
                  "controller_sha256", "helper_sha256", "split_sha256"):
            if k in m:
                out.setdefault("manifest", {})[k] = m[k]
        sources["manifest.json"] = sha(man)
    for prot in ("protocol.json", "config.json"):
        p = rundir / prot
        if p.exists() and "protocol" not in out:
            out["protocol"] = json.load(open(p)); sources[prot] = sha(p)
    for d in sorted(rundir.iterdir()):
        if not d.is_dir() or d.name.startswith((".", "__")):
            continue
        if d.name.startswith("analysis"):
            a = {}
            if (d / "decision.json").exists():
                a["decision"] = json.load(open(d / "decision.json")); sources[f"{d.name}/decision.json"] = sha(d / "decision.json")
            if (d / "derived.json").exists():
                a["derived"] = json.load(open(d / "derived.json")); sources[f"{d.name}/derived.json"] = sha(d / "derived.json")
            for c in ("seed_summary.csv", "paired_metrics.csv"):
                if (d / c).exists():
                    a[c.replace(".csv", "")] = read_csv(d / c); sources[f"{d.name}/{c}"] = sha(d / c)
            analysis[d.name] = a
        elif (d / "status.json").exists() or (d / "config.json").exists():
            jobs[d.name] = export_job(d, sources, d.name)
    if not jobs:
        return None
    out["jobs"] = jobs
    if analysis:
        out["analysis"] = analysis
    states = {j.get("status") for j in jobs.values()}
    out["status"] = "complete" if states == {"complete"} else "partial"
    out["n_jobs"] = {"complete": sum(1 for j in jobs.values() if j.get("status") == "complete"), "total": len(jobs)}
    out["sources"] = sources
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", help="study/run to export (default: all)")
    ap.add_argument("--summary", action="store_true")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    targets = []
    if args.run:
        targets.append(tuple(args.run.strip("/").split("/", 1)))
    else:
        for study in sorted((RESEARCH / "outputs").iterdir()):
            if not study.is_dir() or study.name in ("torch_cache",):
                continue
            for run in sorted(study.iterdir()):
                if run.is_dir() and not run.name.startswith("."):
                    targets.append((study.name, run.name))
    rows = []
    for study, run in targets:
        try:
            out = export_run(study, run)
        except Exception as ex:  # noqa: BLE001 — report and continue; never half-write
            print(f"ERROR {study}/{run}: {ex}", file=sys.stderr); continue
        if out is None:
            continue
        dest = OUT / f"{out['run_id']}.json"
        json.dump(out, open(dest, "w"), indent=1, sort_keys=True)
        rows.append((out["run_id"], out["status"], out["n_jobs"]["complete"], out["n_jobs"]["total"], dest.name))
    if args.summary or True:
        w = max((len(r[0]) for r in rows), default=10)
        for r in rows:
            print(f"{r[0]:<{w}}  {r[1]:<8} {r[2]}/{r[3]} jobs  -> ralph/results/{r[4]}")
    print(f"{len(rows)} run(s) exported to {OUT}")


if __name__ == "__main__":
    main()
