#!/usr/bin/env bash
# bootstrap.sh — make this compute session usable again after a reset.
#
# /home/work is EPHEMERAL (deleted when the Backend.AI session ends).
# /home/work/research is the persistent vfolder. Everything durable lives there;
# this script re-creates the symlinks, PATH, and user-space tools. Idempotent —
# run it as often as you like:
#
#     bash /home/work/research/paper/bootstrap.sh
#
set -euo pipefail

PERSIST=/home/work/research
PAPER=$PERSIST/paper
TOOLS=$PERSIST/tools
mkdir -p "$PAPER" "$TOOLS/bin" "$TOOLS/share" "$PERSIST/.claude" "$PERSIST/.config" "$PERSIST/.ssh"

link() { # link <target-in-persist> <path-in-home>
    local target=$1 path=$2
    if [ -L "$path" ] && [ "$(readlink -f "$path")" = "$(readlink -f "$target")" ]; then return; fi
    if [ -e "$path" ] && [ ! -L "$path" ]; then
        # migrate whatever the ephemeral home already has, then replace with a link
        if [ -d "$path" ]; then cp -an "$path"/. "$target"/ 2>/dev/null || true; rm -rf "$path"
        else cp -n "$path" "$target" 2>/dev/null || true; rm -f "$path"; fi
    fi
    rm -f "$path"
    ln -s "$target" "$path"
    echo "linked $path -> $target"
}

# --- 1. persistent locations -------------------------------------------------
link "$PAPER"                 /home/work/paper
link "$PERSIST/.claude"       "$HOME/.claude"
mkdir -p "$TOOLS/share/claude" "$PERSIST/.config/herdr" "$PERSIST/.config/herdr-mgr"
link "$TOOLS/bin"             "$HOME/.local/bin"
link "$TOOLS/share/claude"    "$HOME/.local/share/claude"
link "$PERSIST/.config/herdr"     "$HOME/.config/herdr"
link "$PERSIST/.config/herdr-mgr" "$HOME/.config/herdr-mgr"
[ -f "$PERSIST/.gitconfig" ] || cat > "$PERSIST/.gitconfig" <<'EOF'
[user]
	name = Limtriangle
	email = moselim0210@gmail.com
[init]
	defaultBranch = main
[pull]
	rebase = false
EOF
link "$PERSIST/.gitconfig" "$HOME/.gitconfig"

# --- 2. shell environment ----------------------------------------------------
ENVFILE=$PAPER/env.sh
if ! grep -q 'paper/env.sh' "$HOME/.bashrc" 2>/dev/null; then
    printf '\n# writing-driven-autoresearch environment\n[ -f %s ] && source %s\n' "$ENVFILE" "$ENVFILE" >> "$HOME/.bashrc"
    echo "added env.sh to ~/.bashrc"
fi
# shellcheck disable=SC1090
source "$ENVFILE"

# --- 3. GitHub deploy key (persistent) --------------------------------------
if [ ! -f "$PERSIST/.ssh/id_github" ]; then
    ssh-keygen -t ed25519 -N "" -C "gist-hvi paper deploy key" -f "$PERSIST/.ssh/id_github" >/dev/null
    echo "generated $PERSIST/.ssh/id_github — add the .pub as a DEPLOY KEY (write access) on github.com/Limtriangle/paper"
fi
if ! grep -q 'IdentityFile .*id_github' "$HOME/.ssh/config" 2>/dev/null; then
    cat >> "$HOME/.ssh/config" <<EOF

Host github.com
	IdentityFile $PERSIST/.ssh/id_github
	IdentitiesOnly yes
	StrictHostKeyChecking accept-new
EOF
    chmod 600 "$HOME/.ssh/config"
    echo "added github.com block to ~/.ssh/config"
fi

# --- 4. user-space tools (no sudo) ------------------------------------------
have() { command -v "$1" >/dev/null 2>&1; }

if ! have tectonic; then
    V=0.17.0
    echo "installing tectonic $V"
    curl -fsSL "https://github.com/tectonic-typesetting/tectonic/releases/download/tectonic%40$V/tectonic-$V-x86_64-unknown-linux-gnu.tar.gz" \
        | tar -xz -C "$TOOLS/bin" tectonic
fi

if ! have uv; then
    echo "installing uv"
    curl -LsSf https://astral.sh/uv/install.sh | UV_INSTALL_DIR="$TOOLS/bin" UV_NO_MODIFY_PATH=1 sh
fi

if ! have herdr; then
    echo "installing herdr"
    curl -fsSL https://herdr.dev/install.sh | sh
fi

if ! have claude; then
    echo "installing claude code"
    curl -fsSL https://claude.ai/install.sh | bash
fi

# --- 5. summary --------------------------------------------------------------
echo
echo "=== bootstrap summary ==="
for t in tectonic uv herdr claude git python3 nvidia-smi; do
    printf '  %-11s %s\n' "$t" "$(command -v $t 2>/dev/null || echo MISSING)"
done
echo "  paper       $(readlink -f /home/work/paper)"
echo "  claude cfg  $CLAUDE_CONFIG_DIR"
echo "  github key  $PERSIST/.ssh/id_github.pub"
