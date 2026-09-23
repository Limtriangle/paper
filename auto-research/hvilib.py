"""hvilib — shared instrument for every HVI-CIDNet study script (experiment agent).

Study scripts under auto-research/ import this module. It wraps the UNMODIFIED upstream
repo at /home/work/research/code/HVI-CIDNet (commit pinned in COMMIT) and provides:

  * repo pin check, sys.path setup, the run-directory convention (HVI-PLAN.md §2)
  * the LOLv1 train/val split of our485 (seeded, hashed); eval15 is the TEST split and is
    guarded: open_rgb() refuses any path under eval15 unless allow_test_split() was called
    (only auto-research/final_eval_test.py may call it)
  * the upstream training protocol as a dict (data/options.py defaults) and faithful
    re-implementations of: augmentation (data/data.py transform1), the loss
    (train.py:62-64, same modules, weights and summation order), the LR schedule
    (data/scheduler.py classes instantiated exactly as train.py:150-166 does)
  * the upstream metric definitions copied from measure.py (PSNR / SSIM on uint8,
    LPIPS-alex, optional GT-mean) — preflight verifies the copies against the originals
  * per-image colour diagnostics (CIEDE2000, ab error, chroma-edge band metrics)
  * job bookkeeping: status.json, metrics.csv, validation_summary.csv, atomic saves

Nothing here reads the test split. Nothing here modifies the upstream repo.
"""
from __future__ import annotations

import contextlib
import csv
import hashlib
import json
import math
import os
import random
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(os.environ.get("RESEARCH", "/home/work/research"))
PAPER = Path(os.environ.get("PAPER", "/home/work/research/paper"))
REPO = ROOT / "code" / "HVI-CIDNet"
COMMIT = "eb43d7d91e9a336c66856824ff9e4603ae41f408"
DATA = ROOT / "datasets" / "LOLv1"
TRAIN_DIR = DATA / "our485"          # train + held-out validation come from here
TEST_DIR = DATA / "eval15"           # TEST split: never read outside final_eval_test.py
OUTPUTS = ROOT / "outputs"
HUB = OUTPUTS / "torch_cache"        # torchvision / lpips pretrained weights
SPLIT_SEED, N_VAL = 42, 50
IMAGE_EXT = (".png", ".jpg", ".bmp", ".JPG", ".jpeg")

# data/options.py defaults + train.py behaviour, verbatim. A study that changes any of
# these writes the change into its own protocol dict (new run name, new hash).
UPSTREAM_PROTOCOL = {
    "dataset": "LOLv1",
    "train_source": "our485 minus the held-out validation images",
    "val_source": f"{N_VAL} images held out from our485 (split seed {SPLIT_SEED})",
    "test_source": "eval15",
    "test15": "NEVER READ",
    "crop": 256,                      # options.py:15 cropSize
    "batch_size": 8,                  # options.py:14 batchSize
    "epochs": 1000,                   # options.py:16 nEpochs
    "optimizer": "Adam",              # train.py:151
    "lr": 1e-4,                       # options.py:19
    "betas": [0.9, 0.999],            # torch default, train.py:151 passes none
    "schedule": "GradualWarmupScheduler(multiplier=1,total_epoch=3) -> "
                "CosineAnnealingRestartLR(periods=[epochs-3], eta_min=1e-7); "
                "scheduler.step() once per epoch after training (train.py:160-161,219)",
    "warmup_epochs": 3,               # options.py:29-30 (start_warmup True)
    "lr_min": 1e-7,
    "weights": {"L1": 1.0, "SSIM": 0.5, "edge": 50.0, "perceptual": 0.01, "HVI": 1.0},
    "perceptual": {"vgg": "vgg19", "layers": ["conv1_2", "conv2_2", "conv3_4", "conv4_4"],
                   "criterion": "mse", "range_norm": True, "use_input_norm": True},
    "random_gamma": False,            # options.py:71
    "grad_clip": "none (upstream calls clip_grad_norm_ before backward: no effect)",
    "augmentation": "RandomCrop(crop) + RandomHorizontalFlip + RandomVerticalFlip, "
                    "same crop/flips for low and high (data/data.py:7-13)",
    "shuffle": True, "drop_last": False,
    "precision": "FP32, TF32 disabled, no AMP",
    "cudnn": "deterministic=True, benchmark=False (upstream: benchmark=True, random seed)",
    "val_every": 1,
    "selection": "highest validation mean PSNR (uint8, ungated, no GT mean) over epochs",
    "eval_gated": "reported both ways; upstream eval.py:18-19 sets trans.gated=True "
                  "(alpha_s=1.3 saturation gain) for LOLv1",
    "channels": [36, 36, 72, 144], "heads": [1, 2, 4, 8],   # net/CIDNet.py:10-11
}


# ------------------------------------------------------------------ small utilities
def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_json(obj):
    return sha256_text(json.dumps(obj, sort_keys=True, separators=(",", ":")))


def json_save(path, obj):
    path = Path(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, sort_keys=False), encoding="utf-8")
    os.replace(tmp, path)


def json_load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def csv_save(path, rows):
    require(bool(rows), "Cannot save an empty CSV")
    keys = []
    for r in rows:
        for k in r:
            if k not in keys:
                keys.append(k)
    path = Path(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)
    os.replace(tmp, path)


def csv_rows(path):
    p = Path(path)
    if not p.is_file():
        return []
    with p.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def is_image(p):
    return Path(p).name.endswith(IMAGE_EXT)


def git(*args):
    return subprocess.check_output(["git", "-C", str(REPO), *args], text=True).strip()


# ------------------------------------------------------------------ repo
def check_repo():
    """The upstream clone must be at the pinned commit and unmodified (pycache ignored)."""
    require(REPO.is_dir(), f"Upstream repo missing: {REPO}")
    head = git("rev-parse", "HEAD")
    require(head == COMMIT, f"Upstream HEAD {head} != pinned {COMMIT}")
    dirty = [l for l in git("status", "--porcelain").splitlines() if "__pycache__" not in l]
    require(not dirty, f"Upstream repo has local modifications: {dirty}")
    return head


def import_repo():
    """Make `net`, `loss`, `data` importable. Never chdir into the repo."""
    check_repo()
    if str(REPO) not in sys.path:
        sys.path.insert(0, str(REPO))
    import torch
    HUB.mkdir(parents=True, exist_ok=True)
    torch.hub.set_dir(str(HUB))
    os.environ.setdefault("TORCH_HOME", str(HUB))


@contextlib.contextmanager
def cpu_cuda_shim():
    """Upstream loss modules hard-code .cuda() (loss/losses.py:45, loss/vgg_arch.py:202,
    216-217). For CPU preflight only, make .cuda() a no-op. Never used on a GPU worker."""
    import torch
    t_cuda, m_cuda = torch.Tensor.cuda, torch.nn.Module.cuda
    torch.Tensor.cuda = lambda self, *a, **k: self
    torch.nn.Module.cuda = lambda self, *a, **k: self
    try:
        yield
    finally:
        torch.Tensor.cuda, torch.nn.Module.cuda = t_cuda, m_cuda


def set_determinism(threads=3, strict=False):
    """strict=True additionally enables torch.use_deterministic_algorithms(True) (needs
    CUBLAS_WORKSPACE_CONFIG=:4096:8 in the environment): bitwise-reproducible training at
    ~1.7x the step cost. Default mode leaves atomic-add backward kernels nondeterministic."""
    import torch
    torch.set_num_threads(threads)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    if strict:
        os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
        torch.use_deterministic_algorithms(True)


def seed_all(seed):
    import numpy as np
    import torch
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def state_digest(model):
    import torch
    h = hashlib.sha256()
    for k, v in sorted(model.state_dict().items()):
        h.update(k.encode())
        h.update(v.detach().cpu().contiguous().numpy().tobytes())
    return h.hexdigest()


def build_model(channels=None, heads=None):
    from net.CIDNet import CIDNet
    p = UPSTREAM_PROTOCOL
    return CIDNet(channels=list(channels or p["channels"]), heads=list(heads or p["heads"]))


def count_parameters(model):
    return sum(p.numel() for p in model.parameters())


# ------------------------------------------------------------------ data
_TEST_ALLOWED = False


_TEST_ALLOWED_SCRIPTS = {
    "final_eval_test.py": "evaluate: the one final evaluation per reported configuration",
    "scene_split.py": "list + embed eval15 GT images for scene clustering only; no evaluation",
}


def allow_test_split(reason):
    """Only the whitelisted scripts may call this, once; the permit is written into their JSON."""
    global _TEST_ALLOWED
    script = Path(sys.argv[0]).name
    require(script in _TEST_ALLOWED_SCRIPTS,
            f"The test split may only be accessed by {sorted(_TEST_ALLOWED_SCRIPTS)}")
    _TEST_ALLOWED = True
    return {"test_split_accessed": True, "scope": _TEST_ALLOWED_SCRIPTS[script],
            "reason": reason, "script": sys.argv[0]}


def _guard(path):
    p = Path(path).resolve()
    if not _TEST_ALLOWED and (p == TEST_DIR.resolve() or TEST_DIR.resolve() in p.parents):
        raise RuntimeError(f"TEST SPLIT ACCESS ATTEMPTED: {p}")
    return p


def open_rgb(path):
    from PIL import Image
    with Image.open(_guard(path)) as im:
        return im.convert("RGB")


def list_dir(path):
    """Guarded directory listing (sorted names). Refuses eval15 or anything under it."""
    return sorted(q.name for q in _guard(path).iterdir())


def make_split(seed=SPLIT_SEED, n_val=N_VAL):
    """Deterministic: sorted names, one shuffle with random.Random(seed), first n_val = val."""
    low = [n for n in list_dir(TRAIN_DIR / "low") if is_image(n)]
    high = [n for n in list_dir(TRAIN_DIR / "high") if is_image(n)]
    require(low == high and len(low) == 485, f"our485 layout unexpected: {len(low)}/{len(high)}")
    names = list(low)
    random.Random(seed).shuffle(names)
    val, train = sorted(names[:n_val]), sorted(names[n_val:])
    require(not set(val) & set(train), "split overlap")
    return {"split_seed": seed, "train_val_source": "our485", "test_source": "eval15",
            "test": "NEVER READ", "n_train": len(train), "n_val": len(val),
            "train": train, "val": val}


def split_sha(split):
    return sha256_json({k: split[k] for k in ("split_seed", "train", "val")})


SPLITS = {"random42": "seeded random 50-image hold-out (make_split)",
          "scene_v1": "scene-disjoint 40-image hold-out, auto-research/split_scene_v1.json"}


def load_split(name="scene_v1"):
    """Named split -> dict. scene_v1 is verified against the sha256 stored in its file."""
    require(name in SPLITS, f"unknown split {name}")
    if name == "random42":
        s = make_split()
    else:
        s = json_load(Path(__file__).resolve().parent / f"split_{name}.json")
        require(s["sha256"] == split_sha(s), "split file sha256 mismatch")
    require(not set(s["train"]) & set(s["val"]) and len(s["train"]) + len(s["val"]) == 485, "bad split")
    s["name"] = name
    return s


def dataset_fingerprint(force=False):
    """sha256 over (name, file sha256) of every our485 image; cached. eval15 excluded."""
    cache = OUTPUTS / "lolv1_our485_fingerprint.json"
    if cache.is_file() and not force:
        return json_load(cache)
    entries = []
    for sub in ("low", "high"):
        for p in sorted((TRAIN_DIR / sub).iterdir()):
            if is_image(p):
                entries.append([f"{sub}/{p.name}", sha256_file(p)])
    fp = {"root": str(TRAIN_DIR), "n_files": len(entries),
          "sha256": sha256_json(entries), "computed_at": time.time()}
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    json_save(cache, fp)
    return fp


class Pairs:
    """Train pairs with the upstream augmentation (RandomCrop + H/V flip, identical for low
    and high) but a deterministic per-(seed, epoch, index) RNG instead of the process RNG."""

    def __init__(self, names, crop, seed, data_dir=TRAIN_DIR):
        self.names, self.crop, self.seed, self.epoch = list(names), crop, seed, 0
        self.data_dir = Path(data_dir)

    def __len__(self):
        return len(self.names)

    def __getitem__(self, index):
        from torchvision.transforms.functional import to_tensor
        from PIL import Image
        name = self.names[index]
        low = open_rgb(self.data_dir / "low" / name)
        high = open_rgb(self.data_dir / "high" / name)
        require(low.size == high.size, f"size mismatch {name}")
        rng = random.Random(self.seed + self.epoch * 1000003 + index)
        w, h = low.size
        require(min(w, h) >= self.crop, f"image smaller than crop: {name}")
        left, top = rng.randrange(w - self.crop + 1), rng.randrange(h - self.crop + 1)
        box = (left, top, left + self.crop, top + self.crop)
        low, high = low.crop(box), high.crop(box)
        for op in (Image.Transpose.FLIP_LEFT_RIGHT, Image.Transpose.FLIP_TOP_BOTTOM):
            if rng.random() < 0.5:
                low, high = low.transpose(op), high.transpose(op)
        return to_tensor(low), to_tensor(high)


def make_loader(dataset, batch_size, seed, epoch, workers=3, shuffle=True, drop_last=False):
    import torch
    from torch.utils.data import DataLoader
    g = torch.Generator().manual_seed(seed + epoch)

    def init(worker_id):
        s = seed + epoch * 1000003 + worker_id
        random.seed(s)
        torch.manual_seed(s)

    return DataLoader(dataset, batch_size=batch_size, shuffle=shuffle, num_workers=workers,
                      drop_last=drop_last, generator=g, worker_init_fn=init,
                      persistent_workers=False)


# ------------------------------------------------------------------ loss (train.py:62-64)
class UpstreamLoss:
    """Same modules, weights and summation order as train.py init_loss()/train().
    Returns (total, {term: tensor}). Term keys are stable for later ablation studies."""

    def __init__(self, weights=None, lock_dir=HUB):
        from loss.losses import L1Loss, SSIM, EdgeLoss, PerceptualLoss
        import fcntl
        w = dict(UPSTREAM_PROTOCOL["weights"], **(weights or {}))
        self.weights = w
        self.L1 = L1Loss(loss_weight=w["L1"], reduction="mean").cuda()      # train.py:174
        self.D = SSIM(weight=w["SSIM"]).cuda()                              # train.py:175
        self.E = EdgeLoss(loss_weight=w["edge"]).cuda()                     # train.py:176
        Path(lock_dir).mkdir(parents=True, exist_ok=True)
        with (Path(lock_dir) / ".vgg_init.lock").open("a") as lock:        # 4 workers, 1 download
            fcntl.flock(lock, fcntl.LOCK_EX)
            pl = UPSTREAM_PROTOCOL["perceptual"]
            self.P = PerceptualLoss({k: 1 for k in pl["layers"]}, perceptual_weight=1.0,
                                    criterion=pl["criterion"]).cuda()      # train.py:177
        self.P_weight = w["perceptual"]                                     # options.py:68
        self.HVI_weight = w["HVI"]                                          # options.py:64

    def space(self, out, gt, prefix):
        t = {}
        t[f"{prefix}_l1"] = self.L1(out, gt)
        t[f"{prefix}_ssim"] = self.D(out, gt)
        t[f"{prefix}_edge"] = self.E(out, gt)
        t[f"{prefix}_perc"] = self.P_weight * self.P(out, gt)[0]
        total = t[f"{prefix}_l1"] + t[f"{prefix}_ssim"] + t[f"{prefix}_edge"] + t[f"{prefix}_perc"]
        return total, t

    def __call__(self, model, output_rgb, gt_rgb):
        output_hvi = model.HVIT(output_rgb)                                 # train.py:60
        gt_hvi = model.HVIT(gt_rgb)                                         # train.py:61
        loss_hvi, th = self.space(output_hvi, gt_hvi, "hvi")               # train.py:62
        loss_rgb, tr = self.space(output_rgb, gt_rgb, "rgb")               # train.py:63
        loss = loss_rgb + self.HVI_weight * loss_hvi                        # train.py:64
        return loss, {**tr, **th}

    def reference(self, model, output_rgb, gt_rgb):
        """Literal transcription of train.py:60-64 for the preflight equality check."""
        L1_loss, D_loss, E_loss, P_loss = self.L1, self.D, self.E, self.P
        opt_P_weight, opt_HVI_weight = self.P_weight, self.HVI_weight
        gt_rgb = gt_rgb
        output_hvi = model.HVIT(output_rgb)
        gt_hvi = model.HVIT(gt_rgb)
        loss_hvi = L1_loss(output_hvi, gt_hvi) + D_loss(output_hvi, gt_hvi) + E_loss(output_hvi, gt_hvi) + opt_P_weight * P_loss(output_hvi, gt_hvi)[0]
        loss_rgb = L1_loss(output_rgb, gt_rgb) + D_loss(output_rgb, gt_rgb) + E_loss(output_rgb, gt_rgb) + opt_P_weight * P_loss(output_rgb, gt_rgb)[0]
        loss = loss_rgb + opt_HVI_weight * loss_hvi
        return loss


# ------------------------------------------------------------------ schedule (train.py:150-166)
def make_optimizer_and_scheduler(model, epochs, lr=None, warmup=None, lr_min=None):
    import torch.optim as optim
    from data.scheduler import CosineAnnealingRestartLR, GradualWarmupScheduler
    p = UPSTREAM_PROTOCOL
    lr = p["lr"] if lr is None else lr
    warmup = p["warmup_epochs"] if warmup is None else warmup
    lr_min = p["lr_min"] if lr_min is None else lr_min
    optimizer = optim.Adam(model.parameters(), lr=lr)                       # train.py:151
    step = CosineAnnealingRestartLR(optimizer=optimizer, periods=[epochs - warmup - 0],
                                    restart_weights=[1], eta_min=lr_min)    # train.py:160
    sched = GradualWarmupScheduler(optimizer, multiplier=1, total_epoch=warmup,
                                   after_scheduler=step)                    # train.py:161
    return optimizer, sched


def simulate_schedule(epochs, lr=None, warmup=None, lr_min=None):
    """LR actually used in each epoch (1-based) under the upstream loop, no model needed."""
    import torch
    dummy = torch.nn.Parameter(torch.zeros(1))
    holder = type("M", (), {"parameters": lambda self: [dummy]})()
    optimizer, sched = make_optimizer_and_scheduler(holder, epochs, lr, warmup, lr_min)
    out = []
    for _ in range(epochs):
        out.append(optimizer.param_groups[0]["lr"])
        sched.step()                                                        # train.py:219
    return out


# ------------------------------------------------------------------ metrics (measure.py)
def _ssim_measure(prediction, target):
    """measure.py:15-33 verbatim (cv2, float64, 11x11 gaussian sigma 1.5, 5px crop)."""
    import cv2
    import numpy as np
    C1 = (0.01 * 255) ** 2
    C2 = (0.03 * 255) ** 2
    img1 = prediction.astype(np.float64)
    img2 = target.astype(np.float64)
    kernel = cv2.getGaussianKernel(11, 1.5)
    window = np.outer(kernel, kernel.transpose())
    mu1 = cv2.filter2D(img1, -1, window)[5:-5, 5:-5]
    mu2 = cv2.filter2D(img2, -1, window)[5:-5, 5:-5]
    mu1_sq = mu1 ** 2
    mu2_sq = mu2 ** 2
    mu1_mu2 = mu1 * mu2
    sigma1_sq = cv2.filter2D(img1 ** 2, -1, window)[5:-5, 5:-5] - mu1_sq
    sigma2_sq = cv2.filter2D(img2 ** 2, -1, window)[5:-5, 5:-5] - mu2_sq
    sigma12 = cv2.filter2D(img1 * img2, -1, window)[5:-5, 5:-5] - mu1_mu2
    ssim_map = ((2 * mu1_mu2 + C1) * (2 * sigma12 + C2)) / ((mu1_sq + mu2_sq + C1) * (sigma1_sq + sigma2_sq + C2))
    return ssim_map.mean()


def calculate_ssim(target, ref):
    """measure.py:35-56 verbatim."""
    import numpy as np
    img1 = np.array(target, dtype=np.float64)
    img2 = np.array(ref, dtype=np.float64)
    if not img1.shape == img2.shape:
        raise ValueError("Input images must have the same dimensions.")
    if img1.ndim == 2:
        return _ssim_measure(img1, img2)
    elif img1.ndim == 3:
        if img1.shape[2] == 3:
            ssims = []
            for i in range(3):
                ssims.append(_ssim_measure(img1[:, :, i], img2[:, :, i]))
            return np.array(ssims).mean()
        elif img1.shape[2] == 1:
            return _ssim_measure(np.squeeze(img1), np.squeeze(img2))
    else:
        raise ValueError("Wrong input image dimensions.")


def calculate_psnr(target, ref):
    """measure.py:58-63 verbatim (float32, 255 scale, +1e-8)."""
    import numpy as np
    img1 = np.array(target, dtype=np.float32)
    img2 = np.array(ref, dtype=np.float32)
    diff = img1 - img2
    psnr = 10.0 * np.log10(255.0 * 255.0 / (np.mean(np.square(diff)) + 1e-8))
    return psnr


def to_uint8_hwc(t):
    """torchvision ToPILImage semantics (float -> mul(255).byte(), i.e. truncation)."""
    return t.detach().clamp(0, 1).mul(255).byte().permute(1, 2, 0).cpu().numpy()


def gt_mean_adjust(im1, im2):
    """measure.py:91-94 verbatim. Returns float64 array (not re-quantised, as upstream)."""
    import cv2
    import numpy as np
    mean_restored = cv2.cvtColor(im1, cv2.COLOR_RGB2GRAY).mean()
    mean_target = cv2.cvtColor(im2, cv2.COLOR_RGB2GRAY).mean()
    return np.clip(im1 * (mean_target / mean_restored), 0, 255)


class LPIPSMetric:
    def __init__(self, device="cuda"):
        import fcntl
        import lpips
        HUB.mkdir(parents=True, exist_ok=True)
        with (HUB / ".lpips_init.lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            self.fn = lpips.LPIPS(net="alex", verbose=False).to(device).eval()
        self.device = device
        self.im2tensor = lpips.im2tensor

    def __call__(self, im1, im2):
        """measure.py:98-102: forward(ref, pred) on im2tensor'd HWC arrays."""
        import torch
        with torch.no_grad():
            a = self.im2tensor(im1).to(self.device)
            b = self.im2tensor(im2).to(self.device)
            return self.fn.forward(b, a).item()


def colour_scores(pred, gt):
    """Diagnostics on float RGB CHW tensors: CIEDE2000 mean, Lab ab-error mean, and the
    same three on a chroma-edge band of the GT (90th pct of |grad ab|, floor 1, dilated 3,
    3px border removed). Diagnostic convention, not a published metric."""
    import numpy as np
    from skimage.color import rgb2lab, deltaE_ciede2000
    from scipy.ndimage import binary_dilation
    p = pred.detach().cpu().numpy().transpose(1, 2, 0).astype(np.float64)
    g = gt.detach().cpu().numpy().transpose(1, 2, 0).astype(np.float64)
    pl, gl = rgb2lab(p), rgb2lab(g)
    de = deltaE_ciede2000(gl, pl)
    chroma = np.linalg.norm(pl[..., 1:] - gl[..., 1:], axis=-1)
    dy, dx = np.gradient(gl[..., 1:], axis=(0, 1))
    edge = np.sqrt((dx ** 2 + dy ** 2).sum(axis=-1))
    positives = edge[edge > 0]
    threshold = max(1.0, float(np.percentile(positives, 90))) if positives.size else np.inf
    mask = binary_dilation(edge >= threshold, iterations=3)
    mask[:3] = mask[-3:] = False
    mask[:, :3] = mask[:, -3:] = False
    err = ((p - g) ** 2).mean(axis=-1)
    nan = float("nan")
    return {"delta_e00": float(de.mean()), "ab_error": float(chroma.mean()),
            "edge_pixels": int(mask.sum()),
            "edge_delta_e00": float(de[mask].mean()) if mask.any() else nan,
            "edge_ab_error": float(chroma[mask].mean()) if mask.any() else nan,
            "edge_psnr": -10 * math.log10(max(float(err[mask].mean()), 1e-12)) if mask.any() else nan}


# ------------------------------------------------------------------ inference helpers
def infer(model, x, gated=False):
    """Full-image forward with the upstream eval switches (eval.py:18-19, 47-48)."""
    import torch
    h, w = x.shape[-2:]
    xp = torch.nn.functional.pad(x, (0, (-w) % 8, 0, (-h) % 8), mode="replicate")
    tr = model.trans
    tr.gated, tr.gated2, tr.alpha = bool(gated), False, 1.0                # gamma: never applied (=1)
    try:
        with torch.no_grad():
            y = model(xp)[..., :h, :w]
    finally:
        tr.gated = False
    return y.clamp(0, 1)                                                    # eval.py:39


def load_val_pair(name, data_dir=TRAIN_DIR):
    from torchvision.transforms.functional import to_tensor
    import numpy as np
    low = open_rgb(Path(data_dir) / "low" / name)
    high = open_rgb(Path(data_dir) / "high" / name)
    return to_tensor(low), to_tensor(high), np.array(high)


def validate_psnr(model, names, device="cuda", eval_gated=True):
    """Per-epoch selection metric: mean upstream PSNR (uint8) over the val split, ungated
    (identity knobs) and, if eval_gated, also gated. No GT-mean. Returns (psnr, psnr_gated|None)."""
    import torch
    model.eval()
    acc = {False: 0.0, True: 0.0}
    for name in names:
        x, _, gt_u8 = load_val_pair(name)
        x = x.unsqueeze(0).to(device)
        for gated in ((False, True) if eval_gated else (False,)):
            pred = infer(model, x, gated=gated)[0]
            acc[gated] += float(calculate_psnr(to_uint8_hwc(pred), gt_u8))
    model.train()
    return acc[False] / len(names), (acc[True] / len(names) if eval_gated else None)


def detailed_evaluation(model, names, folder, checkpoints=("last", "best"), device="cuda",
                        n_images=4, data_dir=TRAIN_DIR, split_label="validation", eval_gated=True):
    """Full metric set for each checkpoint file <folder>/<ckpt>.pt on the given names.
    Writes <ckpt>_per_image.csv, <ckpt>_<split_label>_images/, and validation_summary.csv."""
    import torch
    from torchvision.transforms.functional import to_pil_image
    lp = LPIPSMetric(device)
    summary = []
    metric_keys = ["psnr", "ssim", "lpips", "psnr_gtmean", "ssim_gtmean", "lpips_gtmean",
                   "psnr_gated", "ssim_gated", "lpips_gated", "delta_e00", "ab_error",
                   "edge_delta_e00", "edge_ab_error", "edge_psnr"]
    for label in checkpoints:
        state = torch.load(Path(folder) / f"{label}.pt", map_location="cpu", weights_only=False)
        model.load_state_dict(state["model"])
        epoch = state["epoch"]
        del state
        model.eval()
        rows = []
        images = Path(folder) / f"{label}_{split_label}_images"
        images.mkdir(exist_ok=True)
        for index, name in enumerate(names):
            x, gt, gt_u8 = load_val_pair(name, data_dir)
            x = x.unsqueeze(0).to(device)
            gt = gt.unsqueeze(0).to(device)
            pred = infer(model, x, gated=False)
            u8 = to_uint8_hwc(pred[0])
            u8g = to_uint8_hwc(infer(model, x, gated=True)[0]) if eval_gated else None
            adj = gt_mean_adjust(u8, gt_u8)
            r = {"image": name,
                 "psnr": float(calculate_psnr(u8, gt_u8)),
                 "ssim": float(calculate_ssim(u8, gt_u8)),
                 "lpips": lp(u8, gt_u8),
                 "psnr_gtmean": float(calculate_psnr(adj, gt_u8)),
                 "ssim_gtmean": float(calculate_ssim(adj, gt_u8)),
                 "lpips_gtmean": lp(adj, gt_u8),
                 **({"psnr_gated": float(calculate_psnr(u8g, gt_u8)),
                     "ssim_gated": float(calculate_ssim(u8g, gt_u8)),
                     "lpips_gated": lp(u8g, gt_u8)} if eval_gated else {}),
                 **colour_scores(pred[0], gt[0])}
            require(all(math.isfinite(r[k]) for k in ("psnr", "ssim", "lpips")),
                    f"non-finite metric on {name}")
            rows.append(r)
            if index < n_images:
                stem = Path(name).stem
                to_pil_image(pred[0].cpu()).save(images / f"{stem}_output.png")
                to_pil_image(x[0].cpu()).save(images / f"{stem}_input.png")
                to_pil_image(gt[0].cpu()).save(images / f"{stem}_target.png")
        csv_save(Path(folder) / f"{label}_per_image.csv", rows)
        means = {}
        for k in metric_keys:
            if k not in rows[0]:
                continue
            valid = [r[k] for r in rows if math.isfinite(r[k])]
            means[k] = sum(valid) / len(valid) if valid else None
            means[f"{k}_n"] = len(valid)
        summary.append({"checkpoint": label, "epoch": epoch, "n": len(rows), **means})
        model.train()
    csv_save(Path(folder) / "validation_summary.csv", summary)
    return summary


# ------------------------------------------------------------------ job bookkeeping
class Job:
    """One <study>/<run>/<job> directory. mkdir(exist_ok=False): never resume/overwrite."""

    def __init__(self, run_dir, name):
        self.dir = Path(run_dir) / name
        self.dir.mkdir(parents=True, exist_ok=False)
        self.name = name

    def status(self, state, **extra):
        """state is one of running | complete | failed (HVI-PLAN.md §2; tooling/status.sh
        greps for "running"); finer progress goes into `phase`."""
        require(state in ("running", "complete", "failed"), f"bad state {state}")
        json_save(self.dir / "status.json",
                  {"state": state, "pid": os.getpid(), "updated_at": time.time(), **extra})

    def save(self, obj, name):
        import torch
        dest = self.dir / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_suffix(dest.suffix + ".tmp")
        torch.save(obj, tmp)
        os.replace(tmp, dest)

    def fail(self, error_text):
        (self.dir / "error.txt").write_text(error_text, encoding="utf-8")
        self.status("failed", error=error_text[-3000:])


def gpu_info():
    import torch
    props = torch.cuda.get_device_properties(0)
    return {"name": props.name, "total_mem_bytes": props.total_memory,
            "capability": f"{props.major}.{props.minor}",
            "CUDA_VISIBLE_DEVICES": os.environ.get("CUDA_VISIBLE_DEVICES")}


def free_gpus(max_used_mib=1500):
    """Indices whose used memory (nvidia-smi) is below the threshold. Never kills anything."""
    out = subprocess.check_output(["nvidia-smi", "--query-gpu=index,memory.used",
                                   "--format=csv,noheader,nounits"], text=True)
    free = []
    for line in out.strip().splitlines():
        idx, used = [x.strip() for x in line.split(",")]
        if int(used) < max_used_mib:
            free.append(int(idx))
    return free


def environment():
    import torch
    import torchvision
    import lpips
    import PIL
    import numpy
    return {"python": sys.version.split()[0], "torch": torch.__version__,
            "torchvision": torchvision.__version__, "cuda": torch.version.cuda,
            "cudnn": torch.backends.cudnn.version(), "lpips": getattr(lpips, "__version__", "0.1.4"),
            "pillow": PIL.__version__, "numpy": numpy.__version__,
            "venv": os.environ.get("VIRTUAL_ENV")}
