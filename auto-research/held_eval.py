"""held_eval — run an evaluation command on one GPU while holding it from the ladder queue; the hold file
is removed in a finally block (also on SIGTERM/SIGINT), so a stale hold cannot outlive the command.

    python3 auto-research/held_eval.py --gpu N -- <command ...>      # e.g. final_eval_test.py --oracle ...
Exit code = the command's. Master requirement 2026-09-24 (hold must be released even on failure).
"""
import argparse, os, signal, subprocess, sys
from pathlib import Path
HOLD_DIR = Path(os.environ.get("RESEARCH", "/home/work/research")) / "outputs" / "queue"


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--gpu", type=int, required=True)
    ap.add_argument("cmd", nargs=argparse.REMAINDER)
    a = ap.parse_args()
    cmd = a.cmd[1:] if a.cmd and a.cmd[0] == "--" else a.cmd
    if not cmd:
        sys.exit("no command given")
    hold = HOLD_DIR / f"hold_gpu{a.gpu}"
    HOLD_DIR.mkdir(parents=True, exist_ok=True)
    hold.write_text(f"held by pid {os.getpid()}: {' '.join(cmd)}\n")
    proc = None

    def forward(signum, frame):
        if proc and proc.poll() is None:
            proc.send_signal(signum)
    for s in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        signal.signal(s, forward)
    try:
        env = dict(os.environ, CUDA_VISIBLE_DEVICES=str(a.gpu))
        proc = subprocess.Popen(cmd, env=env)
        rc = proc.wait()
    finally:
        try:
            hold.unlink()
        except FileNotFoundError:
            pass
        print(f"[held_eval] hold_gpu{a.gpu} released", flush=True)
    sys.exit(rc)


if __name__ == "__main__":
    main()
