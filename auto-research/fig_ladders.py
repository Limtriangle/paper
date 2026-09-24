"""fig_ladders — the lead figure (HVI-PLAN.md §6): (a) S1 loss ladder and (b) S2 representation
ladder as paired-by-seed deltas with Holm-adjusted 95% CIs and verdict markers; (c) the per-GT-
intensity-decile A0 - A2 mechanism difference with seed-level CIs and the darkness stress-test
dose-response as an inset.

    python3 auto-research/fig_ladders.py                       # reads ralph/results/s{1,2}__*_v1.json
                                                              # -> writing/figures/fig_ladders.pdf (+ .sources.json)
    python3 auto-research/fig_ladders.py --s1 X --s2 Y --out DIR/fig.pdf --synthetic   # test render (watermarked)

Every plotted number comes from a JSON key of the contract (DECISIONS 2026-09-24 05:20):
analysis.analysis_s{1,2}.decision.contrasts.<A-B>.{mean,ci_holm,verdict} and
analysis.analysis_s2.decision.mechanism_A0_vs_A2.{hue_err|delta_e00}.per_decile[k].{mean,ci95},
.stress.{delta_hue_err_A0_minus_A2,ci95}. The PDF metadata and the sidecar carry the sources' sha256.
Grayscale-safe: verdicts are encoded by marker shape and fill as well as hue; ICML full width (6.75 in).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import hvilib as H  # noqa: E402

# reference palette (dataviz skill, validated): slot 1 blue, slot 2 orange; ink and neutrals
INK, INK2, GRID, BAND = "#0b0b0b", "#52514e", "#d9d8d3", "#f0efec"
VERDICT = {"contributes": {"color": "#2a78d6", "marker": "o", "fill": "#2a78d6", "label": "contributes"},
           "removable": {"color": "#eb6834", "marker": "o", "fill": "white", "label": "removable"},
           "inconclusive": {"color": INK2, "marker": "s", "fill": INK2, "label": "inconclusive"},
           "missing": {"color": GRID, "marker": "x", "fill": GRID, "label": "not run"}}
SESOI = 0.3
S1_ROWS = [("L0-L1", "L0$-$L1  VGG on HVI"), ("L1-L2", "L1$-$L2  $k$ in the loss"),
           ("L2-L3", "L2$-$L3  HVI supervision"), ("L2-L4", "L2$-$L4  $C_k$-weighted chroma")]
S2_ROWS = [("A0-A1", "A0$-$A1  learned vs fixed $k$"), ("A0-A2", "A0$-$A2  $C_k$ ($k$ = 0)"),
           ("A2-A3", "A2$-$A3  polar vs linear chroma"), ("A3-A4", "A3$-$A4  max vs luma")]


def style():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
                         "font.size": 7.5, "axes.labelsize": 7.5, "axes.titlesize": 8, "xtick.labelsize": 7,
                         "ytick.labelsize": 7, "legend.fontsize": 6.5, "axes.edgecolor": INK2, "axes.linewidth": 0.5,
                         "xtick.color": INK2, "ytick.color": INK2, "text.color": INK, "axes.labelcolor": INK,
                         "pdf.fonttype": 42, "ps.fonttype": 42})
    return plt


def ladder_panel(ax, decision, rows, title):
    contrasts = decision.get("contrasts", {})
    ys = list(range(len(rows)))[::-1]
    ax.axvspan(-SESOI, SESOI, color=BAND, lw=0, zorder=0)
    ax.axvline(0, color=INK2, lw=0.6, zorder=1)
    xs = [abs(x) for c in contrasts.values() if "mean" in c for x in c.get("ci_holm", c.get("ci95", [0, 0]))]
    lim = max(0.6, (max(xs) if xs else 0.5) * 1.15)
    for y, (key, label) in zip(ys, rows):
        c = contrasts.get(key, {})
        v = c.get("verdict", "missing") if "mean" in c else "missing"
        st = VERDICT[v]
        if "mean" in c:
            lo, hi = c.get("ci_holm", c.get("ci95"))
            ax.plot([lo, hi], [y, y], color=st["color"], lw=1.2, solid_capstyle="butt", zorder=2)
            ax.plot(c["mean"], y, marker=st["marker"], ms=5, mfc=st["fill"], mec=st["color"], mew=1.0, ls="", zorder=3)
            n = c.get("n")
            label = f"{label}  $n$={n}" if n else label
        else:
            ax.plot(0, y, marker="x", ms=4, color=GRID, ls="", zorder=3)
            label = f"{label}   (not run)"
        ax.text(-lim * 0.97, y + 0.36, label, fontsize=6.5, color=INK, va="center", ha="left", zorder=4)
    ax.set_yticks([])
    ax.set_ylim(-0.6, len(rows) - 0.2)
    ax.set_xlabel(r"$\Delta$ GT-mean PSNR (dB), paired by seed")
    ax.set_title(title, loc="left", fontweight="bold")
    ax.grid(axis="x", color=GRID, lw=0.4, zorder=0)
    ax.tick_params(axis="y", length=0)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.set_xlim(-lim, lim)


def mechanism_panel(ax, decision, metric):
    mech = decision.get("mechanism_A0_vs_A2", {})
    m = mech.get(metric, {})
    per = m.get("per_decile", [])
    ylabel = {"hue_err": r"$\Delta$ hue err. $|\Delta h|\,S_{gt}$, A0$-$A2",
              "delta_e00": r"$\Delta\,\Delta E_{00}$, A0$-$A2"}[metric]
    ax.axvspan(-0.5, 2.5, color=BAND, lw=0, zorder=0)
    ax.axhline(0, color=INK2, lw=0.6, zorder=1)
    if per:
        xs = [d["decile"] for d in per]
        means = [d["mean"] for d in per]
        lo = [d["ci95"][0] for d in per]
        hi = [d["ci95"][1] for d in per]
        ax.fill_between(xs, lo, hi, color="#cde2fb", lw=0, zorder=1)
        ax.plot(xs, means, color="#2a78d6", lw=1.2, marker="o", ms=3, mfc="#2a78d6", mec="#2a78d6", zorder=3)
        ax.text(-0.4, 0.98, "bottom 3\ndeciles", transform=ax.get_xaxis_transform(), fontsize=6, color=INK2,
                va="top", ha="left")
    else:
        ax.text(0.5, 0.5, "mechanism keys not present", transform=ax.transAxes, ha="center", va="center", color=INK2)
    ax.set_xticks(range(10))
    ax.set_xticklabels([f"{k}" for k in range(10)])
    ax.set_xlabel("GT intensity decile (max RGB)")
    ax.set_ylabel(ylabel)
    ax.set_title("(c) Where the $C_k$ effect sits", loc="left", fontweight="bold")
    ax.grid(axis="y", color=GRID, lw=0.4, zorder=0)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    st = mech.get("stress", {})
    if st.get("factors"):
        ins = ax.inset_axes([0.50, 0.26, 0.47, 0.36])
        f = st["factors"]
        d = [st["delta_hue_err_A0_minus_A2"][k] for k in f]
        ci = [st["ci95"][k] for k in f]
        x = list(range(len(f)))
        ins.errorbar(x, d, yerr=[[v - c[0] for v, c in zip(d, ci)], [c[1] - v for v, c in zip(d, ci)]],
                     color="#2a78d6", lw=1.0, marker="o", ms=2.5, capsize=1.5, elinewidth=0.7)
        ins.axhline(0, color=INK2, lw=0.5)
        ins.set_xticks(x)
        ins.set_xticklabels([f"×{float(k):g}" for k in f], fontsize=6)
        ins.tick_params(axis="y", labelsize=6)
        ins.set_title("darkness stress: $\\Delta$ hue err", fontsize=6, pad=2)
        for s in ("top", "right"):
            ins.spines[s].set_visible(False)
        ins.patch.set_alpha(0.9)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    R = H.PAPER / "ralph" / "results"
    ap.add_argument("--s1", default=str(R / "s1__loss_ladder_v1.json"))
    ap.add_argument("--s2", default=str(R / "s2__rep_ladder_v1.json"))
    ap.add_argument("--out", default=str(H.PAPER / "writing" / "figures" / "fig_ladders.pdf"))
    ap.add_argument("--mechanism-metric", choices=("hue_err", "delta_e00"), default="hue_err")
    ap.add_argument("--synthetic", action="store_true", help="test render: watermark SYNTHETIC; never under writing/")
    ap.add_argument("--png", action="store_true", help="also write a PNG preview next to the PDF")
    a = ap.parse_args()
    out = Path(a.out).resolve()
    if a.synthetic:
        H.require("writing" not in out.parts, "a synthetic render must not be written under writing/")
    plt = style()
    from matplotlib.backends.backend_pdf import PdfPages
    srcs = {}
    decisions = {}
    for name, p in (("s1", a.s1), ("s2", a.s2)):
        p = Path(p)
        if p.is_file():
            d = H.json_load(p)
            srcs[p.name] = H.sha256_file(p)
            decisions[name] = d["analysis"][f"analysis_{name}"]["decision"]
            if d.get("synthetic") and not a.synthetic:
                raise RuntimeError(f"{p} is marked synthetic; pass --synthetic and an --out outside writing/")
        else:
            decisions[name] = {}
    fig, axes = plt.subplots(1, 3, figsize=(6.75, 2.35), gridspec_kw={"width_ratios": [1.0, 1.0, 1.0], "wspace": 0.45})
    ladder_panel(axes[0], decisions["s1"], S1_ROWS, "(a) Loss ladder (S1)")
    ladder_panel(axes[1], decisions["s2"], S2_ROWS, "(b) Representation ladder (S2)")
    mechanism_panel(axes[2], decisions["s2"], a.mechanism_metric)
    handles = [plt.Line2D([], [], marker=v["marker"], mfc=v["fill"], mec=v["color"], color=v["color"], ls="-", lw=1.2, ms=5,
                          label=v["label"]) for k, v in VERDICT.items() if k != "missing"]
    handles.append(plt.Rectangle((0, 0), 1, 1, color=BAND, label=f"±{SESOI} dB (smallest effect of interest)"))
    fig.legend(handles=handles, loc="lower center", ncol=4, frameon=False, bbox_to_anchor=(0.42, -0.06))
    fig.subplots_adjust(left=0.04, right=0.99, top=0.88, bottom=0.30)
    if a.synthetic:
        fig.text(0.5, 0.5, "SYNTHETIC SELF-TEST DATA — NOT A RESULT", ha="center", va="center", fontsize=22,
                 color="#e34948", alpha=0.35, rotation=20, zorder=10)
    fingerprint = {"figure": out.name, "written_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "script": "auto-research/fig_ladders.py",
                   "script_sha256": H.sha256_file(Path(__file__)), "sources": srcs, "synthetic": bool(a.synthetic),
                   "keys": ["analysis.analysis_s1.decision.contrasts.*.{mean,ci_holm,verdict}",
                            "analysis.analysis_s2.decision.contrasts.*.{mean,ci_holm,verdict}",
                            f"analysis.analysis_s2.decision.mechanism_A0_vs_A2.{a.mechanism_metric}.per_decile[*].{{mean,ci95}}",
                            "analysis.analysis_s2.decision.mechanism_A0_vs_A2.stress.{delta_hue_err_A0_minus_A2,ci95}"]}
    out.parent.mkdir(parents=True, exist_ok=True)
    meta = {"Title": "fig_ladders" + (" (SYNTHETIC)" if a.synthetic else ""), "Author": "experiment agent",
            "Subject": "sources: " + "; ".join(f"{k} sha256={v}" for k, v in srcs.items()) + (" | SYNTHETIC" if a.synthetic else ""),
            "Keywords": json.dumps(fingerprint["sources"])}
    with PdfPages(out, metadata=meta) as pdf:
        pdf.savefig(fig, bbox_inches="tight")
    H.json_save(out.with_suffix(".sources.json"), fingerprint)
    if a.png:
        fig.savefig(out.with_suffix(".png"), dpi=200, bbox_inches="tight")
    print("wrote", out, "and", out.with_suffix(".sources.json"))


if __name__ == "__main__":
    main()
