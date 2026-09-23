"""c1_arms — representation arms and losses for the C1 ladder (ralph/related/redteam/R2 §Revised
minimal design). Same CIDNet body in every arm; only the working representation (what the
I-branch sees, what the HV-branch emits, where the residual is taken) and the loss change.

    python3 auto-research/c1_arms.py --preflight   # CPU, one fwd/bwd per arm -> ralph/results/phase0_arms_preflight.json

Arms (I-branch input / 3-ch working tensor [c0, c1, I] / loss):
  A0  HVI, learned k (upstream RGB_HVI)                         / frozen
  A2  HVI with k = 0 (C_k = 1: I = max, S cos h, S sin h)        / frozen
  A3  I = max(R,G,B), chroma = (Cb, Cr) BT.601 (Y recovered as max - max(d))   / frozen
  A4  YCbCr: I = Y, chroma = (Cb, Cr)                             / frozen
  L1  as A0                                                      / rgb_only
  R   split-less reference: I-branch sees Y, HV-branch sees RGB and emits a 3-ch RGB residual
      (HVD_block0 is a 36->3 conv, +324 parameters); out = rgb + hv_0 + i_dec0 (broadcast) / frozen
  U   as A0                                                      / upstream (coupled learned k, VGG on HVI)

Losses:
  frozen    L_rgb (L1 + 0.5 SSIM + 50 edge + 0.01 VGG) + L_hvi at constant k0 (L1 + 0.5 SSIM + 50 edge,
            NO VGG); the loss-side transform is a separate RGB_HVI with density_k = k0, requires_grad False:
            no gradient reaches any k through the loss.
  rgb_only  L_rgb only.
  upstream  hvilib.UpstreamLoss: train.py:60-64 verbatim, HVIT with the model's learnable k, VGG on both.

Transforms run in FP32 with autocast disabled. Test-time knobs (gated, gated2/alpha, gamma) are
identity in every arm. The residual is added in the working space, then decoded.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import torch
import torch.nn as nn

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import hvilib as H  # noqa: E402

LADDER = ("A0", "A2", "A3", "A4", "L1", "U")   # identical parameter counts by construction
ARMS = {"A0": ("hvi", "frozen"), "A2": ("hvi_k0", "frozen"), "A3": ("max_cbcr", "frozen"),
        "A4": ("ycbcr", "frozen"), "L1": ("hvi", "rgb_only"), "R": ("rgb_residual", "frozen"),
        "U": ("hvi", "upstream")}
K0_DEFAULT = 0.2          # upstream init value; frozen in the loss transform
BT601 = torch.tensor([[.299, .587, .114], [-.299 * .564, -.587 * .564, (1 - .114) * .564],
                      [(1 - .299) * .713, -.587 * .713, -.114 * .713]])


def _no_autocast(x):
    return torch.autocast(device_type=x.device.type, enabled=False)


def ycbcr(rgb):
    return torch.einsum("ij,bjhw->bihw", BT601.to(rgb), rgb)           # (Y, Cb, Cr)


def ycbcr_inverse(y, cb, cr):
    ycc = torch.stack([y, cb, cr], 1)
    return torch.einsum("ij,bjhw->bihw", torch.linalg.inv(BT601).to(ycc), ycc)


class ArmNet(nn.Module):
    """CIDNet body (net/CIDNet.py:74-119 transcribed) between an encode() and a decode()."""

    def __init__(self, arm, channels=None, heads=None, seed=None):
        super().__init__()
        H.require(arm in ARMS, f"unknown arm {arm}")
        self.arm, (self.rep, self.loss_kind) = arm, ARMS[arm]
        self.net = H.build_model(channels, heads)                       # seeded by the caller
        self.trans = self.net.trans                                     # infer() toggles knobs here
        self.trans.gated = self.trans.gated2 = False
        self.trans.alpha, self.trans.alpha_s = 1.0, 1.3
        if self.rep == "hvi_k0":
            with torch.no_grad():
                self.trans.density_k.fill_(0.0)
            self.trans.density_k.requires_grad_(False)
        if self.rep == "rgb_residual":
            ch1 = self.net.HVD_block0[1].in_channels
            g = torch.Generator().manual_seed((seed or 0) + 777)        # shared layers keep matched init
            conv = nn.Conv2d(ch1, 3, 3, stride=1, padding=0, bias=False)
            with torch.no_grad():
                conv.weight.copy_(torch.empty_like(conv.weight).uniform_(
                    -1, 1, generator=g) * (1 / (ch1 * 9)) ** 0.5)          # kaiming-uniform bound
            self.net.HVD_block0[1] = conv

    # ---- representation -------------------------------------------------------------
    def encode(self, rgb):
        """rgb [0,1] -> (x3 working tensor, i1 I-branch input), FP32."""
        rgb = rgb.float()
        with _no_autocast(rgb):
            if self.rep in ("hvi", "hvi_k0"):
                x = self.trans.HVIT(rgb)                                # net/HVI_transform.py:16-47
                return x, x[:, 2:3]
            y, cb, cr = ycbcr(rgb).unbind(1)
            if self.rep == "ycbcr":
                x = torch.stack([cb, cr, y], 1)
                return x, x[:, 2:3]
            if self.rep == "max_cbcr":
                m, _ = rgb.max(1)
                x = torch.stack([cb, cr, m], 1)
                return x, x[:, 2:3]
            return rgb, y.unsqueeze(1)                                   # rgb_residual

    def decode(self, out):
        with _no_autocast(out):
            out = out.float()
            if self.rep in ("hvi", "hvi_k0"):
                return self.trans.PHVIT(out)                            # net/HVI_transform.py:49-122
            if self.rep == "ycbcr":
                return ycbcr_inverse(out[:, 2].clamp(0, 1), out[:, 0], out[:, 1]).clamp(0, 1)
            if self.rep == "max_cbcr":
                cbp, crp = out[:, 0] / .564, out[:, 1] / .713
                d = torch.stack([crp, -(.299 * crp + .114 * cbp) / .587, cbp], 1)
                y = out[:, 2].clamp(0, 1).unsqueeze(1) - d.max(1, keepdim=True)[0]
                return (y + d).clamp(0, 1)
            return out.clamp(0, 1)                                       # rgb_residual

    # ---- CIDNet body, net/CIDNet.py:74-118 verbatim (names kept) -----------------------
    def body(self, hvi, i):
        n = self.net
        i_enc0 = n.IE_block0(i)
        i_enc1 = n.IE_block1(i_enc0)
        hv_0 = n.HVE_block0(hvi)
        hv_1 = n.HVE_block1(hv_0)
        i_jump0 = i_enc0
        hv_jump0 = hv_0
        i_enc2 = n.I_LCA1(i_enc1, hv_1)
        hv_2 = n.HV_LCA1(hv_1, i_enc1)
        v_jump1 = i_enc2
        hv_jump1 = hv_2
        i_enc2 = n.IE_block2(i_enc2)
        hv_2 = n.HVE_block2(hv_2)
        i_enc3 = n.I_LCA2(i_enc2, hv_2)
        hv_3 = n.HV_LCA2(hv_2, i_enc2)
        v_jump2 = i_enc3
        hv_jump2 = hv_3
        i_enc3 = n.IE_block3(i_enc2)
        hv_3 = n.HVE_block3(hv_2)
        i_enc4 = n.I_LCA3(i_enc3, hv_3)
        hv_4 = n.HV_LCA3(hv_3, i_enc3)
        i_dec4 = n.I_LCA4(i_enc4, hv_4)
        hv_4 = n.HV_LCA4(hv_4, i_enc4)
        hv_3 = n.HVD_block3(hv_4, hv_jump2)
        i_dec3 = n.ID_block3(i_dec4, v_jump2)
        i_dec2 = n.I_LCA5(i_dec3, hv_3)
        hv_2 = n.HV_LCA5(hv_3, i_dec3)
        hv_2 = n.HVD_block2(hv_2, hv_jump1)
        i_dec2 = n.ID_block2(i_dec3, v_jump1)
        i_dec1 = n.I_LCA6(i_dec2, hv_2)
        hv_1 = n.HV_LCA6(hv_2, i_dec2)
        i_dec1 = n.ID_block1(i_dec1, i_jump0)
        i_dec0 = n.ID_block0(i_dec1)
        hv_1 = n.HVD_block1(hv_1, hv_jump0)
        hv_0 = n.HVD_block0(hv_1)
        return hv_0, i_dec0

    def forward(self, rgb):
        x, i = self.encode(rgb)
        hv_0, i_dec0 = self.body(x.to(next(self.net.parameters()).dtype), i.to(next(self.net.parameters()).dtype))
        if self.rep == "rgb_residual":
            return self.decode(x + hv_0.float() + i_dec0.float())
        return self.decode(torch.cat([hv_0, i_dec0], dim=1).float() + x)  # net/CIDNet.py:119-120

    def HVIT(self, rgb):                                                 # for UpstreamLoss (arm U)
        return self.trans.HVIT(rgb)


# ---- losses -------------------------------------------------------------------------------
class FrozenLoss:
    """L_rgb (L1+0.5 SSIM+50 edge+0.01 VGG) + L_hvi at constant k0 (L1+0.5 SSIM+50 edge, no VGG)."""

    def __init__(self, k0=K0_DEFAULT, rgb_only=False, weights=None):
        from net.HVI_transform import RGB_HVI
        up = H.UpstreamLoss(weights)                                     # reuses the upstream modules
        self.L1, self.D, self.E, self.P = up.L1, up.D, up.E, up.P
        self.P_weight, self.HVI_weight, self.weights = up.P_weight, up.HVI_weight, up.weights
        self.rgb_only, self.k0 = rgb_only, k0
        self.hvi_k0 = RGB_HVI()
        with torch.no_grad():
            self.hvi_k0.density_k.fill_(k0)
        self.hvi_k0.density_k.requires_grad_(False)
        self.kind = "rgb_only" if rgb_only else "frozen"

    def __call__(self, model, out, gt):
        t = {"rgb_l1": self.L1(out, gt), "rgb_ssim": self.D(out, gt), "rgb_edge": self.E(out, gt),
             "rgb_perc": self.P_weight * self.P(out, gt)[0]}
        total = t["rgb_l1"] + t["rgb_ssim"] + t["rgb_edge"] + t["rgb_perc"]
        if not self.rgb_only:
            oh, gh = self.hvi_k0.HVIT(out.float()), self.hvi_k0.HVIT(gt.float())
            t.update(hvi_l1=self.L1(oh, gh), hvi_ssim=self.D(oh, gh), hvi_edge=self.E(oh, gh))
            total = total + self.HVI_weight * (t["hvi_l1"] + t["hvi_ssim"] + t["hvi_edge"])
        return total, t


def make_loss(kind, k0=K0_DEFAULT, weights=None):
    if kind == "upstream":
        f = H.UpstreamLoss(weights)
        f.kind = "upstream"
        return f
    return FrozenLoss(k0, rgb_only=(kind == "rgb_only"), weights=weights)


def build_arm(arm, seed, channels=None, heads=None):
    """Matched seeds: identical init for every shape-identical layer across arms."""
    H.seed_all(seed)
    return ArmNet(arm, channels, heads, seed=seed)


# ---- preflight ---------------------------------------------------------------------------
def preflight(verbose=True):
    H.import_repo()
    H.set_determinism(2)
    x, gt = torch.rand(2, 3, 32, 40), torch.rand(2, 3, 32, 40)
    report = {"written_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "k0": K0_DEFAULT, "arms": {}}
    with H.cpu_cuda_shim():
        # A0 body == upstream CIDNet.forward, bitwise, same weights
        torch.manual_seed(42)
        ref = H.build_model().eval()
        a0 = build_arm("A0", 42).eval()
        a0.net.load_state_dict(ref.state_dict())
        with torch.no_grad():
            H.require(torch.equal(a0(x), ref(x)), "A0 wrapper != upstream CIDNet forward")
        report["A0_equals_upstream_forward"] = "BITWISE"
        losses = {k: make_loss(k) for k in ("frozen", "rgb_only", "upstream")}
        for arm in ARMS:
            m = build_arm(arm, 42).train()
            loss_fn = losses[m.loss_kind]
            with torch.autocast("cpu", dtype=torch.bfloat16):          # transforms must stay FP32
                xr, ir = m.encode(x)
            H.require(xr.dtype == torch.float32 and ir.dtype == torch.float32, "transform left FP32")
            out = m(x)
            H.require(out.shape == x.shape and bool(out.isfinite().all()), f"{arm}: bad output")
            total, terms = loss_fn(m, out, gt)
            m.zero_grad(set_to_none=True)
            total.backward()
            grads = [p.grad for p in m.parameters() if p.grad is not None]
            H.require(grads and all(bool(g.isfinite().all()) for g in grads), f"{arm}: non-finite grads")
            k = m.trans.density_k
            if m.loss_kind != "upstream":
                H.require(loss_fn.hvi_k0.density_k.grad is None and not loss_fn.hvi_k0.density_k.requires_grad,
                          "loss-side k0 received a gradient")
            with torch.no_grad():
                rt = (m.decode(m.encode(x)[0]) - x).abs().max().item()
            report["arms"][arm] = {
                "representation": m.rep, "loss": loss_fn.kind,
                "parameters": H.count_parameters(m), "parameters_trainable": sum(p.numel() for p in m.parameters() if p.requires_grad),
                "model_k": {"value": k.item(), "learnable": bool(k.requires_grad), "grad": (k.grad.item() if k.grad is not None else None)},
                "loss_terms": {t: v.item() for t, v in terms.items()}, "loss_total": total.item(),
                "encode_decode_roundtrip_max_abs_err": rt,
                "output_dtype": str(out.dtype), "n_param_tensors_without_grad":
                    sum(1 for p in m.parameters() if p.requires_grad and p.grad is None)}
            if verbose:
                print(arm, json.dumps(report["arms"][arm])[:300])
    counts = {a: report["arms"][a]["parameters"] for a in LADDER}
    H.require(len(set(counts.values())) == 1, f"parameter counts differ across the ladder: {counts}")
    report["ladder_parameter_count"] = next(iter(counts.values()))
    report["R_parameter_count"] = report["arms"]["R"]["parameters"]
    report["R_minus_ladder"] = report["R_parameter_count"] - report["ladder_parameter_count"]
    report["test_time_knobs"] = {"gated": False, "gated2": False, "alpha": 1.0, "gamma": 1.0}
    report["note"] = ("CPU synthetic preflight, one forward/backward per arm; not a training result. "
                      "n_param_tensors_without_grad counts I_LCA5's 13 dead tensors (upstream) in every arm.")
    report["preflight"] = "PASS"
    dest = H.PAPER / "ralph" / "results" / "phase0_arms_preflight.json"
    H.json_save(dest, report)
    if verbose:
        print(json.dumps({k: v for k, v in report.items() if k != "arms"}, indent=1))
        print("wrote", dest)
        print("C1_ARMS_PREFLIGHT_PASSED")
    return report


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--preflight", action="store_true", required=True)
    ap.parse_args()
    preflight()
