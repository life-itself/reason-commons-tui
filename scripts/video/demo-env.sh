# Sourced, off camera, by demo.tape: a clean first start in a throwaway folder,
# using this checkout's code. Your own goals and settings are never touched.

DEMO="$(mktemp -d "${TMPDIR:-/tmp}/reason-commons-demo.XXXXXX")"
export REASON_COMMONS_HOME="$DEMO/ReasonCommons"
export REASON_COMMONS_CONFIG="$DEMO/settings.yaml"  # missing, so the app shows its first start
export REASON_COMMONS_PROVIDER=guided
export USER=mira  # the name the first start offers: "Mira"
unset ANTHROPIC_API_KEY

uv sync --quiet
export PATH="$PWD/.venv/bin:$PATH"
python3 scripts/video/seed_demo.py "$REASON_COMMONS_HOME"

cd "$DEMO" || return
export PS1='\[\e[38;5;244m\]~ \[\e[0m\]$ '
export BASH_SILENCE_DEPRECATION_WARNING=1
