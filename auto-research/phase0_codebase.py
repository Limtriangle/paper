"""phase0_codebase — write ralph/results/phase0_codebase.json: what the upstream HVI-CIDNet
code actually does, facts only, each with a file:line pointer into the pinned commit, plus
measured numbers (parameter counts, MACs, inference latency) and the cost block read from
the baseline smoke run.

    python3 auto-research/phase0_codebase.py --gpu 1 [--smoke-run smoke_v1]

Reads: the upstream repo, README, the smoke run's config/metrics. Writes one JSON.
Never reads eval15. Latency is measured on the given GPU with synthetic input.
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import hvilib as H  # noqa: E402

OUT = H.PAPER / "ralph" / "results" / "phase0_codebase.json"
R = "code/HVI-CIDNet"   # pointer prefix; all line numbers refer to commit H.COMMIT


def L(path, lines):
    return f"{R}/{path}:{lines}"


FACTS = {
    "hvi_transform": {
        "class": L("net/HVI_transform.py", "6-122") + " RGB_HVI(nn.Module)",
        "forward_HVIT": {
            "hue_saturation_value": "HSV computed per pixel from RGB (max/min); hue in [0,1), "
                                    "saturation = (max-min)/(max+1e-8), value = max; "
                                    "hue is 0 where max==min " + L("net/HVI_transform.py", "17-31"),
            "density_k": "learnable scalar nn.Parameter initialised at 0.2; the code comment "
                         "says k is the reciprocal of the paper's k " + L("net/HVI_transform.py", "9"),
            "color_sensitive": "C_k = (sin(pi*V/2) + 1e-8) ** k " + L("net/HVI_transform.py", "40"),
            "H": "C_k * S * cos(2*pi*h) " + L("net/HVI_transform.py", "41,43"),
            "V": "C_k * S * sin(2*pi*h) " + L("net/HVI_transform.py", "42,44"),
            "I": "value (= max(R,G,B)), unchanged " + L("net/HVI_transform.py", "45"),
            "output": "cat([H, V, I], dim=1): H,V in [-1,1], I in [0,1] " + L("net/HVI_transform.py", "46"),
            "this_k_side_effect": "HVIT stores k.item() into self.this_k (a Python float) "
                                  + L("net/HVI_transform.py", "37-38"),
        },
        "inverse_PHVIT": {
            "k_used": "self.this_k (Python float captured in the last HVIT call) — the inverse "
                      "is NOT differentiable w.r.t. k " + L("net/HVI_transform.py", "59-60"),
            "steps": "clamp H,V to [-1,1], I to [0,1]; divide H,V by C_k(I)+1e-8; clamp again; "
                     "h = atan2(V+eps, H+eps)/(2pi) mod 1; s = sqrt(H^2+V^2+eps); HSV->RGB by "
                     "the standard 6-sector formula " + L("net/HVI_transform.py", "53-115"),
            "gated_saturation": "if self.gated: s *= alpha_s (alpha_s = 1.3); eval.py enables "
                                "this for LOLv1 only " + L("net/HVI_transform.py", "12-13,69-70")
                                + "; " + L("eval.py", "18-19,47-48"),
            "gated2_intensity": "if self.gated2: rgb *= alpha (LOLv2-real and unpaired eval; "
                                "alpha 0.8-0.84 in eval.py) " + L("net/HVI_transform.py", "120-121")
                                + "; " + L("eval.py", "20-25,105-113"),
        },
    },
    "architecture": {
        "class": L("net/CIDNet.py", "8-126") + " CIDNet(channels=[36,36,72,144], heads=[1,2,4,8], norm=False)",
        "input": "RGB -> HVIT -> hvi (3ch); I branch takes hvi[:,2] (1ch), HV branch takes the "
                 "full 3-channel hvi tensor " + L("net/CIDNet.py", "73-78"),
        "branches": "two U-Nets: HV branch (HVE_block0-3 / HVD_block3-0) and I branch "
                    "(IE_block0-3 / ID_block3-0) " + L("net/CIDNet.py", "20-53"),
        "stem": "ReplicationPad2d(1) + Conv2d 3x3 no bias " + L("net/CIDNet.py", "21-24,39-42"),
        "down": "NormDownsample = Conv3x3(no bias) -> UpsamplingBilinear2d(0.5) -> PReLU; "
                "LayerNorm only if norm=True (default False) " + L("net/transformer_utils.py", "31-48"),
        "up": "NormUpsample = Conv3x3 -> UpsamplingBilinear2d(2) -> cat(skip) -> Conv1x1 -> PReLU "
              + L("net/transformer_utils.py", "50-70"),
        "lca": "6 HV_LCA + 6 I_LCA blocks at levels 2,3,4,4,3,2. CAB: channel-wise cross-attention "
               "(q from x, k/v from y; L2-normalised q,k; learnable temperature per head). "
               "IEL: gated FFN (expansion 2.66, depthwise 3x3, tanh residual gates). HV_LCA: "
               "x = x + CAB(norm x, norm y); x = IEL(norm x) (NO residual on the IEL). I_LCA: "
               "both sub-blocks residual " + L("net/LCA.py", "7-93"),
        "cross_wiring": "each LCA takes its own branch as x and the other branch as y "
                        + L("net/CIDNet.py", "83-84,90-91,97-101,105-106,111-112"),
        "residual_output": "output_hvi = cat([hv_0, i_dec0]) + hvi; output_rgb = PHVIT(output_hvi) "
                           + L("net/CIDNet.py", "119-120"),
        "forward_quirk": "IE_block3 / HVE_block3 are fed i_enc2 / hv_2 (the level-3 downsample "
                         "outputs), not the I_LCA2 / HV_LCA2 outputs; those LCA2 outputs reach the "
                         "decoder only through the skip connections v_jump2 / hv_jump2 "
                         + L("net/CIDNet.py", "90-95,103-104"),
        "dead_block": "I_LCA5's output (i_dec2 at line 105) is overwritten by ID_block2(i_dec3, v_jump1) "
                      "at line 109 before any use, so I_LCA5 (13 tensors) receives no gradient and "
                      "contributes nothing; the I branch effectively has 5 LCA blocks, the HV branch 6 "
                      + L("net/CIDNet.py", "105,109") + " (measured: p.grad is None for all I_LCA5.* after backward)",
        "huggingface_mixin": "CIDNet inherits PyTorchModelHubMixin " + L("net/CIDNet.py", "6,8"),
    },
    "losses": {
        "total": "loss = loss_rgb + HVI_weight * loss_hvi, with loss_X = L1 + SSIM + Edge + "
                 "P_weight * Perceptual computed in X in {RGB, HVI}; HVI tensors via model.HVIT() "
                 + L("train.py", "60-64"),
        "weights": {"L1": 1.0, "SSIM(D)": 0.5, "Edge(E)": 50.0, "Perceptual(P)": 0.01, "HVI": 1.0,
                    "pointer": L("data/options.py", "64-68") + "; " + L("train.py", "168-178")},
        "L1": "mean absolute error " + L("loss/losses.py", "10-37"),
        "SSIM": "1 - SSIM, 11x11 gaussian sigma 1.5, C1=0.01^2, C2=0.03^2 on the raw tensor range "
                + L("loss/losses.py", "166-190") + "; " + L("loss/loss_utils.py", "113-145"),
        "Edge": "MSE between Laplacian-pyramid residuals (5-tap binomial kernel, 1 level, "
                "replicate pad); kernel is created with .cuda() " + L("loss/losses.py", "41-65"),
        "Perceptual": "VGG19 features conv1_2, conv2_2, conv3_4, conv4_4 (weight 1 each), MSE; "
                      "range_norm=True maps x -> (x+1)/2 BEFORE ImageNet normalisation, so RGB in "
                      "[0,1] is fed as [0.5,1] and HVI (H,V in [-1,1]) as [0,1]; VGG weights from "
                      "torchvision pretrained=True " + L("loss/losses.py", "68-161") + "; "
                      + L("loss/vgg_arch.py", "156-168,181-186,213-217,228-230"),
        "gradient_clip": "clip_grad_norm_(0.01) is called BEFORE optimizer.zero_grad()/loss.backward(), "
                         "i.e. on stale gradients that are then zeroed: it has no effect on the update "
                         + L("train.py", "67-72"),
    },
    "training_protocol_upstream": {
        "options_file": L("data/options.py", "11-92"),
        "batch_size": 8, "crop": 256, "epochs": 1000, "lr": 1e-4, "optimizer": "Adam (defaults)",
        "scheduler": "cos_restart=True, start_warmup=True, warmup_epochs=3: GradualWarmupScheduler"
                     "(multiplier=1, total_epoch=3) wrapping CosineAnnealingRestartLR(periods=[997], "
                     "eta_min=1e-7); scheduler.step() once per epoch " + L("train.py", "150-166,219"),
        "schedule_measured": "see instrument.schedule (simulated with the upstream classes): epoch 1 "
                             "trains with lr=0, epochs 2-3 at 1/3 and 2/3 of 1e-4, epoch 4-5 at 1e-4, "
                             "then cosine",
        "snapshots": "checkpoint + evaluation every 10 epochs " + L("data/options.py", "18") + "; " + L("train.py", "221"),
        "threads": 16, "shuffle": True,
        "seed": "random.randint(1, 1e6) per run; NOT reproducible " + L("train.py", "21-28"),
        "cudnn_benchmark": "True " + L("train.py", "32"),
        "gpu": "CUDA_VISIBLE_DEVICES forced to '0' inside train.py " + L("train.py", "33"),
        "augmentation": "RandomCrop(256), RandomHorizontalFlip, RandomVerticalFlip, ToTensor; same "
                        "random seed re-applied for low and high " + L("data/data.py", "7-13") + "; "
                        + L("data/LOLdataset.py", "32-40"),
        "dataset_class": "LOLDatasetFromFolder lists both folders on EVERY __getitem__ and pairs "
                         "low/high by os.listdir order (not sorted); __len__ hard-coded 485 "
                         + L("data/LOLdataset.py", "13-44"),
        "random_gamma": "off by default; if on, input ** U{0.60..1.20} " + L("data/options.py", "71-73") + "; " + L("train.py", "52-55"),
        "precision": "FP32 (no AMP anywhere)",
        "checkpoint_monitoring_split": "for lol_v1 the per-snapshot evaluation reads "
                                       "datasets/LOLdataset/eval15 — the LOLv1 TEST set used in the "
                                       "paper's tables; there is no separate validation split "
                                       + L("data/options.py", "43,53") + "; " + L("train.py", "104-106,226-228,262-265"),
        "monitoring_eval_switches": "eval(..., LOL=True) -> trans.gated=True (saturation x1.3) "
                                    "during training-time evaluation of lol_v1 " + L("train.py", "260-263"),
        "metrics_logged": "PSNR/SSIM/LPIPS via measure.metrics(use_GT_mean=False) on saved PNGs "
                          + L("train.py", "265-276"),
    },
    "evaluation_protocol_upstream": {
        "eval": "loads weights, sets gated (LOLv1) / gated2+alpha (LOLv2-real, unpaired), forward on "
                "the full image (input ** gamma, gamma=1), clamp [0,1], save PNG " + L("eval.py", "12-51"),
        "measure": "PSNR (float32, 255 scale, +1e-8), SSIM (MATLAB-style, per channel, 11x11 "
                   "gaussian sigma 1.5, 5-px border crop, on [0,255]), LPIPS-alex on uint8 via "
                   "lpips.im2tensor; optional GT-mean: scale prediction by mean_gray(GT)/mean_gray(pred) "
                   + L("measure.py", "15-113"),
        "gt_mean_note": "README: GT-mean numbers follow LLFlow/KinD/Retinexformer; only for paired sets",
        "readme_lolv1_numbers": {
            "w_perc": {"psnr": 23.8091, "ssim": 0.8574, "lpips": 0.0856},
            "w_perc_gtmean": {"psnr": 27.7146, "ssim": 0.8760, "lpips": 0.0791},
            "wo_perc": {"psnr": 23.5000, "ssim": 0.8703, "lpips": 0.1053},
            "wo_perc_gtmean": {"psnr": 28.1405, "ssim": 0.8887, "lpips": 0.0988},
            "test_finetuning": {"psnr": 25.4036, "ssim": 0.8652, "lpips": 0.0897},
            "peer_4070": {"psnr": 24.7401, "ssim": 0.8604, "lpips": 0.0896},
            "source": L("Readme.md", "Weights and Results table"),
            "note": "README numbers, not ours; 'wo perc' weights are trained without the perceptual "
                    "term (the README does not give that training command)",
        },
    },
    "datasets_readme": {
        "paired": ["LOLv1 (our485 train / eval15 test)", "LOLv2-real (685 train)", "LOLv2-syn (900 train)",
                   "LOL-Blur (low_blur / high_sharp_scaled)", "Sony-Total-Dark (SID)", "SICE-Mix / SICE-Grad",
                   "FiveK (Retinexformer split)"],
        "unpaired": ["DICM", "LIME", "MEF", "NPE", "VV"],
        "on_disk": "LOLv1 only: our485 (485 pairs, 600x400 PNG) + eval15 (15 pairs); "
                   "/home/work/research/datasets/LOLv1 (zip sha256 prefix 47d85314b7927470)",
        "pointer": L("Readme.md", "Data Preparation") + "; " + L("data/options.py", "33-59"),
    },
    "released_checkpoints_readme": {
        "LOLv1": ["w_perc.pth", "wo_perc.pth", "test_finetuning.pth", "other/PSNR_24.74.pth"],
        "LOLv2_real": ["best_PSNR.pth", "best_SSIM.pth", "w_prec.pth"],
        "LOLv2_syn": ["generalization.pth", "w_perc.pth", "wo_perc.pth"],
        "other": ["LOL-Blur.pth", "SICE.pth", "SID.pth", "fivek.pth"],
        "hosting": "Baidu Pan / OneDrive (code yixu) and HuggingFace (e.g. fediory/HVI-CIDNet-LOLv1-wperc "
                   "via eval_hf.py)",
        "on_disk": "none (weights/ directory absent)",
    },
    "code_facts_a_paper_reader_may_not_expect": [
        "Reported LOLv1 metrics come from outputs with a fixed 1.3x saturation gain applied in the "
        "inverse transform at test time (trans.gated), which is not part of training",
        "The inverse transform uses k as a captured Python float, so k is trained only through the "
        "forward HVIT (loss in HVI space and the residual add), never through the RGB output path",
        "Gradient clipping in train.py is a no-op (called before backward on zeroed gradients)",
        "The training seed is random and unrecorded; runs are not reproducible from the repo alone",
        "Checkpoint monitoring during training reads the LOLv1 test set (eval15); the repo has no "
        "validation split for LOLv1",
        "Epoch 1 of the default schedule trains with lr=0 (warmup starts at 0 with multiplier=1)",
        "The perceptual loss's range_norm maps [0,1] RGB to [0.5,1] before VGG normalisation",
        "IE_block3/HVE_block3 bypass the level-3 LCA outputs on the main path (net/CIDNet.py:94-95)",
        "I_LCA5 is dead code: its output is overwritten before use (net/CIDNet.py:105,109); its "
        "parameters never receive a gradient",
        "Training on CUDA is not bitwise reproducible in default mode (atomic-add backward kernels); "
        "same-seed replicates differ by ~0.02 dB validation PSNR after 2 epochs; strict deterministic "
        "mode is bitwise exact at higher cost (see cost.strict)",
        "requirements.txt pins torch 1.13.1 / Python 3.7; this host runs torch 2.7 / Python 3.12 "
        "(torchvision 'pretrained=True' still works with a deprecation warning)",
    ],
}


def parameter_breakdown(model):
    groups = {"hv_branch": 0, "i_branch": 0, "hv_lca": 0, "i_lca": 0, "k": 0}
    for name, p in model.named_parameters():
        if name.startswith("trans."):
            groups["k"] += p.numel()
        elif name.startswith("HV_LCA"):
            groups["hv_lca"] += p.numel()
        elif name.startswith("I_LCA"):
            groups["i_lca"] += p.numel()
        elif name.startswith(("HVE", "HVD")):
            groups["hv_branch"] += p.numel()
        elif name.startswith(("IE", "ID")):
            groups["i_branch"] += p.numel()
        else:
            raise RuntimeError(f"unassigned parameter {name}")
    groups["total"] = sum(groups.values())
    return groups


def macs(model, shape):
    import torch
    from thop import profile
    with torch.no_grad():
        m, _ = profile(model, inputs=(torch.rand(1, 3, *shape),), verbose=False)
    return int(m)


def latency(model, shape, device, n=50):
    import torch
    model = model.to(device).eval()
    x = torch.rand(1, 3, *shape, device=device)
    with torch.no_grad():
        for _ in range(10):
            model(x)
        torch.cuda.synchronize()
        times = []
        for _ in range(n):
            t0 = time.perf_counter()
            model(x)
            torch.cuda.synchronize()
            times.append(time.perf_counter() - t0)
    return {"median_ms": 1000 * statistics.median(times), "min_ms": 1000 * min(times),
            "n": n, "device": torch.cuda.get_device_name(0), "batch": 1, "shape": list(shape),
            "precision": "FP32, TF32 disabled"}


def reproducibility_block(runs=("smoke_v1", "determinism_a", "determinism_b")):
    """Same seed (42), same code, three GPUs: what is and is not bitwise identical."""
    jobs = {}
    for r in runs:
        job = H.OUTPUTS / "baseline" / r / "upstream_seed42"
        if not (job / "metrics.csv").is_file():
            continue
        cfg = H.json_load(job / "config.json")
        rows = H.csv_rows(job / "metrics.csv")
        jobs[r] = {"initial_model_sha256": cfg["initial_model_sha256"],
                   "strict_deterministic": cfg.get("strict_deterministic", False),
                   "epoch_rows": [{k: float(x[k]) for k in ("loss", "val_psnr", "k")} for x in rows]}
    if len(jobs) < 2:
        return {"status": "fewer than two same-seed runs available"}
    vals = list(jobs.values())
    same_init = len({j["initial_model_sha256"] for j in vals}) == 1
    e1 = len({json.dumps(j["epoch_rows"][0]) for j in vals}) == 1
    e2 = len({json.dumps(j["epoch_rows"][1]) for j in vals if len(j["epoch_rows"]) > 1}) == 1
    p2 = [j["epoch_rows"][1]["val_psnr"] for j in vals if len(j["epoch_rows"]) > 1]
    return {"runs": jobs, "initial_weights_identical": same_init,
            "epoch1_identical_(lr=0,_no_update)": e1, "epoch2_identical_(after_updates)": e2,
            "epoch2_val_psnr_spread_db": (max(p2) - min(p2)) if p2 else None,
            "diagnosis": "default CUDA mode: identical data order/forward/validation; gradients differ "
                         "at ~1e-7 (atomic-add backward kernels) and diverge under Adam. "
                         "torch.use_deterministic_algorithms(True) gives bitwise-identical gradients "
                         "(measured on one step) at ~1.7x step cost (batch 2, 128x128)."}


def cost_block(run):
    d = H.OUTPUTS / "baseline" / run
    job = d / "upstream_seed42"
    if not (job / "metrics.csv").is_file():
        return {"status": "smoke run not available", "run": str(d)}
    rows = H.csv_rows(job / "metrics.csv")
    cfg = H.json_load(job / "config.json")
    st = H.json_load(job / "status.json")
    man = H.json_load(d / "manifest.json")
    tr = [float(r["train_seconds"]) for r in rows]
    va = [float(r["val_seconds"]) for r in rows]
    epochs_full = man["protocol"]["epochs_schedule"]
    per_epoch = statistics.mean(tr[1:]) if len(tr) > 1 else tr[0]
    return {
        "run": f"baseline/{run}", "job": "upstream_seed42", "state": st.get("state"),
        "protocol": {k: man["protocol"].get(k) for k in ("crop", "batch_size", "epochs_schedule",
                                                         "epochs_trained", "precision", "workers",
                                                         "strict_deterministic")},
        "gpu": cfg.get("gpu"), "steps_per_epoch": int(rows[0]["steps"]),
        "images_per_epoch": int(rows[0]["images"]),
        "train_seconds_per_epoch": tr, "val_seconds_per_epoch_50_images_x2": va,
        "peak_mem_alloc_mib": max(float(r["peak_mem_alloc_mib"]) for r in rows),
        "peak_mem_reserved_mib": max(float(r["peak_mem_reserved_mib"]) for r in rows),
        "projected_hours_full_schedule": epochs_full * (per_epoch + statistics.mean(va)) / 3600,
        "projected_hours_train_only": epochs_full * per_epoch / 3600,
        "note": "seconds/epoch = mean over epochs after the first (first includes cudnn/VGG init); "
                "validation = 50 full 600x400 images, ungated + gated forward each",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gpu", type=int, default=1, help="GPU for the latency measurement")
    ap.add_argument("--smoke-run", default="smoke_v1")
    ap.add_argument("--strict-run", default="smoke_strict_v1", help="strict-deterministic smoke for cost.strict")
    ap.add_argument("--no-latency", action="store_true")
    a = ap.parse_args()
    os.environ["CUDA_VISIBLE_DEVICES"] = str(a.gpu)
    import torch
    H.import_repo()
    H.set_determinism(3)
    torch.manual_seed(42)
    model = H.build_model()
    out = {
        "written_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "upstream": {"repo": str(H.REPO), "remote": "https://github.com/Fediory/HVI-CIDNet",
                     "commit": H.check_repo(), "commit_date": H.git("log", "-1", "--format=%ad", "--date=short"),
                     "license": "MIT (LICENSE file)",
                     "files": sorted(str(p.relative_to(H.REPO)) for p in H.REPO.rglob("*.py")
                                     if "__pycache__" not in p.parts)},
        "facts": FACTS,
        "measured": {
            "default_config": {"channels": H.UPSTREAM_PROTOCOL["channels"], "heads": H.UPSTREAM_PROTOCOL["heads"]},
            "parameters": parameter_breakdown(model),
            "macs_256x256": macs(model, (256, 256)),
            "macs_400x600": macs(model, (400, 600)),
            "macs_note": "thop counts (conv/linear only, attention matmuls not counted), as net_test.py does",
            "density_k_init": model.trans.density_k.item(),
        },
        "instrument": {
            "scripts": {"auto-research/hvilib.py": H.sha256_file(HERE / "hvilib.py"),
                        "auto-research/hvi_baseline.py": H.sha256_file(HERE / "hvi_baseline.py")},
            "protocol": H.UPSTREAM_PROTOCOL,
            "split": {"sha256": H.split_sha(H.make_split()), "n_train": 435, "n_val": 50,
                      "rule": "sorted our485 names, random.Random(42).shuffle, first 50 = val",
                      "test": "eval15, guarded in hvilib.open_rgb, NEVER READ"},
            "dataset_fingerprint_our485": H.dataset_fingerprint(),
            "schedule": {"lr_epoch_1_to_6": H.simulate_schedule(1000)[:6],
                         "lr_epoch_1000": H.simulate_schedule(1000)[-1]},
            "deviations_from_upstream": [
                "validation on 50 images held out from our485 instead of eval15 (integrity floor #4)",
                "deterministic seeding, cudnn.deterministic, TF32 off (upstream: random seed, benchmark on)",
                "validation every epoch (upstream: every 10) with PSNR only; full metrics at the end on best/last",
                "no gradient clipping (upstream's call is a no-op, see facts.losses.gradient_clip)",
                "DataLoader workers 3 per job (upstream 16) to share 15 cores across 4 GPUs",
            ],
        },
        "environment": H.environment(),
        "cost": cost_block(a.smoke_run),
        "cost_strict": cost_block(a.strict_run),
        "reproducibility": reproducibility_block(),
    }
    if not a.no_latency:
        out["measured"]["latency_400x600"] = latency(model, (400, 600), "cuda")
        out["measured"]["latency_256x256"] = latency(model, (256, 256), "cuda")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    H.json_save(OUT, out)
    print(f"wrote {OUT}")
    print(json.dumps({"parameters": out["measured"]["parameters"], "macs_256x256": out["measured"]["macs_256x256"],
                      "latency": out["measured"].get("latency_400x600"), "cost": out["cost"]}, indent=1))


if __name__ == "__main__":
    main()
