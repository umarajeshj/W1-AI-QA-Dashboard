import os
from pathlib import Path

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_PATH = PROJECT_ROOT / "data" / "raw" / "qa_dashboard_master_1000_records.csv"
REQUIRED_COLUMNS = {
    "Test Case ID",
    "Test Title",
    "Product Module",
    "Component Layer",
    "Tester Name",
    "Run Type",
    "Status",
    "Duration (ms)",
    "Environment",
    "Week Start Date",
    "Linked Defect ID",
    "Defect Severity",
    "Defect Status",
    "Automation Coverage (%)",
    "Execution Percentage (%)",
}


@st.cache_data(show_spinner=False)
def load_and_clean_data(source_path: str | Path = DEFAULT_DATA_PATH) -> pd.DataFrame:
    configured_path = os.getenv("QA_DASHBOARD_DATA")
    path = Path(configured_path) if configured_path and source_path == DEFAULT_DATA_PATH else Path(source_path)
    if not path.is_file():
        raise FileNotFoundError(f"QA dashboard data file not found: {path}")

    data = pd.read_csv(path)
    missing_columns = REQUIRED_COLUMNS.difference(data.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"CSV is missing required columns: {missing}")

    data["Week Start Date"] = pd.to_datetime(data["Week Start Date"], errors="coerce")
    for column in ("Linked Defect ID", "Defect Status"):
        values = data[column].astype("string").str.strip()
        data[column] = values.replace({"None": pd.NA, "": pd.NA})

    duration_ms = pd.to_numeric(data.pop("Duration (ms)"), errors="coerce")
    data["Duration_Sec"] = duration_ms.astype("float64") / 1000.0
    for column in ("Automation Coverage (%)", "Execution Percentage (%)"):
        data[column] = pd.to_numeric(data[column], errors="coerce")

    return data