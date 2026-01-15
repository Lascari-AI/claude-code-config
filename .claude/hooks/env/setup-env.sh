#!/bin/bash
# .claude/hooks/env/setup-env.sh
# Activates virtual environments and language version managers at session start
# Environment changes are persisted via CLAUDE_ENV_FILE for all subsequent commands

set -e

# Capture environment before any changes
ENV_BEFORE=$(export -p | sort)

# Track what was activated
ACTIVATED=""

# --- Python Virtual Environment ---
VENV_PATHS=(
  "$CLAUDE_PROJECT_DIR/.venv"
  "$CLAUDE_PROJECT_DIR/venv"
  "$CLAUDE_PROJECT_DIR/.env"
  "$CLAUDE_PROJECT_DIR/env"
)

for venv in "${VENV_PATHS[@]}"; do
  if [ -f "$venv/bin/activate" ]; then
    source "$venv/bin/activate"
    ACTIVATED="${ACTIVATED}Python venv ($venv), "
    break
  fi
done

# --- pyenv ---
if [ -d "$HOME/.pyenv" ]; then
  export PYENV_ROOT="$HOME/.pyenv"
  export PATH="$PYENV_ROOT/bin:$PATH"
  if command -v pyenv &> /dev/null; then
    eval "$(pyenv init -)"
    if [ -f "$CLAUDE_PROJECT_DIR/.python-version" ]; then
      ACTIVATED="${ACTIVATED}pyenv ($(cat "$CLAUDE_PROJECT_DIR/.python-version")), "
    fi
  fi
fi

# --- Node.js via nvm ---
export NVM_DIR="${NVM_DIR:-$HOME/.nvm}"
if [ -s "$NVM_DIR/nvm.sh" ]; then
  source "$NVM_DIR/nvm.sh"
  if [ -f "$CLAUDE_PROJECT_DIR/.nvmrc" ]; then
    nvm use 2>/dev/null && ACTIVATED="${ACTIVATED}nvm ($(cat "$CLAUDE_PROJECT_DIR/.nvmrc")), "
  fi
fi

# --- Ruby via rbenv ---
if [ -d "$HOME/.rbenv" ]; then
  export PATH="$HOME/.rbenv/bin:$PATH"
  if command -v rbenv &> /dev/null; then
    eval "$(rbenv init -)"
    if [ -f "$CLAUDE_PROJECT_DIR/.ruby-version" ]; then
      ACTIVATED="${ACTIVATED}rbenv ($(cat "$CLAUDE_PROJECT_DIR/.ruby-version")), "
    fi
  fi
fi

# --- Go ---
if [ -f "$CLAUDE_PROJECT_DIR/go.mod" ]; then
  if [ -d "$HOME/go" ]; then
    export GOPATH="$HOME/go"
    export PATH="$GOPATH/bin:$PATH"
    ACTIVATED="${ACTIVATED}Go, "
  fi
fi

# --- Rust via rustup ---
if [ -f "$HOME/.cargo/env" ]; then
  source "$HOME/.cargo/env"
  if [ -f "$CLAUDE_PROJECT_DIR/Cargo.toml" ]; then
    ACTIVATED="${ACTIVATED}Rust/Cargo, "
  fi
fi

# --- Java via SDKMAN ---
if [ -s "$HOME/.sdkman/bin/sdkman-init.sh" ]; then
  source "$HOME/.sdkman/bin/sdkman-init.sh"
  if [ -f "$CLAUDE_PROJECT_DIR/.sdkmanrc" ]; then
    sdk env 2>/dev/null && ACTIVATED="${ACTIVATED}SDKMAN, "
  fi
fi

# --- Persist environment changes ---
if [ -n "$CLAUDE_ENV_FILE" ]; then
  ENV_AFTER=$(export -p | sort)
  # Find new/changed environment variables and write to env file
  comm -13 <(echo "$ENV_BEFORE") <(echo "$ENV_AFTER") >> "$CLAUDE_ENV_FILE"
fi

# --- Output summary (added to context) ---
if [ -n "$ACTIVATED" ]; then
  # Remove trailing ", "
  ACTIVATED="${ACTIVATED%, }"
  echo "Environment activated: $ACTIVATED"
else
  echo "No language-specific environment found to activate"
fi

exit 0
