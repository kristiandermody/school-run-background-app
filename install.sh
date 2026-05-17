#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# School Run Tracker — Install Script
# Run once from Terminal:  bash install.sh
# ─────────────────────────────────────────────────────────────────────────────

set -e

echo ""
echo "╔══════════════════════════════════════╗"
echo "║   School Run Tracker — Installer     ║"
echo "╚══════════════════════════════════════╝"
echo ""

# ── Paths ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
INSTALL_DIR="$HOME/Development/school-run-background-app/SchoolRun"
PLIST_NAME="com.schoolrun.collector.plist"
AGENTS_DIR="$HOME/Library/LaunchAgents"
LOG_FILE="$HOME/Development/school-run-background-app/logs/school_run.log"
ERR_FILE="$HOME/Development/school-run-background-app/errors/school_run_error.log"
ENV_FILE="$SCRIPT_DIR/.env"

# ── Load .env ─────────────────────────────────────────────────────────────────
echo "→ Loading configuration from .env ..."

if [ ! -f "$ENV_FILE" ]; then
  echo ""
  echo "✗  No .env file found."
  echo "   Copy .env.example to .env and fill in your values, then re-run."
  echo "   cp .env.example .env"
  exit 1
fi

# shellcheck disable=SC1090
source "$ENV_FILE"

if [ -z "$SCHOOL_RUN_API_KEY" ] || [ -z "$SCHOOL_RUN_ORIGIN" ] || [ -z "$SCHOOL_RUN_DEST" ]; then
  echo ""
  echo "✗  .env is missing one or more required values."
  echo "   Check .env.example for the required variables."
  exit 1
fi

echo "  SCHOOL_RUN_ORIGIN: $SCHOOL_RUN_ORIGIN"
echo "  SCHOOL_RUN_DEST:   $SCHOOL_RUN_DEST"
echo "  SCHOOL_RUN_API_KEY: ***set***"

# ── Find Python 3 ─────────────────────────────────────────────────────────────
echo ""
echo "→ Locating Python 3..."
PYTHON=$(which python3 2>/dev/null || which python 2>/dev/null || echo "")

if [ -z "$PYTHON" ]; then
  echo ""
  echo "✗  Python 3 not found."
  echo "   Install it from https://www.python.org/downloads/ then re-run this script."
  exit 1
fi

PY_VERSION=$($PYTHON --version 2>&1)
echo "  Found: $PYTHON  ($PY_VERSION)"

# ── Create directories ─────────────────────────────────────────────────────────
echo ""
echo "→ Installing to $INSTALL_DIR ..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$HOME/Development/school-run-background-app/logs"
mkdir -p "$HOME/Development/school-run-background-app/errors"
mkdir -p "$HOME/Development/school-run-background-app/csv"

# Copy collector script
cp "$SCRIPT_DIR/school_run_collector.py" "$INSTALL_DIR/school_run_collector.py"
chmod +x "$INSTALL_DIR/school_run_collector.py"

echo "  Files copied."

# ── Build plist with real paths and env vars ───────────────────────────────────
echo ""
echo "→ Configuring launchd service..."

PLIST_SRC="$SCRIPT_DIR/$PLIST_NAME"
PLIST_DEST="$AGENTS_DIR/$PLIST_NAME"

mkdir -p "$AGENTS_DIR"

sed \
  -e "s|PYTHON_PATH|$PYTHON|g" \
  -e "s|SCRIPT_PATH|$INSTALL_DIR/school_run_collector.py|g" \
  -e "s|LOG_PATH|$LOG_FILE|g" \
  -e "s|ERR_PATH|$ERR_FILE|g" \
  -e "s|API_KEY_VALUE|$SCHOOL_RUN_API_KEY|g" \
  -e "s|ORIGIN_VALUE|$SCHOOL_RUN_ORIGIN|g" \
  -e "s|DEST_VALUE|$SCHOOL_RUN_DEST|g" \
  "$PLIST_SRC" > "$PLIST_DEST"

echo "  Plist written to $PLIST_DEST"

# ── Unload old version if already running ──────────────────────────────────────
launchctl unload "$PLIST_DEST" 2>/dev/null || true

# ── Load the service ───────────────────────────────────────────────────────────
echo ""
echo "→ Starting service..."
launchctl load "$PLIST_DEST"

# ── Run once immediately to test ───────────────────────────────────────────────
echo ""
echo "→ Running a test check right now..."
export SCHOOL_RUN_API_KEY SCHOOL_RUN_ORIGIN SCHOOL_RUN_DEST
$PYTHON "$INSTALL_DIR/school_run_collector.py"

# ── Done ───────────────────────────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  ✓  Installation complete!                                   ║"
echo "║                                                              ║"
echo "║  The collector runs every 5 min during:                      ║"
echo "║    • Morning:   7:00am – 10:00am  (weekdays)                 ║"
echo "║    • Afternoon: 2:30pm –  5:00pm  (weekdays)                 ║"
echo "║                                                              ║"
echo "║  Data saved to: csv/school_run_data.csv                      ║"
echo "║  Log file at:   logs/school_run.log                          ║"
echo "║                                                              ║"
echo "║  To uninstall:                                               ║"
echo "║    launchctl unload $PLIST_DEST"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
