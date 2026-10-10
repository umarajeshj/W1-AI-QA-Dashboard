import pandas as pd


def compute_global_kpis(data: pd.DataFrame) -> dict[str, int | float]:
    statuses = data["Status"].astype("string").str.casefold()
    defect_ids = data["Linked Defect ID"].dropna()
    closed_statuses = data["Defect Status"].astype("string").str.casefold().isin(
        {"closed", "resolved"}
    )
    closed_defects = data.loc[closed_statuses, "Linked Defect ID"].dropna()
    execution_count = len(data)

    return {
        "total_test_cases": int(data["Test Case ID"].nunique()),
        "total_executions": execution_count,
        "passed": int(statuses.eq("passed").sum()),
        "failed": int(statuses.eq("failed").sum()),
        "defects_logged": int(defect_ids.nunique()),
        "defects_closed": int(closed_defects.nunique()),
        "pass_rate": float(statuses.eq("passed").sum() / execution_count * 100)
        if execution_count
        else 0.0,
        "automation_coverage": float(data["Automation Coverage (%)"].mean()),
        "execution_percentage": float(data["Execution Percentage (%)"].mean()),
    }