# Sourced from ~/.bashrc (bootstrap.sh adds the line). Safe to source repeatedly.
export PERSIST=/home/work/research
export PAPER=$PERSIST/paper
export CLAUDE_CONFIG_DIR=$PERSIST/.claude      # keeps login + settings across session resets
export HERDR_MGR_HOME=$PAPER/herdr            # herdr_sync.py reads topology.json from the repo
export HERDR_SESSION=ralph
export UV_CACHE_DIR=$PERSIST/.cache/uv
export HF_HOME=$PERSIST/.cache/huggingface
export TORCH_HOME=$PERSIST/outputs/torch_cache
case ":$PATH:" in *":$PERSIST/tools/bin:"*) ;; *) export PATH="$PERSIST/tools/bin:$HOME/.local/bin:$PATH" ;; esac
# python env for experiments (system torch + project venv)
[ -f "$PERSIST/env/hvi/bin/activate" ] && VIRTUAL_ENV_DISABLE_PROMPT=1 source "$PERSIST/env/hvi/bin/activate"
