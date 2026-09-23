"""c1_metrics — frozen per-image measurements for the C1 pre-registration (R2 §4c, §5).

All functions take float RGB tensors in [0,1], shape (3,H,W), pred already clamped.

  scalar_gain(pred, gt)      ONE scalar luminance gain g = mean(Y_gt) / mean(Y_pred), BT.601 luma,
                             applied to all three channels, clipped to [0,1]. Never per-channel.
  image_metrics(pred, gt, lp)  raw and GT-mean PSNR (uint8, measure.py definitions), SSIM, LPIPS,
                             CIEDE2000 raw / after gain, log-exposure error log(mean_Y_out / mean_Y_gt),
                             and the decomposition mse_raw = gain_error + mse_gtmean (gain_error := difference).
  decile_table(pred, gt)     10 bins of GT intensity max(R,G,B) at fixed edges k/10: per bin the RGB MSE,
                             CIEDE2000 mean, chroma-weighted circular hue error |dh|_circ * S_gt (hue in
                             turns, |dh| <= 0.5), and the pixel count.
  poisson_gaussian(x, factor, seed)  darkness stress input: x' = Poisson(factor * x * PHOTONS) / PHOTONS +
                             N(0, READ_SIGMA), clipped, deterministic per (seed); factor 1 = the plain input.
"""
from __future__ import annotations

import math

import numpy as np
import torch

PHOTONS, READ_SIGMA = 500.0, 0.01          # stress-test noise model (full scale = 500 photons)
STRESS_FACTORS = (1.0, 0.5, 0.25)
LUMA = torch.tensor([.299, .587, .114])
DECILE_EDGES = [k / 10 for k in range(11)]


def luma(t):
    return (t * LUMA.to(t).view(3, 1, 1)).sum(0)


def scalar_gain(pred, gt):
    g = luma(gt).mean() / luma(pred).mean().clamp_min(1e-8)
    return float(g), (pred * g).clamp(0, 1)


def _u8(t):
    return t.clamp(0, 1).mul(255).byte().permute(1, 2, 0).cpu().numpy()


def _lab(t):
    from skimage.color import rgb2lab
    return rgb2lab(t.detach().cpu().numpy().transpose(1, 2, 0).astype(np.float64))


def _de00(a_lab, b_lab):
    from skimage.color import deltaE_ciede2000
    return deltaE_ciede2000(a_lab, b_lab)


def hue_sat(t):
    """HSV hue in turns [0,1) and saturation, upstream definition (net/HVI_transform.py:17-31)."""
    v, _ = t.max(0)
    mn, _ = t.min(0)
    d = v - mn
    r, g, b = t[0], t[1], t[2]
    h = torch.zeros_like(v)
    h = torch.where(v == r, ((g - b) / (d + 1e-8)) % 6, h)
    h = torch.where((v == g) & (v != r), 2 + (b - r) / (d + 1e-8), h)
    h = torch.where((v == b) & (v != r) & (v != g), 4 + (r - g) / (d + 1e-8), h)
    h = torch.where(d == 0, torch.zeros_like(h), h) / 6
    s = torch.where(v == 0, torch.zeros_like(v), d / (v + 1e-8))
    return h, s


def image_metrics(pred, gt, lp=None):
    import hvilib as H
    g, pg = scalar_gain(pred, gt)
    u_p, u_pg, u_g = _u8(pred), _u8(pg), _u8(gt)
    gl, pl, pgl = _lab(gt), _lab(pred), _lab(pg)
    mse_raw = float(((pred - gt) ** 2).mean())
    mse_gm = float(((pg - gt) ** 2).mean())
    out = {"psnr": float(H.calculate_psnr(u_p, u_g)), "psnr_gtmean": float(H.calculate_psnr(u_pg, u_g)),
           "ssim": float(H.calculate_ssim(u_p, u_g)), "ssim_gtmean": float(H.calculate_ssim(u_pg, u_g)),
           "delta_e00": float(_de00(gl, pl).mean()), "delta_e00_gtmean": float(_de00(gl, pgl).mean()),
           "gain": g, "log_exposure": float(math.log(luma(pred).mean().clamp_min(1e-8) / luma(gt).mean().clamp_min(1e-8))),
           "mse_raw": mse_raw, "mse_gtmean": mse_gm, "gain_error": mse_raw - mse_gm}
    if lp is not None:
        out["lpips"] = lp(u_p, u_g)
        out["lpips_gtmean"] = lp(u_pg, u_g)
    return out


def decile_table(pred, gt):
    inten, _ = gt.max(0)
    de = torch.from_numpy(_de00(_lab(gt), _lab(pred))).to(pred)
    hp, _ = hue_sat(pred)
    hg, sg = hue_sat(gt)
    dh = (hp - hg).abs()
    dh = torch.minimum(dh, 1 - dh) * sg                   # circular, chroma-weighted
    mse = ((pred - gt) ** 2).mean(0)
    rows = []
    for k in range(10):
        lo, hi = DECILE_EDGES[k], DECILE_EDGES[k + 1]
        m = (inten >= lo) & ((inten < hi) if k < 9 else (inten <= hi))
        n = int(m.sum())
        rows.append({"decile": k, "lo": lo, "hi": hi, "n": n,
                     "rgb_mse": float(mse[m].mean()) if n else None,
                     "delta_e00": float(de[m].mean()) if n else None,
                     "hue_err": float(dh[m].mean()) if n else None})
    return rows


def poisson_gaussian(x, factor, seed):
    if factor == 1.0:
        return x
    g = torch.Generator(device="cpu").manual_seed(seed)
    lam = (x.detach().cpu() * factor * PHOTONS).clamp_min(0)
    shot = torch.poisson(lam, generator=g) / PHOTONS
    read = torch.randn(x.shape, generator=g) * READ_SIGMA
    return (shot + read).clamp(0, 1).to(x)


def stress_seed(name, factor):
    import zlib
    return zlib.crc32(f"{name}:{factor}".encode()) & 0x7FFFFFFF
