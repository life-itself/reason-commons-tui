#!/bin/zsh
# Desktop apps need not inherit keys exported by interactive shell startup.
# Keep shell startup chatter away from MCP's stdio, and keep secrets out of config.
unsetopt XTRACE VERBOSE
if [[ -z "${ANTHROPIC_API_KEY:-}" && -r "${ZDOTDIR:-$HOME}/.zshrc" ]]; then
  source "${ZDOTDIR:-$HOME}/.zshrc" >/dev/null 2>&1
fi
unsetopt XTRACE VERBOSE
if [[ -n "${ANTHROPIC_API_KEY:-}" ]]; then
  export ANTHROPIC_API_KEY
fi
reason_commons_root="${0:A:h:h}"
exec "${reason_commons_root}/.venv/bin/python" -m reason_commons mcp "$@"
