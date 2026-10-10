# QA Dashboard

Enterprise-oriented QA test analytics built with Streamlit, Pandas, and Plotly. The dashboard
ships with a deterministic 1,000-record sample dataset at
`data/raw/qa_dashboard_master_1000_records.csv`.

## Run from GitHub

### Prerequisites

- Python 3.10 or later
- Git, if cloning the repository

Clone the repository and move into its directory:

```bash
git clone https://github.com/umarajeshj/W1-AI-QA-Dashboard.git
cd W1-AI-QA-Dashboard
```

Alternatively, download and extract the repository ZIP from GitHub, then open a terminal in the
extracted project directory.

Create and activate a virtual environment, then install the app and its dependencies.

**Windows PowerShell**

```bash
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
```

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

Start the dashboard from the project directory:

```bash
streamlit run app.py
```

Streamlit prints a local URL in the terminal; the default is <http://localhost:8501>.

## Development

Install the optional test and lint tools in the active virtual environment:

```bash
python -m pip install -e ".[dev]"
python -m pytest
python -m ruff check app.py src/qa_dashboard tests
```

The included sample data is used by default. To use another CSV with the same column schema, set
`QA_DASHBOARD_DATA` to its path before starting Streamlit. To recreate the included sample file,
run `python -m qa_dashboard.sample_data` after installing the project.
