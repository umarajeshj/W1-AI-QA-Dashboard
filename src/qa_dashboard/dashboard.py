import pandas as pd
import plotly.express as px
import streamlit as st

from qa_dashboard.data import load_and_clean_data
from qa_dashboard.metrics import compute_global_kpis

EMPTY_STATE_MESSAGE = "No test case executions found for the selected global filter criteria."
STATUS_COLORS = {
    "Passed": "#158f73",
    "Failed": "#d85b51",
    "Blocked": "#d39b32",
    "Skipped": "#8b98a5",
    "In Progress": "#477ca8",
}
CHART_TEMPLATE = "plotly_white"


def render_global_sidebar_filters(data: pd.DataFrame) -> pd.DataFrame:
    st.sidebar.header("Global filters")
    if data.empty:
        return data

    filtered = data.copy()
    earliest = data["Week Start Date"].min().date()
    latest = data["Week Start Date"].max().date()
    selected_dates = st.sidebar.date_input(
        "Week start date",
        value=(earliest, latest),
        min_value=earliest,
        max_value=latest,
    )
    if isinstance(selected_dates, (tuple, list)) and len(selected_dates) == 2:
        start_date, end_date = pd.Timestamp(selected_dates[0]), pd.Timestamp(selected_dates[1])
        filtered = filtered[
            filtered["Week Start Date"].between(start_date, end_date, inclusive="both")
        ]
    elif isinstance(selected_dates, (tuple, list)) and len(selected_dates) == 1:
        selected_date = pd.Timestamp(selected_dates[0])
        filtered = filtered[filtered["Week Start Date"].eq(selected_date)]

    filter_columns = [
        ("Product module", "Product Module"),
        ("Component layer", "Component Layer"),
        ("Tester", "Tester Name"),
        ("Environment", "Environment"),
        ("Run type", "Run Type"),
        ("Test status", "Status"),
    ]
    for label, column in filter_columns:
        options = sorted(data[column].dropna().astype(str).unique().tolist())
        selected = st.sidebar.multiselect(label, options, default=options)
        filtered = filtered[filtered[column].astype(str).isin(selected)]

    st.sidebar.caption(f"{len(filtered):,} of {len(data):,} executions in view")
    return filtered


def render_tab_overview(filtered_data: pd.DataFrame) -> None:
    if filtered_data.empty:
        st.info(EMPTY_STATE_MESSAGE)
        return

    st.subheader("Release health overview")
    kpis = compute_global_kpis(filtered_data)
    metric_columns = st.columns(6)
    metrics = [
        ("Test cases", f"{kpis['total_test_cases']:,}", "Unique cases in scope"),
        ("Passed", f"{kpis['passed']:,}", "Successful executions"),
        ("Failed", f"{kpis['failed']:,}", "Failed executions"),
        ("Defects logged", f"{kpis['defects_logged']:,}", "Unique linked defects"),
        ("Pass rate", f"{kpis['pass_rate']:.1f}%", "Of all executions"),
        (
            "Automation coverage",
            f"{kpis['automation_coverage']:.1f}%",
            "Average in selected scope",
        ),
    ]
    for column, (label, value, help_text) in zip(metric_columns, metrics):
        column.metric(label, value, help=help_text)

    status_trend = (
        filtered_data.groupby(["Week Start Date", "Status"], observed=True)
        .size()
        .reset_index(name="Executions")
        .sort_values("Week Start Date")
    )
    defects_by_week = (
        filtered_data.dropna(subset=["Linked Defect ID"])
        .groupby("Week Start Date", observed=True)["Linked Defect ID"]
        .nunique()
        .rename("Defects logged")
        .reset_index()
        .sort_values("Week Start Date")
    )
    outcome_counts = filtered_data["Status"].value_counts().rename_axis("Status").reset_index(
        name="Executions"
    )

    left, right = st.columns([1.55, 1])
    with left:
        st.markdown("#### Weekly execution trend")
        trend_chart = px.line(
            status_trend,
            x="Week Start Date",
            y="Executions",
            color="Status",
            markers=True,
            color_discrete_map=STATUS_COLORS,
            template=CHART_TEMPLATE,
        )
        trend_chart.update_layout(legend_title_text="Outcome", margin={"t": 12, "b": 8})
        st.plotly_chart(trend_chart, width="stretch")
    with right:
        st.markdown("#### Overall test proportion")
        outcome_chart = px.pie(
            outcome_counts,
            names="Status",
            values="Executions",
            hole=0.68,
            color="Status",
            color_discrete_map=STATUS_COLORS,
            template=CHART_TEMPLATE,
        )
        outcome_chart.update_traces(textposition="inside", textinfo="percent")
        outcome_chart.update_layout(showlegend=True, legend_title_text="Outcome", margin={"t": 12})
        st.plotly_chart(outcome_chart, width="stretch")

    lower_left, lower_right = st.columns([1.1, 1])
    with lower_left:
        st.markdown("#### Defects logged by week")
        defects_chart = px.bar(
            defects_by_week,
            x="Week Start Date",
            y="Defects logged",
            template=CHART_TEMPLATE,
            color_discrete_sequence=["#d85b51"],
        )
        defects_chart.update_layout(margin={"t": 12, "b": 8}, xaxis_title=None)
        st.plotly_chart(defects_chart, width="stretch")
    with lower_right:
        st.markdown("#### Release signals")
        failed_rate = kpis["failed"] / max(kpis["total_executions"], 1) * 100
        insights = [
            f"**{kpis['defects_closed']:,}** of **{kpis['defects_logged']:,}** linked defects are closed or resolved.",
            f"Execution completion averages **{kpis['execution_percentage']:.1f}%** in the selected scope.",
            f"Failed executions account for **{failed_rate:.1f}%** of the current run volume.",
        ]
        for insight in insights:
            st.markdown(f"- {insight}")


def render_tab_automation_maturity(filtered_data: pd.DataFrame) -> None:
    if filtered_data.empty:
        st.info(EMPTY_STATE_MESSAGE)
        return

    st.subheader("Automation maturity")
    coverage_mean = filtered_data["Automation Coverage (%)"].mean()
    execution_mean = filtered_data["Execution Percentage (%)"].mean()
    automated_cases = filtered_data.loc[
        filtered_data["Automation Coverage (%)"].ge(80), "Test Case ID"
    ].nunique()
    top_metrics = st.columns(3)
    top_metrics[0].metric("Average automation coverage", f"{coverage_mean:.1f}%")
    top_metrics[1].metric("Average execution completion", f"{execution_mean:.1f}%")
    top_metrics[2].metric("Cases at 80%+ coverage", f"{automated_cases:,}")

    module_summary = (
        filtered_data.groupby("Product Module", as_index=False, observed=True)
        .agg(
            **{
                "Automation Coverage (%)": ("Automation Coverage (%)", "mean"),
                "Execution Percentage (%)": ("Execution Percentage (%)", "mean"),
                "Executions": ("Test Case ID", "size"),
            }
        )
        .sort_values("Automation Coverage (%)")
    )
    layer_summary = (
        filtered_data.groupby("Component Layer", as_index=False, observed=True)
        .agg(
            **{
                "Automation Coverage (%)": ("Automation Coverage (%)", "mean"),
                "Execution Percentage (%)": ("Execution Percentage (%)", "mean"),
            }
        )
    )

    left, right = st.columns([1.2, 1])
    with left:
        st.markdown("#### Coverage vs. execution by module")
        maturity_chart = px.scatter(
            module_summary,
            x="Automation Coverage (%)",
            y="Execution Percentage (%)",
            size="Executions",
            color="Product Module",
            hover_name="Product Module",
            template=CHART_TEMPLATE,
        )
        maturity_chart.update_layout(margin={"t": 12, "b": 8}, legend_title_text="Module")
        st.plotly_chart(maturity_chart, width="stretch")
    with right:
        st.markdown("#### Coverage and execution by layer")
        layer_chart = px.bar(
            layer_summary,
            x="Component Layer",
            y=["Automation Coverage (%)", "Execution Percentage (%)"],
            barmode="group",
            color_discrete_sequence=["#247b70", "#477ca8"],
            template=CHART_TEMPLATE,
        )
        layer_chart.update_layout(margin={"t": 12, "b": 8}, legend_title_text=None)
        st.plotly_chart(layer_chart, width="stretch")

    st.markdown("#### Coverage distribution")
    distribution = px.box(
        filtered_data,
        x="Component Layer",
        y="Automation Coverage (%)",
        color="Component Layer",
        points="outliers",
        template=CHART_TEMPLATE,
    )
    distribution.update_layout(showlegend=False, margin={"t": 12, "b": 8})
    st.plotly_chart(distribution, width="stretch")


def render_tab_tester_velocity(filtered_data: pd.DataFrame) -> None:
    if filtered_data.empty:
        st.info(EMPTY_STATE_MESSAGE)
        return

    st.subheader("Tester velocity")
    tester_data = filtered_data.copy()
    normalized_status = tester_data["Status"].astype("string").str.casefold()
    normalized_defect_status = tester_data["Defect Status"].astype("string").str.casefold()
    tester_data["_passed"] = normalized_status.eq("passed").astype(int)
    tester_data["_failed"] = normalized_status.eq("failed").astype(int)
    tester_data["_closed_defect"] = tester_data["Linked Defect ID"].where(
        normalized_defect_status.isin({"closed", "resolved"})
    )
    summary = (
        tester_data.groupby("Tester Name", as_index=False, observed=True)
        .agg(
            Executions=("Test Case ID", "size"),
            Passed=("_passed", "sum"),
            Failed=("_failed", "sum"),
            **{
                "Average duration (sec)": ("Duration_Sec", "mean"),
                "Defects logged": ("Linked Defect ID", "nunique"),
                "Defects closed": ("_closed_defect", "nunique"),
            },
        )
    )
    summary["Pass rate (%)"] = summary["Passed"] / summary["Executions"] * 100
    summary["Defect close rate (%)"] = (
        summary["Defects closed"] / summary["Defects logged"].replace(0, pd.NA) * 100
    ).fillna(0)

    logged_closed = summary.melt(
        id_vars="Tester Name",
        value_vars=["Defects logged", "Defects closed"],
        var_name="Defect measure",
        value_name="Defects",
    )
    st.markdown("#### Defects logged vs. closed by tester")
    defect_chart = px.bar(
        logged_closed,
        x="Tester Name",
        y="Defects",
        color="Defect measure",
        barmode="group",
        color_discrete_map={"Defects logged": "#d85b51", "Defects closed": "#158f73"},
        template=CHART_TEMPLATE,
    )
    defect_chart.update_layout(margin={"t": 12, "b": 8}, legend_title_text=None)
    st.plotly_chart(defect_chart, width="stretch")

    st.markdown("#### Tester execution summary")
    display_columns = [
        "Tester Name",
        "Executions",
        "Passed",
        "Failed",
        "Pass rate (%)",
        "Average duration (sec)",
        "Defects logged",
        "Defects closed",
        "Defect close rate (%)",
    ]
    st.dataframe(
        summary[display_columns].sort_values("Executions", ascending=False),
        hide_index=True,
        width="stretch",
        column_config={
            "Pass rate (%)": st.column_config.ProgressColumn(
                "Pass rate", min_value=0, max_value=100, format="%.1f%%"
            ),
            "Defect close rate (%)": st.column_config.ProgressColumn(
                "Defect close rate", min_value=0, max_value=100, format="%.1f%%"
            ),
            "Average duration (sec)": st.column_config.NumberColumn(format="%.2f s"),
        },
    )

    defects = filtered_data.dropna(subset=["Linked Defect ID"]).copy()
    st.markdown("#### Top defective suites")
    if defects.empty:
        st.caption("No linked defects are present in the selected scope.")
    else:
        defects["_closed_defect"] = defects["Linked Defect ID"].where(
            defects["Defect Status"].astype("string").str.casefold().isin({"closed", "resolved"})
        )
        suite_defects = (
            defects.groupby("Product Module", as_index=False, observed=True)
            .agg(
                **{
                    "Defects logged": ("Linked Defect ID", "nunique"),
                    "Defects closed": ("_closed_defect", "nunique"),
                }
            )
            .merge(
                filtered_data.groupby("Product Module", as_index=False, observed=True)[
                    "Automation Coverage (%)"
                ]
                .mean()
                .rename(columns={"Automation Coverage (%)": "Avg automation coverage (%)"}),
                on="Product Module",
            )
            .sort_values("Defects logged", ascending=False)
            .head(8)
        )
        st.dataframe(suite_defects, hide_index=True, width="stretch")


def render_tab_layer_stability(filtered_data: pd.DataFrame) -> None:
    if filtered_data.empty:
        st.info(EMPTY_STATE_MESSAGE)
        return

    st.subheader("Layer stability and defect risk")
    outcome_by_suite = (
        filtered_data.groupby(["Product Module", "Status"], observed=True)
        .size()
        .reset_index(name="Executions")
    )
    status_by_week = (
        filtered_data.groupby(["Week Start Date", "Status"], observed=True)
        .size()
        .reset_index(name="Executions")
        .sort_values("Week Start Date")
    )
    latency_by_layer = (
        filtered_data.groupby("Component Layer", as_index=False, observed=True)
        .agg(
            **{
                "Median duration (sec)": ("Duration_Sec", "median"),
                "P95 duration (sec)": ("Duration_Sec", lambda values: values.quantile(0.95)),
            }
        )
    )

    left, right = st.columns([1.2, 1])
    with left:
        st.markdown("#### Test outcome distribution by suite")
        suite_chart = px.bar(
            outcome_by_suite,
            x="Product Module",
            y="Executions",
            color="Status",
            barmode="stack",
            color_discrete_map=STATUS_COLORS,
            template=CHART_TEMPLATE,
        )
        suite_chart.update_layout(margin={"t": 12, "b": 8}, legend_title_text="Outcome")
        st.plotly_chart(suite_chart, width="stretch")
    with right:
        st.markdown("#### Test status distribution by week")
        weekly_status_chart = px.area(
            status_by_week,
            x="Week Start Date",
            y="Executions",
            color="Status",
            color_discrete_map=STATUS_COLORS,
            template=CHART_TEMPLATE,
        )
        weekly_status_chart.update_layout(margin={"t": 12, "b": 8}, legend_title_text="Outcome")
        st.plotly_chart(weekly_status_chart, width="stretch")

    lower_left, lower_right = st.columns([1.15, 1])
    with lower_left:
        st.markdown("#### Execution duration by layer")
        latency_chart = px.bar(
            latency_by_layer,
            x="Component Layer",
            y=["Median duration (sec)", "P95 duration (sec)"],
            barmode="group",
            color_discrete_sequence=["#477ca8", "#d39b32"],
            template=CHART_TEMPLATE,
        )
        latency_chart.update_layout(margin={"t": 12, "b": 8}, legend_title_text=None)
        st.plotly_chart(latency_chart, width="stretch")
    with lower_right:
        st.markdown("#### Open defect exposure by layer")
        unresolved = filtered_data[
            filtered_data["Linked Defect ID"].notna()
            & ~filtered_data["Defect Status"]
            .astype("string")
            .str.casefold()
            .isin({"closed", "resolved"})
        ]
        severity_counts = (
            unresolved.groupby(["Component Layer", "Defect Severity"], observed=True)
            .size()
            .reset_index(name="Open defects")
        )
        if severity_counts.empty:
            st.caption("No unresolved linked defects are present in the selected scope.")
        else:
            severity_chart = px.bar(
                severity_counts,
                x="Component Layer",
                y="Open defects",
                color="Defect Severity",
                barmode="stack",
                color_discrete_sequence=["#9ab2c1", "#d39b32", "#d85b51", "#8f3e48"],
                template=CHART_TEMPLATE,
            )
            severity_chart.update_layout(margin={"t": 12, "b": 8}, legend_title_text="Severity")
            st.plotly_chart(severity_chart, width="stretch")


def main() -> None:
    st.set_page_config(page_title="QA Dashboard", page_icon="QA", layout="wide")
    st.markdown(
        """
        <style>
        :root { --qa-ink: #172b35; --qa-muted: #627680; --qa-line: #dce5e5; }
        [data-testid="stAppViewContainer"] { background: #f5f8f7; }
        [data-testid="stSidebar"] { border-right: 1px solid var(--qa-line); }
        [data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid var(--qa-line);
            border-top: 3px solid #247b70;
            padding: 0.9rem 1rem;
        }
        h1, h2, h3 { color: var(--qa-ink); }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.title("QA Dashboard")
    st.caption("Release stability across UI, API, workflow, and data layers")

    try:
        data = load_and_clean_data()
    except (FileNotFoundError, ValueError) as error:
        st.error(str(error))
        st.stop()

    filtered_data = render_global_sidebar_filters(data)
    overview_tab, automation_tab, tester_tab, layer_tab = st.tabs(
        ["Overview", "Automation maturity", "Tester velocity", "Layer & defect risk"]
    )
    with overview_tab:
        render_tab_overview(filtered_data)
    with automation_tab:
        render_tab_automation_maturity(filtered_data)
    with tester_tab:
        render_tab_tester_velocity(filtered_data)
    with layer_tab:
        render_tab_layer_stability(filtered_data)


if __name__ == "__main__":
    main()