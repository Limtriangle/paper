"""hvi_baseline — the instrument: train + validate UNMODIFIED HVI-CIDNet under the upstream
protocol (data/options.py defaults) on LOLv1 with a held-out validation split.

    python3 auto-research/hvi_baseline.py --preflight                      # CPU, synthetic
    python3 auto-research/hvi_baseline.py --launch --run smoke_v1 --gpu 0 --smoke
    python3 auto-research/hvi_baseline.py --launch --run full_v1  --gpu 1 --seed 42
    python3 auto-research/hvi_baseline.py --status --run smoke_v1

Writes ONLY under /home/work/research/outputs/baseline/<run>/ (HVI-PLAN.md §2 layout):
    manifest.json, split_snapshot.json, <job>.log, <job>/{config,status}.json,
    <job>/metrics.csv, <job>/validation_summary.csv, <job>/{best,last}.pt, per-image CSVs.
Never reads eval15 (guarded in hvilib.open_rgb). Never resumes or overwrites a job.
--smoke trains the first N epochs (default 2) of the full 1000-epoch schedule on the full
train and validation sets, so its seconds/epoch and peak VRAM are the real cost.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import hvilib as H  # noqa: E402
import c1_arms as C  # noqa: E402

SCRIPT = Path(__file__).resolve()
LIB = HERE / "hvilib.py"


def run_dir(run, study="baseline"):
    return H.OUTPUTS / study / run


def job_name(condition, seed):
    return f"{condition}_seed{seed}"


# ------------------------------------------------------------------ preflight (CPU)
def preflight(verbose=True):
    """CPU, synthetic tensors. Proves: repo pinned; model reproducible from seed; loss ==
    literal train.py formula (bitwise); metric copies == measure.py (bitwise); schedule
    simulated from the upstream classes; split deterministic; test guard active."""
    import numpy as np
    import torch
    H.import_repo()
    H.set_determinism(2)
    report = {"commit": H.check_repo()}
    # model
    torch.manual_seed(42)
    m1 = H.build_model()
    torch.manual_seed(42)
    m2 = H.build_model()
    d1, d2 = H.state_digest(m1), H.state_digest(m2)
    H.require(d1 == d2, "same seed must give identical initial weights")
    from net.CIDNet import CIDNet
    torch.manual_seed(42)
    H.require(H.state_digest(CIDNet()) == d1, "build_model() differs from CIDNet() defaults")
    report["model"] = {"parameters": H.count_parameters(m1), "initial_sha256_seed42": d1,
                       "density_k_init": m1.trans.density_k.item()}
    x, gt = torch.rand(2, 3, 32, 40), torch.rand(2, 3, 32, 40)
    m1.eval()
    with torch.no_grad():
        y = m1(x)
    H.require(y.shape == x.shape and bool(y.isfinite().all()), "bad forward")
    # loss: bitwise equal to the literal train.py expression
    with H.cpu_cuda_shim():
        loss = H.UpstreamLoss()
        m1.train()
        pred = m1(x)
        total, terms = loss(m1, pred, gt)
        ref = loss.reference(m1, pred, gt)
    H.require(torch.equal(total, ref), f"loss != train.py formula: {total.item()} vs {ref.item()}")
    H.require(set(terms) == {f"{s}_{t}" for s in ("rgb", "hvi") for t in ("l1", "ssim", "edge", "perc")},
              "unexpected term keys")
    total.backward()
    grads = [p.grad for p in m1.parameters() if p.grad is not None]
    H.require(grads and all(bool(g.isfinite().all()) for g in grads), "non-finite gradients")
    H.require(m1.trans.density_k.grad is not None, "k receives no gradient")
    report["loss"] = {"equals_train_py_formula": "BITWISE", "value": total.item(),
                      "terms": {k: v.item() for k, v in terms.items()}}
    # metrics: copies == measure.py originals (import measure.py with its env side effect undone)
    saved = os.environ.get("CUDA_VISIBLE_DEVICES")
    try:
        import measure as M  # sets CUDA_VISIBLE_DEVICES=0 at import (measure.py:2)
    finally:
        if saved is None:
            os.environ.pop("CUDA_VISIBLE_DEVICES", None)
        else:
            os.environ["CUDA_VISIBLE_DEVICES"] = saved
    rng = np.random.default_rng(0)
    a = rng.integers(0, 256, (48, 64, 3), dtype=np.uint8)
    b = rng.integers(0, 256, (48, 64, 3), dtype=np.uint8)
    H.require(H.calculate_psnr(a, b) == M.calculate_psnr(a, b), "psnr copy differs")
    H.require(H.calculate_ssim(a, b) == M.calculate_ssim(a, b), "ssim copy differs")
    from torchvision import transforms
    t = torch.rand(3, 48, 64)
    via_pil = np.array(transforms.ToPILImage()(t))
    H.require(np.array_equal(via_pil, H.to_uint8_hwc(t)), "uint8 conversion != ToPILImage")
    adj = H.gt_mean_adjust(a, b)
    import cv2
    ref_adj = np.clip(a * (cv2.cvtColor(b, cv2.COLOR_RGB2GRAY).mean()
                           / cv2.cvtColor(a, cv2.COLOR_RGB2GRAY).mean()), 0, 255)
    H.require(np.array_equal(adj, ref_adj), "gt-mean copy differs")
    report["metrics"] = {"psnr_ssim_gtmean_equal_measure_py": "BITWISE",
                         "uint8_equals_ToPILImage": True}
    # schedule
    lrs = H.simulate_schedule(H.UPSTREAM_PROTOCOL["epochs"])
    report["schedule"] = {"epochs": len(lrs), "lr_epoch_1_to_6": lrs[:6],
                          "lr_epoch_500": lrs[499], "lr_last_3": lrs[-3:],
                          "max_lr": max(lrs), "min_lr": min(lrs)}
    # split + test guard
    split = H.make_split()
    H.require(H.make_split() == split, "split not deterministic")
    report["split"] = {"sha256": H.split_sha(split), "n_train": split["n_train"],
                       "n_val": split["n_val"], "val_first5": split["val"][:5]}
    for probe in (lambda: H.open_rgb(H.TEST_DIR / "low" / "1.png"),
                  lambda: H.list_dir(H.TEST_DIR / "low"), lambda: H.list_dir(H.TEST_DIR)):
        try:
            probe()
            H.require(False, "test guard did not fire")
        except RuntimeError as e:
            H.require("TEST SPLIT ACCESS ATTEMPTED" in str(e), "wrong guard error")
    report["test_guard"] = "ACTIVE (open + listing)"
    # augmentation determinism
    ds = H.Pairs(split["train"][:3], 256, 42)
    a1, b1 = ds[0]
    a2, b2 = H.Pairs(split["train"][:3], 256, 42)[0]
    H.require(torch.equal(a1, a2) and torch.equal(b1, b2) and a1.shape == (3, 256, 256),
              "augmentation not deterministic")
    report["augmentation"] = "deterministic per (seed, epoch, index)"
    report["environment"] = H.environment()
    report["preflight"] = "PASS (CPU synthetic; not a training result)"
    if verbose:
        print(json.dumps(report, indent=1))
        print("BASELINE_PREFLIGHT_PASSED")
    return report


# ------------------------------------------------------------------ launch
def make_protocol(args, split):
    p = dict(H.UPSTREAM_PROTOCOL)
    p.update({"k0": args.k0, "val_every": args.val_every, "split": args.split,
              "schedule_kind": args.schedule, "warmup_epochs": args.warmup, "lr": args.lr,
              "finetune_from": (str(Path(args.finetune).resolve()) if args.finetune else None),
              "finetune_from_sha256": (H.sha256_file(args.finetune) if args.finetune else None),
              "eval_gated": bool(args.eval_gated),
              "inverse_knobs": {"gated": False, "gated2": False, "alpha": 1.0, "gamma": 1.0},
              "mode": "smoke" if args.smoke else "full", "study": args.study,
              "epochs_schedule": args.epochs,
              "epochs_trained": (args.smoke_epochs if args.smoke else args.epochs),
              "step_limit": 0, "val_limit": 0, "commit": H.COMMIT,
              "split_sha256": H.split_sha(split), "workers": args.workers,
              "snapshot_every": args.snapshot_every,   # upstream options.py:18 snapshots=10; 0 = off
              "strict_deterministic": bool(args.strict)})
    return p


def launch(args):
    import fcntl
    import torch
    out = run_dir(args.run, args.study)
    out.parent.mkdir(parents=True, exist_ok=True)
    lock = (out.parent / ".launch.lock").open("a")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    free = H.free_gpus()
    H.require(args.gpu in free, f"GPU {args.gpu} is not free (free: {free}); nothing was stopped")
    name = job_name(args.arm, args.seed)
    split = H.load_split(args.split)
    if out.exists():   # add a job to an existing run: same protocol, same code, new (arm, seed)
        manifest = H.json_load(out / "manifest.json")
        H.require(manifest["protocol"] == make_protocol(args, split), "protocol differs from the existing run: use a new run name")
        H.require(manifest["script_sha256"] == H.sha256_file(SCRIPT) and manifest["lib_sha256"] == H.sha256_file(LIB)
                  and manifest["arms_sha256"] == H.sha256_file(HERE / "c1_arms.py"), "code changed since the run was created")
        H.require(not (out / name).exists() and name not in [j["job"] for j in manifest["jobs"]], f"job {name} already exists")
    else:
        report = preflight(verbose=False)
        report["arms"] = C.preflight(verbose=False)
        fp = H.dataset_fingerprint()
        out.mkdir(exist_ok=False)
        H.json_save(out / "split_snapshot.json", split)
        manifest = {"study": args.study, "run": args.run, "created_at": time.time(),
                    "script": str(SCRIPT), "script_sha256": H.sha256_file(SCRIPT),
                    "lib_sha256": H.sha256_file(LIB), "arms_sha256": H.sha256_file(HERE / "c1_arms.py"),
                    "commit": H.COMMIT, "split_sha256": H.split_sha(split), "dataset_fingerprint": fp,
                    "protocol": make_protocol(args, split), "preflight": report,
                    "jobs": [], "launch_error": None}
        H.json_save(out / "manifest.json", manifest)
    env = os.environ.copy()
    env.update(CUDA_VISIBLE_DEVICES=str(args.gpu), OMP_NUM_THREADS="3", MKL_NUM_THREADS="3",
               PYTHONUNBUFFERED="1", TORCH_HOME=str(H.HUB), CUBLAS_WORKSPACE_CONFIG=":4096:8")
    cmd = [sys.executable, "-u", str(SCRIPT), "--worker", "--run", args.run, "--study", args.study,
           "--arm", args.arm, "--seed", str(args.seed)]
    try:
        with (out / f"{name}.log").open("x") as log:
            proc = subprocess.Popen(cmd, env=env, stdout=log, stderr=subprocess.STDOUT,
                                    start_new_session=True, cwd=str(HERE))
        manifest["jobs"].append({"job": name, "arm": args.arm, "seed": args.seed, "gpu_index": args.gpu,
                                 "pid": proc.pid, "launched_at": time.time()})
        H.json_save(out / "manifest.json", manifest)
    except Exception:
        manifest["launch_error"] = traceback.format_exc()
        H.json_save(out / "manifest.json", manifest)
        raise
    print(f"LAUNCHED {args.study}/{args.run}/{name} on GPU {args.gpu} pid={proc.pid} "
          f"mode={manifest['protocol']['mode']} epochs_trained={manifest['protocol']['epochs_trained']}")
    print(f"  log: {out / (name + '.log')}")
    print(f"  export: python3 tooling/export_results.py --run {args.study}/{args.run}")


# ------------------------------------------------------------------ worker (one GPU)
def worker(args):
    import numpy as np
    import random
    import torch
    out = run_dir(args.run, args.study)
    manifest = H.json_load(out / "manifest.json")
    H.require(H.sha256_file(SCRIPT) == manifest["script_sha256"], "script changed since launch")
    H.require(H.sha256_file(LIB) == manifest["lib_sha256"], "hvilib changed since launch")
    p = dict(manifest["protocol"], arm=args.arm, condition=args.arm,
             representation=C.ARMS[args.arm][0], loss=C.ARMS[args.arm][1])
    job = H.Job(out, job_name(args.arm, args.seed))
    job.status("running", phase="initializing")
    try:
        H.import_repo()
        H.require(torch.cuda.is_available() and torch.cuda.device_count() == 1,
                  "worker must see exactly one GPU")
        H.set_determinism(3, strict=p.get("strict_deterministic", False))
        split = H.json_load(out / "split_snapshot.json")
        H.require(H.split_sha(split) == p["split_sha256"] == H.split_sha(H.load_split(p["split"])),
                  "split changed")
        seed = args.seed
        model = C.build_arm(p["arm"], seed, p["channels"], p["heads"])
        init_info = {"init": "scratch (seeded)"}
        if p.get("finetune_from"):
            import safetensors.torch as sf
            src = Path(p["finetune_from"])
            H.require(H.sha256_file(src) == p["finetune_from_sha256"], "fine-tune init file changed")
            sd = sf.load_file(str(src)) if src.suffix == ".safetensors" else torch.load(src, map_location="cpu", weights_only=False)["model"]
            init_info = {"init": "finetune", "from": str(src), "from_sha256": p["finetune_from_sha256"], **model.load_pretrained(sd)}
        config = {"variant": p["condition"], "condition": p["condition"], "seed": seed, **init_info,
                  "schedule_kind": p["schedule_kind"], "warmup_epochs": p["warmup_epochs"],
                  "arm": p["arm"], "representation": p["representation"], "loss": p["loss"],
                  "k0": p["k0"], "val_every": p["val_every"], "split": p["split"],
                  "inverse_knobs": p["inverse_knobs"],
                  "width": p["channels"][0], "channels": p["channels"], "heads": p["heads"],
                  "parameters": H.count_parameters(model),
                  "initial_model_sha256": H.state_digest(model),
                  "epochs_schedule": p["epochs_schedule"], "epochs_trained": p["epochs_trained"],
                  "step_limit": p["step_limit"], "val_limit": p["val_limit"],
                  "weights": p["weights"], "crop": p["crop"], "batch_size": p["batch_size"],
                  "lr": p["lr"], "amp": False, "precision": p["precision"],
                  "script_sha256": manifest["script_sha256"], "lib_sha256": manifest["lib_sha256"],
                  "commit": p["commit"], "split_sha256": p["split_sha256"],
                  "torch": torch.__version__, "gpu": torch.cuda.get_device_name(0),
                  "CUDA_VISIBLE_DEVICES": os.environ.get("CUDA_VISIBLE_DEVICES"),
                  "selection": p["selection"], "test15": "NEVER READ", "mode": p["mode"],
                  "strict_deterministic": p.get("strict_deterministic", False)}
        H.json_save(job.dir / "config.json", config)
        (job.dir / "packages.txt").write_text(
            subprocess.run([sys.executable, "-m", "pip", "freeze"], text=True,
                           capture_output=True).stdout, encoding="utf-8")
        model.cuda().train()
        loss_fn = C.make_loss(p["loss"], p["k0"], p["weights"])
        if p["schedule_kind"] == "finetune":
            lrs = H.finetune_lr_schedule(p["epochs_schedule"], p["lr"], p["warmup_epochs"], p["lr_min"])
            optimizer = torch.optim.Adam(model.parameters(), lr=lrs[0])
            scheduler = None
        else:
            optimizer, scheduler = H.make_optimizer_and_scheduler(
                model, p["epochs_schedule"], p["lr"], p["warmup_epochs"], p["lr_min"])
        train_names = split["train"]
        val_names = split["val"][:p["val_limit"]] if p["val_limit"] else split["val"]
        dataset = H.Pairs(train_names, p["crop"], seed)
        history, best_psnr = [], -float("inf")
        print(f"START {job.name}: params={config['parameters']} "
              f"epochs_trained={p['epochs_trained']}/{p['epochs_schedule']} "
              f"batch={p['batch_size']} crop={p['crop']}", flush=True)
        for epoch in range(p["epochs_trained"]):
            if scheduler is None:
                for g in optimizer.param_groups:
                    g["lr"] = lrs[epoch]
            lr = optimizer.param_groups[0]["lr"]
            dataset.epoch = epoch
            loader = H.make_loader(dataset, p["batch_size"], seed, epoch, workers=p["workers"],
                                   shuffle=p["shuffle"], drop_last=p["drop_last"])
            job.status("running", phase="training", epoch=epoch + 1)
            torch.cuda.reset_peak_memory_stats()
            torch.cuda.synchronize()
            tick = time.time()
            model.train()
            total, steps, n_images = 0.0, 0, 0
            term_sum = {}
            for index, (x, gt) in enumerate(loader):
                if p["step_limit"] and index >= p["step_limit"]:
                    break
                x, gt = x.cuda(non_blocking=True), gt.cuda(non_blocking=True)
                output_rgb = model(x)                                      # train.py:57
                loss, terms = loss_fn(model, output_rgb, gt)               # train.py:60-64
                H.require(bool(torch.isfinite(loss)), "non-finite training loss")
                optimizer.zero_grad()                                      # train.py:70
                loss.backward()                                            # train.py:71
                optimizer.step()                                           # train.py:72
                total += loss.item()
                steps += 1
                n_images += x.shape[0]
                for k, v in terms.items():
                    term_sum[k] = term_sum.get(k, 0.0) + v.item()
            torch.cuda.synchronize()
            train_seconds = time.time() - tick
            if scheduler is not None:
                scheduler.step()                                           # train.py:219
            do_val = (epoch + 1) % p["val_every"] == 0 or epoch + 1 == p["epochs_trained"]
            if do_val:
                job.status("running", phase="validating", epoch=epoch + 1)
                v0 = time.time()
                psnr, psnr_gated = H.validate_psnr(model, val_names, eval_gated=p["eval_gated"])
                val_seconds = time.time() - v0
            else:
                psnr, psnr_gated, val_seconds = None, None, 0.0
            row = {"epoch": epoch + 1, "steps": steps, "images": n_images, "loss": total / steps,
                   "val_psnr": "" if psnr is None else psnr,
                   "val_psnr_gated": "" if psnr_gated is None else psnr_gated,
                   "train_seconds": train_seconds, "val_seconds": val_seconds, "lr": lr,
                   "k": model.trans.density_k.detach().item(),
                   "peak_mem_alloc_mib": torch.cuda.max_memory_allocated() / 2**20,
                   "peak_mem_reserved_mib": torch.cuda.max_memory_reserved() / 2**20}
            row.update({f"term_{k}": v / steps for k, v in term_sum.items()})
            if psnr is not None and psnr > best_psnr:
                best_psnr = psnr
                job.save({"epoch": epoch + 1, "model": model.state_dict(), "val_psnr": psnr,
                          "config": config}, "best.pt")
            history.append(row)
            if p.get("snapshot_every") and (epoch + 1) % p["snapshot_every"] == 0:
                (job.dir / "snapshots").mkdir(exist_ok=True)
                job.save({"epoch": epoch + 1, "model": model.state_dict(), "val_psnr": psnr,
                          "config": config}, f"snapshots/epoch_{epoch + 1:04d}.pt")
            job.save({"epoch": epoch + 1, "model": model.state_dict(),
                      "optimizer": optimizer.state_dict(), "scheduler": (scheduler.state_dict() if scheduler else None),
                      "history": history, "torch_rng": torch.get_rng_state(),
                      "cuda_rng": torch.cuda.get_rng_state_all(), "python_rng": random.getstate(),
                      "numpy_rng": np.random.get_state(), "config": config}, "last.pt")
            H.csv_save(job.dir / "metrics.csv", history)
            print(f"{job.name}: epoch {epoch+1}/{p['epochs_trained']} loss={row['loss']:.5f} "
                  f"val_psnr={psnr} (gated {psnr_gated}) lr={lr:.3g} "
                  f"train_s={train_seconds:.1f} val_s={val_seconds:.1f} "
                  f"peak_alloc={row['peak_mem_alloc_mib']:.0f}MiB", flush=True)
        del optimizer, loss_fn
        torch.cuda.empty_cache()
        job.status("running", phase="evaluating")
        H.detailed_evaluation(model, val_names, job.dir, eval_gated=p["eval_gated"])
        cfg = H.json_load(job.dir / "config.json")
        cfg["epochs_trained"] = len(history)
        cfg["gpu_info"] = H.gpu_info()
        H.json_save(job.dir / "config.json", cfg)
        job.status("complete", epochs=len(history))
        print("BASELINE_WORKER_COMPLETE; validation split only; eval15 never read", flush=True)
    except Exception:
        job.fail(traceback.format_exc())
        raise


# ------------------------------------------------------------------ status
def status(args):
    out = run_dir(args.run, args.study)
    if not (out / "manifest.json").exists():
        print("no manifest")
        return
    m = H.json_load(out / "manifest.json")
    p = m["protocol"]
    print(f"{args.study}/{args.run}: mode={p['mode']} schedule={p['schedule_kind']} lr={p['lr']} "
          f"epochs={p['epochs_trained']}/{p['epochs_schedule']}")
    for j in m["jobs"]:
        d = out / j["job"]
        s = H.json_load(d / "status.json") if (d / "status.json").exists() else {}
        rows = H.csv_rows(d / "metrics.csv")
        line = f"  {j['job']} gpu={j['gpu_index']} pid={j['pid']} state={s.get('state')}"
        if rows:
            r = rows[-1]
            line += (f" epoch={r['epoch']} val_psnr={float(r['val_psnr']):.4f} "
                     f"train_s={float(r['train_seconds']):.1f} val_s={float(r['val_seconds']):.1f}")
        print(line)
        if s.get("state") == "failed":
            print(s.get("error", "")[-1500:])
    if m.get("launch_error"):
        print("LAUNCH_ERROR", m["launch_error"][-1500:])


def parse_args():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--preflight", action="store_true")
    mode.add_argument("--launch", action="store_true")
    mode.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    mode.add_argument("--status", action="store_true")
    ap.add_argument("--run", default="smoke_v1")
    ap.add_argument("--study", default="baseline", help="outputs/<study>/<run>/")
    ap.add_argument("--finetune", help="init weights (.safetensors or a job .pt); enables schedule=finetune unless overridden")
    ap.add_argument("--schedule", choices=("upstream", "finetune"), default=None)
    ap.add_argument("--warmup", type=int, default=None, help="warmup epochs (upstream 3; finetune default 2)")
    ap.add_argument("--lr", type=float, default=None, help="peak lr (upstream 1e-4; finetune default 3e-5)")
    ap.add_argument("--gpu", type=int, default=0)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--epochs", type=int, default=H.UPSTREAM_PROTOCOL["epochs"], help="schedule length")
    ap.add_argument("--smoke", action="store_true", help="train only --smoke-epochs of the schedule")
    ap.add_argument("--smoke-epochs", type=int, default=2)
    ap.add_argument("--workers", type=int, default=3, help="DataLoader workers (15 cores / 4 GPUs)")
    ap.add_argument("--strict", action="store_true",
                    help="torch.use_deterministic_algorithms(True): bitwise-reproducible, ~1.7x slower")
    ap.add_argument("--snapshot-every", type=int, default=10,
                    help="also keep snapshots/epoch_N.pt every N epochs (upstream: 10); 0 = off")
    ap.add_argument("--arm", default="U", choices=tuple(C.ARMS),
                    help="C1 arm (c1_arms.py); U = upstream model + upstream loss")
    ap.add_argument("--k0", type=float, default=C.K0_DEFAULT, help="frozen k in the loss-side HVI transform")
    ap.add_argument("--val-every", type=int, default=5, help="validate every N epochs (and the last)")
    ap.add_argument("--split", default="scene_v1", choices=tuple(H.SPLITS))
    ap.add_argument("--eval-gated", action="store_true",
                    help="also record upstream's gated (x1.3 saturation) columns; default: identity knobs only")
    a = ap.parse_args()
    H.require(Path(a.run).name == a.run and a.run not in ("", ".", ".."), "unsafe run name")
    H.require(Path(a.study).name == a.study and a.study not in ("", ".", ".."), "unsafe study name")
    if a.schedule is None:
        a.schedule = "finetune" if a.finetune else "upstream"
    if a.warmup is None:
        a.warmup = 2 if a.schedule == "finetune" else H.UPSTREAM_PROTOCOL["warmup_epochs"]
    if a.lr is None:
        a.lr = 3e-5 if a.schedule == "finetune" else H.UPSTREAM_PROTOCOL["lr"]
    return a


def main():
    a = parse_args()
    if a.preflight:
        preflight()
    elif a.launch:
        launch(a)
    elif a.worker:
        worker(a)
    else:
        status(a)


if __name__ == "__main__":
    main()
