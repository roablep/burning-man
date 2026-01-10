# Burning Man Theme Camp Dues Analysis

## Project Overview
This project is a data analysis and visualization tool focused on Burning Man Theme Camp dues and financial structures. It processes survey data to provide insights into camp budgets, individual contributions, and amenity offerings. The core of the project is a Streamlit application that allows users to interactively filter and explore the data.

**Key Technologies:**
*   **Language:** Python (>=3.11.6)
*   **Framework:** Streamlit
*   **Data Analysis:** Pandas, Statsmodels, Scikit-learn
*   **Visualization:** Altair, Plotly, Matplotlib, Seaborn
*   **Dependency Management:** Poetry

## Directory Structure
- `src/bm/` contains the core Burning Man workflows and the Streamlit app (`bm_streamlit_app.py`).
- `src/census/` holds census ingestion, cleaning, and analysis scripts plus `data/` inputs (CSV/JSON/MD).
- `reports/` stores generated analysis reports and writeups; `analysis_cache/` holds cached analysis artifacts.

## Getting Started

### Prerequisites
*   **Poetry:** Required for dependency management.
*   **Pyenv:** Recommended for Python version management.
*   **Homebrew (macOS):** Required for installing `tcl-tk@8` if running on macOS.

### Setup
*   `build-dev.sh`: A helper script to set up the development environment, particularly useful for handling macOS-specific dependencies like `tkinter`.
*   `activate.sh`: A convenience script to activate the virtual environment.

```bash
./build-dev.sh
```

This script will:
1.  Check/Install the required Python version using `pyenv`.
2.  Configure environment variables for `tkinter` (on macOS).
3.  Install project dependencies via `poetry`.
4.  Create a local virtual environment (`.venv`).

## Development Conventions
*   **Code Style:** The codebase follows standard Python conventions.
*   **Data Location:** Ensure raw data files (CSV) are placed in the `static/` directory.
*   **Visualization:** The app primarily uses Altair for interactive charts, with some Plotly and Matplotlib/Seaborn usage for specific specific plots.
