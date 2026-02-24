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
- `src/bm/`: Core Burning Man workflows and the Streamlit app (`bm_streamlit_app.py`).
- `src/census_field_notes/`: Census ingestion, cleaning, and analysis scripts plus `data/` inputs.
- `src/census_next_gen_rs/`: Next generation census research scripts.
- `reports/`: Generated analysis reports and writeups.
- `analysis_cache/`: Cached analysis artifacts (JSON).
- `static/`: Raw data files (e.g., `Theme Camp Dues!.csv`).
- `tests/`: Project unit tests.

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
*   **Code Style:** Standard Python conventions (PEP 8).
*   **Data Location:** Ensure raw data files (CSV) are placed in the `static/` directory.
*   **Visualization:** Primarily uses Altair for interactive charts, with Plotly and Matplotlib/Seaborn for specific plots.

---

## Operational Protocols for Reliability (Self-Correction)

### 1. Verify Data Continuity (The "Ecosystem Check")
*   **Principle:** Do not build "islands" of code.
*   **Self-Check:** Trace a single data record through the *entire* lifecycle of the system.
    *   Does it leave Step 1 with the necessary IDs?
    *   Does it survive storage in Step 2?
    *   Is it fully present for the report in Step 3?
*   **Heuristic:** If an intermediate step drops data, the pipeline is broken, even if the code runs without error.

### 2. Boundary Skepticism
*   **Principle:** State and types are lost at every system boundary (File I/O, API calls, separate scripts).
*   **Self-Check:** Treat every `read` or `load` operation as "untrusted."
    *   Never assume a loaded CSV field is a list/dict; explicit parsing is required.
    *   Never assume an API call succeeded; explicit error handling/retries are required.

### 3. Defensive by Design
*   **Principle:** "Happy paths" are rare. Code for the missing state.
*   **Self-Check:** Instead of assuming data exists, explicitly handle the *absence* first.
    *   What if the column is missing? (Don't let it become NaN).
    *   What if the file is empty?
    *   What if the config is missing?

### 4. The "Constraint Audit"
*   **Principle:** "Main functionality" is not "Complete."
*   **Self-Check:** Before confirming completion, perform a line-by-line audit against the original plan.
    *   Did I implement the retries?
    *   Did I use the specific configuration flags?
    *   Did I preserve the exact output format requested?

## Data Persistence & Quality Assurance

### 1. Data Persistence & Schema Mandates
*   **Single Source of Truth:** When implementing data models backed by raw files (CSV/JSON), verify field parity. If a field exists in the model, it MUST exist in the data source.
*   **Round-Trip Verification:** For any storage layer implementation, verify the "Round Trip":
    1.  Create/Update Object -> Save to file.
    2.  Load from file -> Verify Data matches.
*   **Null Safety:** Never assume data files return clean types. Always explicitly handle `NULL` -> `None`/`[]` conversions before passing data to strict validation layers.

### 2. State Management Rules
*   **ID Continuity:** When performing "Upsert" operations, ensure the application-side ID matches the persistent ID.
*   **Timezone Consistency:** Always explicitly define the timezone strategy. Prefer storing UTC.

### 3. Self-Correction Protocol
*   **"What If It Exists?"**: Before implementing a `save()` function, ask: "What happens if this record already exists?" Ensure the logic handles updates as robustly as inserts.

## State Lifecycle & Edge Case Audit

### 1. The "Restart" Test (Persistence)
*   **Question:** "If the process crashes or restarts right now, what data is lost?"
*   **Rule:** Operational state MUST be persisted (e.g., `analysis_cache/`), not held in memory variables.

### 2. The "Replay" Test (Idempotency)
*   **Question:** "If I run this function twice on the same input, does it break or duplicate data?"
*   **Rule:** All processing loops MUST check for existence before processing.

### 3. The "Abort" Test (Null Safety)
*   **Question:** "What if the user cancels, the file is empty, or the API returns nothing?"
*   **Rule:** Never perform operations (like `.split()` or index access `[0]`) on the result of an I/O operation without a prior `if result:` check.

## System Integration & Lifecycle Mandates

### 1. The "Producer-Consumer" Contract
*   **Rule:** For every piece of data you save (Producer), you MUST identify or implement the code that reads and acts upon it (Consumer).

### 2. Robust Identification
*   **Rule:** When relying on external IDs, always implement a deterministic fallback strategy (e.g., hashing content) if the external ID is missing.

### 3. Component Usage Verification
*   **Rule:** Before marking a phase as complete, verify that all newly created helper classes are actually imported and invoked.
