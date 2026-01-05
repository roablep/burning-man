#!/bin/bash
_is_sourced() {
  [[ "${BASH_SOURCE[0]:-}" != "${0}" ]]
}

if ! _is_sourced; then
  set -euo pipefail
fi

# chmod +x build-dev.sh
# ./build-dev.sh

show_help() {
  echo "Usage: build-dev.sh [OPTION]"
  echo "Builds the development environment using pyenv and Poetry."
  echo
  echo "Options:"
  echo "  --help            Display this help text and exit"
  echo "  --skip-venv       Skip rebuilding the virtual environment"
  echo
  echo "Examples:"
  echo "  ./build-dev.sh"
  echo "  ./build-dev.sh --skip-venv"
}

SKIP_VENV=false
while [[ "${1:-}" != "" ]]; do
  case "$1" in
    --help) show_help; exit 0 ;;
    --skip-venv) SKIP_VENV=true ;;
    *) echo "Unknown option: $1"; show_help; exit 1 ;;
  esac
  shift
done

brew_has_formula() {
  brew list --versions "$1" >/dev/null
}

pyenv_has_version() {
  pyenv prefix "$1" >/dev/null 2>&1
}

is_macos() {
  [[ "$(uname -s)" == "Darwin" ]]
}

ensure_homebrew() {
  if ! command -v brew >/dev/null 2>&1; then
    echo "Error: Homebrew is required on macOS for Tcl/Tk detection and install."
    echo "Install it from https://brew.sh and re-run."
    exit 1
  fi
}

# Ensure Tcl/Tk 8.6 is available (tcl-tk@8), and set build flags for pyenv.
# This prevents the '_tkinter' missing problem.
configure_tk_env_for_pyenv() {
  if ! is_macos; then
    return 0
  fi

  ensure_homebrew

  # If unversioned tcl-tk is installed, it may be Tcl/Tk 9 depending on brew state.
  # We strongly prefer tcl-tk@8 for Python builds.
  if brew list --formula | grep -q '^tcl-tk$'; then
    echo "Warning: Homebrew formula 'tcl-tk' is installed."
    echo "If this is Tcl/Tk 9, Python may build without tkinter."
    echo "Recommendation: brew uninstall tcl-tk && brew install tcl-tk@8"
  fi

  if ! brew_has_formula "tcl-tk@8"; then
    echo "Homebrew formula 'tcl-tk@8' not found. Installing it now..."
    brew install tcl-tk@8
  fi

  local TK_PREFIX
  TK_PREFIX="$(brew --prefix tcl-tk@8)"

  # Sanity check for separate libs (these must exist)
  if [[ ! -f "$TK_PREFIX/lib/libtcl8.6.dylib" || ! -f "$TK_PREFIX/lib/libtk8.6.dylib" ]]; then
    echo "Error: Expected Tcl/Tk 8.6 libs not found under: $TK_PREFIX/lib"
    echo "Expected: libtcl8.6.dylib and libtk8.6.dylib"
    echo "Try: brew reinstall tcl-tk@8"
    exit 1
  fi

  # Export build environment used by python-build (pyenv install)
  export PATH="$TK_PREFIX/bin:$PATH"
  export PKG_CONFIG_PATH="$TK_PREFIX/lib/pkgconfig"
  export CPPFLAGS="-I$TK_PREFIX/include"
  export LDFLAGS="-L$TK_PREFIX/lib"

  # Some python-build paths prefer explicit configure opts too.
  export PYTHON_CONFIGURE_OPTS="--with-tcltk-includes='-I$TK_PREFIX/include' --with-tcltk-libs='-L$TK_PREFIX/lib -ltcl8.6 -ltk8.6'"

  echo "Configured Tcl/Tk build env for pyenv using: $TK_PREFIX"
}

ensure_pyenv_version() {
  echo "Checking pyenv setup..."

  if ! command -v pyenv >/dev/null 2>&1; then
    echo "Error: 'pyenv' is not installed."
    echo "Please install pyenv first (e.g., 'brew install pyenv' on macOS)."
    exit 1
  fi

  if [ -f ".python-version" ]; then
    REQUIRED_VERSION="$(cat .python-version)"
  else
    echo "No .python-version file found. Creating one with default 3.11.9..."
    echo "3.11.9" > .python-version
    REQUIRED_VERSION="3.11.9"
  fi

  echo "Project requires Python version: $REQUIRED_VERSION"

  # Configure TK env *before* installing python so _tkinter compiles
  configure_tk_env_for_pyenv

  if ! pyenv_has_version "$REQUIRED_VERSION"; then
    echo "Python $REQUIRED_VERSION is not installed in pyenv. Installing now..."
    pyenv install "$REQUIRED_VERSION"
  else
    echo "Python $REQUIRED_VERSION is already installed in pyenv."
  fi

  pyenv local "$REQUIRED_VERSION"

  # Optional but useful: validate tkinter is present on macOS (fast fail)
  if is_macos; then
    echo "Verifying tkinter (_tkinter) is available..."
    local PYTHON_BIN
    PYTHON_BIN="$(pyenv prefix "$REQUIRED_VERSION")/bin/python"
    if ! "$PYTHON_BIN" -c "import tkinter; print('tk ok', __import__('tkinter').TkVersion)" >/dev/null 2>&1; then
      echo "ERROR: Python $REQUIRED_VERSION was installed but tkinter is missing."
      echo "This usually means pyenv built against the wrong Tcl/Tk."
      echo "Fix:"
      echo "  brew uninstall tcl-tk"
      echo "  brew reinstall tcl-tk@8"
      echo "  pyenv uninstall -f $REQUIRED_VERSION"
      echo "  ./build-dev.sh"
      exit 1
    fi
  fi
}

ensure_poetry() {
  if ! command -v poetry >/dev/null 2>&1; then
    echo "Error: 'poetry' is not installed."
    echo "Install it from https://python-poetry.org/docs/#installation and re-run."
    exit 1
  fi
}

rebuild_poetry_env() {
  local ENV_PATH
  if ENV_PATH="$(poetry env info -p 2>/dev/null)"; then
    echo "Removing existing Poetry environment at: $ENV_PATH"
    poetry env remove "$ENV_PATH"
  else
    echo "No existing Poetry environment found."
  fi
}

if [[ "$SKIP_VENV" == false ]]; then
  ensure_pyenv_version
  ensure_poetry

  if [ -t 0 ]; then
    echo "Step 1 will remove and rebuild the Poetry virtual environment using Python $REQUIRED_VERSION."
    echo "Are you sure? Type N to install libs only. (y/n)"
    read -r REPLY
    if [[ "$REPLY" =~ ^[Yy]$ ]]; then
      rebuild_poetry_env
    else
      echo "Skipping Poetry env rebuild, installing libraries only."
    fi
  else
    echo "Running in non-interactive shell, skipping Poetry env rebuild."
    echo "Skipping Poetry env rebuild, installing libraries only."
  fi
fi

echo "Installing dependencies with Poetry..."
poetry config virtualenvs.in-project true --local
poetry install

echo "Build script completed."
