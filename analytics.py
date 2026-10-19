# analytics.py
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

import categories
import database


def load_data(days=1):
    today = datetime.now().date()
    start = today - timedelta(days=days - 1)

    rows = database.get_usage(str(start), str(today))
    df = pd.DataFrame(rows, columns=["date", "hour", "app_name", "seconds"])

    if df.empty:
        return df

    df["category"] = df["app_name"].apply(categories.get_category)
    return df


def calculate_metrics(df, days=1):
    if df.empty:
        return {
            "score": 0,
            "productive_time": "0h 00m",
            "distracting_time": "0h 00m",
            "neutral_time": "0h 00m",
            "context_switches": 0,
            "focus_efficiency": 0.0,
        }

    prod_sec = df[df["category"] == "Productive"]["seconds"].sum()
    dist_sec = df[df["category"] == "Distracting"]["seconds"].sum()
    neut_sec = df[df["category"] == "Neutral"]["seconds"].sum()

    total_rated = prod_sec + dist_sec
    raw_score = (prod_sec / total_rated * 100) if total_rated > 0 else 0

    today = datetime.now().date()
    start = today - timedelta(days=days - 1)
    switches = database.get_switch_count(str(start), str(today))

    # Context switch penalty: High switching fragments attention
    hours_active = max((prod_sec + dist_sec + neut_sec) / 3600.0, 0.5)
    switches_per_hour = switches / hours_active
    penalty = min(switches_per_hour * 0.4, 25.0)
    focus_efficiency = max(0, round(raw_score - penalty, 1))

    return {
        "score": round(raw_score),
        "productive_time": format_time(prod_sec),
        "distracting_time": format_time(dist_sec),
        "neutral_time": format_time(neut_sec),
        "context_switches": switches,
        "focus_efficiency": focus_efficiency,
    }


def hourly_intensity_matrix(df):
    """Creates a 24-hour activity array grouped by category."""
    hours = np.arange(24)
    matrix = pd.DataFrame(0, index=hours, columns=categories.CATEGORY_NAMES)

    if not df.empty:
        grouped = df.groupby(["hour", "category"])["seconds"].sum().unstack(fill_value=0)
        for cat in categories.CATEGORY_NAMES:
            if cat in grouped.columns:
                matrix[cat] = grouped[cat]

    return matrix / 60.0  # converted to minutes


def top_apps_breakdown(df, n=6):
    if df.empty:
        return pd.Series(dtype=float)
    totals = df.groupby("app_name")["seconds"].sum().sort_values(ascending=False).head(n)
    return totals / 60.0


def weekly_trend(df):
    if df.empty:
        return pd.DataFrame(columns=categories.CATEGORY_NAMES)
    pivot = df.pivot_table(
        index="date",
        columns="category",
        values="seconds",
        aggfunc="sum",
        fill_value=0
    )
    pivot = pivot.reindex(columns=categories.CATEGORY_NAMES, fill_value=0)
    return pivot / 3600.0  # in hours


def generate_executive_insights(df):
    if df.empty:
        return ["No active telemetry logged yet. Click 'Start Tracking' to gather metrics."]

    insights = []
    by_app = df.groupby("app_name")["seconds"].sum()
    top_app = by_app.idxmax()
    insights.append(f"Top Application: {top_app} ({format_time(by_app.max())})")

    distracting = df[df["category"] == "Distracting"]
    if not distracting.empty:
        worst_app = distracting.groupby("app_name")["seconds"].sum().idxmax()
        worst_hour = distracting.groupby("hour")["seconds"].sum().idxmax()
        insights.append(f"Primary Vulnerability: {worst_app} peak at {worst_hour:02d}:00.")
    else:
        insights.append("Zero distraction leaks detected. Optimal focus maintained.")

    # High productivity window discovery
    productive = df[df["category"] == "Productive"]
    if not productive.empty:
        peak_hour = productive.groupby("hour")["seconds"].sum().idxmax()
        insights.append(f"Peak Flow Zone: {peak_hour:02d}:00 - {(peak_hour+1):02d}:00.")

    return insights


def format_time(seconds):
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return f"{hours}h {minutes:02d}m"


def export_csv(df, path):
    df.to_csv(path, index=False)