# rivanna-py

## Repo Setup

### Prerequisites
- **Poetry**: This project uses [Poetry](https://python-poetry.org/) for dependency management.
- **Pyenv**: Recommended for managing Python versions (handled by `build-dev.sh`).

### Quick Start
To set up your local environment for development, simply run:

```bash
./build-dev.sh
```

This script will:
1. Ensure the correct Python version (via `pyenv`) is installed.
2. Configure environment variables (especially for `tkinter` on macOS).
3. Install project dependencies using `poetry`.
4. Create a virtual environment inside the project (`.venv`).

### Activating the Environment
After running the build script, you can activate the virtual environment:

```bash
source .venv/bin/activate
# or
source activate.sh
```

Alternatively, you can run commands directly using `poetry run <command>`.

## Running the Streamlit server

You can run the Streamlit app using `poetry run`:

```bash
poetry run streamlit run src/bm/bm_streamlit_app.py
```

Or, if your environment is activated:

```bash
streamlit run src/bm/bm_streamlit_app.py
```
