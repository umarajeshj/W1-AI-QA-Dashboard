import pandas as pd

from qa_dashboard.data import load_and_clean_data
from qa_dashboard.metrics import compute_global_kpis


def _source_rows() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Test Case ID": "TC-1",
                "Test Title": "Create release",
                "Product Module": "Release Management",
                "Component Layer": "API",
                "Tester Name": "Avery Chen",
                "Run Type": "Integration",
                "Status": "Passed",
                "Duration (ms)": 1500,
                "Environment": "QA",
                "Week Start Date": "2026-09-28",
                "Linked Defect ID": "None",
                "Defect Severity": "None",
                "Defect Status": "None",
                "Automation Coverage (%)": 80,
                "Execution Percentage (%)": 95,
            },
            {
                "Test Case ID": "TC-2",
                "Test Title": "Approve release",
                "Product Module": "Release Management",
                "Component Layer": "UI",
                "Tester Name": "Jordan Patel",
                "Run Type": "Black Box",
                "Status": "Failed",
                "Duration (ms)": 2500,
                "Environment": "UAT",
                "Week Start Date": "2026-09-28",
                "Linked Defect ID": "DEF-1",
                "Defect Severity": "High",
                "Defect Status": "Closed",
                "Automation Coverage (%)": 60,
                "Execution Percentage (%)": 75,
            },
        ]
    )


def test_load_and_clean_data_parses_and_converts_columns(tmp_path):
    source_path = tmp_path / "qa.csv"
    _source_rows().to_csv(source_path, index=False)

    cleaned = load_and_clean_data(source_path)

    assert pd.api.types.is_datetime64_any_dtype(cleaned["Week Start Date"])
    assert pd.isna(cleaned.loc[0, "Linked Defect ID"])
    assert pd.isna(cleaned.loc[0, "Defect Status"])
    assert cleaned.loc[0, "Duration_Sec"] == 1.5
    assert "Duration (ms)" not in cleaned.columns


def test_compute_global_kpis_counts_runs_cases_and_closed_defects(tmp_path):
    source_path = tmp_path / "qa.csv"
    _source_rows().to_csv(source_path, index=False)
    cleaned = load_and_clean_data(source_path)

    kpis = compute_global_kpis(cleaned)

    assert kpis["total_test_cases"] == 2
    assert kpis["total_executions"] == 2
    assert kpis["passed"] == 1
    assert kpis["failed"] == 1
    assert kpis["defects_logged"] == 1
    assert kpis["defects_closed"] == 1
    assert kpis["pass_rate"] == 50.0
    assert kpis["automation_coverage"] == 70.0