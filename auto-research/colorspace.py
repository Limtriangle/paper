"""colorspace — C1 adapters: sRGB image -> [chroma0, chroma1, intensity] (B,3,H,W) and back.

Channel layout matches CIDNet's HVI tensor (net/CIDNet.py:73-74): channel 2 is the I-branch
input, all three feed the HV branch, the output residual is added in this space, and the
adapter's inverse() replaces trans.PHVIT. Every adapter is differentiable and works on [0,1].

    python3 auto-research/colorspace.py      # round-trip tests -> ralph/results/phase0_colorspace_roundtrip.json

Adapters (exact mappings; eps = 1e-8 unless stated):
  srgb    intensity I = max(R,G,B); chroma = chromaticity minus the achromatic point:
          (r - 1/3, g - 1/3) with r = R/(R+G+B+eps), g = G/(R+G+B+eps). Lossless:
          c = (r, g, 1-r-g); rgb = I * c / max(c). Undefined at black (0/0), like HVI.
  hsv     I = V = max(R,G,B); chroma = (h - 1/2, s - 1/2), h in [0,1) the standard hue,
          s = (max-min)/(max+eps). Inverse: 6-sector HSV->RGB. Hue wraps at 0/1 (discontinuous).
  ycbcr   ITU-R BT.601 full range: Y = .299R + .587G + .114B; Cb = .564(B-Y); Cr = .713(R-Y).
          Linear, lossless. Cb, Cr in [-0.5, 0.5].
  hvi_nock  HVI with C_k = 1: chroma = s*(cos 2*pi*h, sin 2*pi*h), I = V. Inverse: s = |chroma|,
          h = atan2 / 2*pi. Equals the upstream transform without the density term.
  hvi     the upstream RGB_HVI module verbatim (net/HVI_transform.py) with k fixed to its
          init value 0.2 for the test: chroma = C_k(V) * s * (cos, sin), C_k = (sin(pi V/2)+eps)^k;
          inverse divides by C_k(I) + eps. k learnable in training (upstream default).
"""
from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

import torch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import hvilib as H  # noqa: E402

EPS = 1e-8
PI = math.pi


def _hsv(rgb):
    v, _ = rgb.max(1)
    mn, _ = rgb.min(1)
    d = v - mn
    r, g, b = rgb[:, 0], rgb[:, 1], rgb[:, 2]
    h = torch.zeros_like(v)
    h = torch.where(v == r, ((g - b) / (d + EPS)) % 6, h)
    h = torch.where((v == g) & (v != r), 2 + (b - r) / (d + EPS), h)
    h = torch.where((v == b) & (v != r) & (v != g), 4 + (r - g) / (d + EPS), h)
    h = torch.where(d == 0, torch.zeros_like(h), h) / 6
    s = torch.where(v == 0, torch.zeros_like(v), d / (v + EPS))
    return h, s, v


def _hsv_to_rgb(h, s, v):
    h = h % 1
    hi = torch.floor(h * 6)
    f = h * 6 - hi
    p, q, t = v * (1 - s), v * (1 - f * s), v * (1 - (1 - f) * s)
    hi = hi.long() % 6
    r = torch.stack([v, q, p, p, t, v], 1).gather(1, hi.unsqueeze(1))
    g = torch.stack([t, v, v, q, p, p], 1).gather(1, hi.unsqueeze(1))
    b = torch.stack([p, p, t, v, v, q], 1).gather(1, hi.unsqueeze(1))
    return torch.cat([r, g, b], 1)


class SRGB:
    name = "srgb"

    def forward(self, rgb):
        s = rgb.sum(1, keepdim=True) + EPS
        i, _ = rgb.max(1, keepdim=True)
        return torch.cat([rgb[:, :1] / s - 1 / 3, rgb[:, 1:2] / s - 1 / 3, i], 1)

    def inverse(self, x):
        r, g = x[:, :1] + 1 / 3, x[:, 1:2] + 1 / 3
        c = torch.cat([r, g, 1 - r - g], 1).clamp(0, 1)
        cm, _ = c.max(1, keepdim=True)
        return (x[:, 2:3].clamp(0, 1) * c / (cm + EPS)).clamp(0, 1)


class HSV:
    name = "hsv"

    def forward(self, rgb):
        h, s, v = _hsv(rgb)
        return torch.stack([h - 0.5, s - 0.5, v], 1)

    def inverse(self, x):
        return _hsv_to_rgb(x[:, 0] + 0.5, (x[:, 1] + 0.5).clamp(0, 1), x[:, 2].clamp(0, 1)).clamp(0, 1)


class YCbCr:
    name = "ycbcr"
    M = torch.tensor([[.299, .587, .114], [-.299 * .564, -.587 * .564, (1 - .114) * .564],
                      [(1 - .299) * .713, -.587 * .713, -.114 * .713]])

    def forward(self, rgb):
        y, cb, cr = torch.einsum("ij,bjhw->bihw", self.M.to(rgb), rgb).unbind(1)
        return torch.stack([cb, cr, y], 1)

    def inverse(self, x):
        ycc = torch.stack([x[:, 2], x[:, 0], x[:, 1]], 1)
        return torch.einsum("ij,bjhw->bihw", torch.linalg.inv(self.M).to(x), ycc).clamp(0, 1)


class HVINoCk:
    name = "hvi_nock"

    def forward(self, rgb):
        h, s, v = _hsv(rgb)
        return torch.stack([s * torch.cos(2 * PI * h), s * torch.sin(2 * PI * h), v], 1)

    def inverse(self, x):
        a, b = x[:, 0].clamp(-1, 1), x[:, 1].clamp(-1, 1)
        s = torch.sqrt(a * a + b * b + EPS).clamp(0, 1)
        h = (torch.atan2(b + EPS, a + EPS) / (2 * PI)) % 1
        return _hsv_to_rgb(h, s, x[:, 2].clamp(0, 1)).clamp(0, 1)


class HVIUpstream:
    name = "hvi"

    def __init__(self, k=0.2):
        from net.HVI_transform import RGB_HVI
        self.t = RGB_HVI()
        with torch.no_grad():
            self.t.density_k.fill_(k)

    def forward(self, rgb):
        return self.t.HVIT(rgb)

    def inverse(self, x):
        return self.t.PHVIT(x)


ADAPTERS = (SRGB, HSV, YCbCr, HVINoCk, HVIUpstream)


def roundtrip(a, rgb):
    with torch.no_grad():
        x = a.forward(rgb)
        back = a.inverse(x)
    return x, (back - rgb).abs().max().item()


def near_black(a, n=4096, gen=None):
    """Inputs with max(R,G,B) < 1/255: round-trip error, chroma magnitude, and the inverse's
    gain (|d rgb| / |d chroma| for a 1e-3 chroma perturbation)."""
    rgb = torch.rand(n, 3, 1, 1, generator=gen) * (1 / 255) * torch.rand(n, 1, 1, 1, generator=gen)
    rgb = torch.cat([rgb, torch.zeros(1, 3, 1, 1)], 0)
    x, err = roundtrip(a, rgb)
    with torch.no_grad():
        d = torch.zeros_like(x)
        d[:, :2] = 1e-3
        gain = ((a.inverse(x + d) - a.inverse(x)).abs().amax(dim=(1, 2, 3)) / (1e-3 * math.sqrt(2))).max().item()
        black = a.inverse(a.forward(torch.zeros(1, 3, 1, 1))).abs().max().item()
    return {"n": n + 1, "max_abs_roundtrip_error": err,
            "max_abs_chroma": x[:, :2].abs().max().item(), "max_inverse_gain": gain,
            "black_maps_to_black_error": black}


def main():
    H.import_repo()
    gen = torch.Generator().manual_seed(0)
    torch.manual_seed(0)
    rgb = torch.rand(8, 3, 32, 40, generator=gen)
    grid = torch.stack(torch.meshgrid(*[torch.linspace(0, 1, 17)] * 3, indexing="ij"), 0).reshape(1, 3, 17, -1)
    out = {"written_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "torch": torch.__version__,
           "layout": "[chroma0, chroma1, intensity]", "adapters": {}}
    for cls in ADAPTERS:
        a = cls()
        x, e_rand = roundtrip(a, rgb)
        _, e_grid = roundtrip(a, grid)
        xg = torch.autograd.functional.jacobian(lambda z: a.inverse(a.forward(z)).sum(), rgb[:1, :, :2, :2])
        out["adapters"][a.name] = {
            "doc": next(l.strip() for l in __doc__.splitlines() if l.strip().startswith(a.name + " ")),
            "roundtrip_max_abs_error_random_uniform": e_rand,
            "roundtrip_max_abs_error_17x17x17_grid_incl_black_white_grey": e_grid,
            "chroma_range": [x[:, :2].min().item(), x[:, :2].max().item()],
            "intensity_range": [x[:, 2].min().item(), x[:, 2].max().item()],
            "differentiable": bool(torch.isfinite(xg).all()),
            "near_black_I_below_1_over_255": near_black(a, gen=gen),
        }
        print(a.name, json.dumps(out["adapters"][a.name], indent=None)[:400])
    dest = H.PAPER / "ralph" / "results" / "phase0_colorspace_roundtrip.json"
    H.json_save(dest, out)
    print("wrote", dest)


if __name__ == "__main__":
    main()
