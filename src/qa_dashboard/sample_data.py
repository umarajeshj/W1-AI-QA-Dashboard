import csv
import random
from datetime import date, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_PATH = PROJECT_ROOT / "data" / "raw" / "qa_dashboard_master_1000_records.csv"
FIELDNAMES = [
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
]

MODULES = {
    "Release Management": ["create release", "approve release", "rollback build"],
    "Test Execution": ["start test run", "retry failed case", "cancel execution"],
    "Defect Tracking": ["link defect", "update severity", "close resolved defect"],
    "User Access": ["assign role", "revoke access", "enforce permissions"],
    "Workflow Engine": ["route approval", "resume workflow", "handle timeout"],
    "Reporting": ["export report", "filter dashboard", "aggregate weekly metrics"],
    "Integrations": ["sync issue tracker", "retry webhook", "validate payload"],
    "Data Import": ["validate CSV", "reject malformed row", "import large file"],
    "Notifications": ["send alert", "suppress duplicate", "respect preferences"],
    "Configuration": ["save environment", "validate policy", "apply feature flag"],
}
LAYERS = ["UI", "API", "Workflow Engine", "SQL Server DB"]
LAYER_COVERAGE = {"UI": 57, "API": 78, "Workflow Engine": 69, "SQL Server DB": 74}
TESTERS = [
    "Avery Chen",
    "Jordan Patel",
    "Morgan Reed",
    "Taylor Brooks",
    "Casey Nguyen",
    "Riley Morgan",
    "Quinn Foster",
    "Jamie Rivera",
    "Drew Bennett",
    "Skyler James",
]
RUN_TYPES = [
    "UI Functional",
    "API Contract",
    "Integration",
    "Black Box",
    "Performance",
    "Regression",
    "Workflow",
]
STATUSES = ["Passed", "Failed", "Blocked", "Skipped", "In Progress"]
SEVERITIES = ["Critical", "High", "Medium", "Low"]
DEFECT_STATUSES = ["Open", "In Progress", "Fixed", "Closed", "Reopened"]
ENVIRONMENTS = ["QA", "UAT", "Staging", "Pre-Production"]


def _duration_ms(rng: random.Random, layer: str, run_type: str) -> int:
    if run_type == "Performance":
        return rng.randint(1800, 18000)
    ranges = {
        "UI": (350, 6500),
        "API": (25, 2400),
        "Workflow Engine": (180, 7200),
        "SQL Server DB": (12, 1300),
    }
    low, high = ranges[layer]
    return rng.randint(low, high)


def generate_sample_data(output_path: Path = OUTPUT_PATH, row_count: int = 1000) -> Path:
    rng = random.Random(20261009)
    first_week = date(2025, 10, 6)
    weeks = [first_week + timedelta(weeks=index) for index in range(53)]
    status_weights = [0.75, 0.13, 0.055, 0.045, 0.02]
    defect_weights = [0.34, 0.25, 0.14, 0.19, 0.08]
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=FIELDNAMES)
        writer.writeheader()
        for index in range(1, row_count + 1):
            module = rng.choice(list(MODULES))
            layer = rng.choices(LAYERS, weights=[0.32, 0.28, 0.22, 0.18], k=1)[0]
            run_type = rng.choice(RUN_TYPES)
            status = rng.choices(STATUSES, weights=status_weights, k=1)[0]
            defect_probability = {
                "Failed": 0.78,
                "Blocked": 0.48,
                "Passed": 0.025,
                "Skipped": 0.01,
                "In Progress": 0.015,
            }[status]
            has_defect = rng.random() < defect_probability
            defect_id = f"DEF-{index:05d}" if has_defect else "None"
            defect_status = rng.choices(DEFECT_STATUSES, weights=defect_weights, k=1)[0]
            if not has_defect:
                defect_status = "None"

            coverage = max(20, min(100, LAYER_COVERAGE[layer] + rng.randint(-19, 19)))
            if status in {"Blocked", "In Progress"}:
                execution_percentage = rng.randint(30, 84)
            else:
                execution_percentage = rng.randint(72, 100)

            writer.writerow(
                {
                    "Test Case ID": f"TC-{index:05d}",
                    "Test Title": f"{module}: {rng.choice(MODULES[module])}",
                    "Product Module": module,
                    "Component Layer": layer,
                    "Tester Name": rng.choice(TESTERS),
                    "Run Type": run_type,
                    "Status": status,
                    "Duration (ms)": _duration_ms(rng, layer, run_type),
                    "Environment": rng.choice(ENVIRONMENTS),
                    "Week Start Date": rng.choice(weeks).isoformat(),
                    "Linked Defect ID": defect_id,
                    "Defect Severity": rng.choice(SEVERITIES) if has_defect else "None",
                    "Defect Status": defect_status,
                    "Automation Coverage (%)": coverage,
                    "Execution Percentage (%)": execution_percentage,
                }
            )

    return output_path


def main() -> None:
    output_path = generate_sample_data()
    print(f"Generated 1,000 sample records: {output_path}")


if __name__ == "__main__":
    main()