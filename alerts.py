import streamlit as st
import pandas as pd

from history_manager import (
    get_history_files,
    load_history,
    compare_history
)

# ==================================================
# PAGE CONFIG
# ==================================================

st.set_page_config(
    page_title="Alerts Dashboard",
    page_icon="🔔",
    layout="wide"
)

# ==================================================
# HEADER
# ==================================================

st.title(
    "🔔 Alerts Dashboard"
)

st.caption(
    "Automatically detect sector score changes and momentum shifts."
)

# ==================================================
# LOAD HISTORY
# ==================================================

history_files = get_history_files()

if len(history_files) < 2:

    st.warning(
        """
At least 2 history snapshots are required.

Run sector_compare_live.py on different days first.
"""
    )

    st.stop()

# ==================================================
# LOAD LATEST SNAPSHOTS
# ==================================================

old_file = history_files[-2]
new_file = history_files[-1]

old_df = load_history(
    old_file
)

new_df = load_history(
    new_file
)

comparison_df = compare_history(
    old_df,
    new_df
)

if comparison_df.empty:

    st.warning(
        "Unable to compare history files."
    )

    st.stop()

# ==================================================
# ALERT COUNTS
# ==================================================

positive_alerts = len(
    comparison_df[
        comparison_df["Change"] > 0
    ]
)

negative_alerts = len(
    comparison_df[
        comparison_df["Change"] < 0
    ]
)

c1, c2, c3 = st.columns(3)

c1.metric(
    "Sectors Compared",
    len(comparison_df)
)

c2.metric(
    "Positive Alerts",
    positive_alerts
)

c3.metric(
    "Negative Alerts",
    negative_alerts
)

# ==================================================
# MAJOR IMPROVEMENTS
# ==================================================

st.subheader(
    "🚀 Major Positive Alerts"
)

positive_df = comparison_df[
    comparison_df["Change"] > 0
].sort_values(
    "Change",
    ascending=False
)

if positive_df.empty:

    st.info(
        "No positive alerts."
    )

else:

    for _, row in positive_df.iterrows():

        st.success(
            f"""
✅ {row['Sector']}

Previous Score: {row['Average Score_Old']:.2f}

Current Score: {row['Average Score_New']:.2f}

Improvement: +{row['Change']:.2f}
"""
        )

# ==================================================
# MAJOR DECLINES
# ==================================================

st.subheader(
    "📉 Negative Alerts"
)

negative_df = comparison_df[
    comparison_df["Change"] < 0
].sort_values(
    "Change"
)

if negative_df.empty:

    st.info(
        "No negative alerts."
    )

else:

    for _, row in negative_df.iterrows():

        st.error(
            f"""
⚠️ {row['Sector']}

Previous Score: {row['Average Score_Old']:.2f}

Current Score: {row['Average Score_New']:.2f}

Decline: {row['Change']:.2f}
"""
        )

# ==================================================
# RANKING CHANGES
# ==================================================

st.subheader(
    "🏆 Top Opportunity Alert"
)

best_sector = comparison_df.iloc[0]

st.success(
    f"""
Sector: {best_sector['Sector']}

Previous Score: {best_sector['Average Score_Old']:.2f}

Current Score: {best_sector['Average Score_New']:.2f}

Score Change: +{best_sector['Change']:.2f}

This sector currently has the strongest improving momentum.
"""
)

# ==================================================
# RISK ALERT
# ==================================================

st.subheader(
    "⚠️ Risk Alert"
)

worst_sector = comparison_df.iloc[-1]

st.error(
    f"""
Sector: {worst_sector['Sector']}

Previous Score: {worst_sector['Average Score_Old']:.2f}

Current Score: {worst_sector['Average Score_New']:.2f}

Score Change: {worst_sector['Change']:.2f}

This sector currently has the weakest momentum.
"""
)

# ==================================================
# ALERT TABLE
# ==================================================

st.subheader(
    "📋 Alert Details"
)

alert_df = comparison_df.copy()

alert_df["Alert"] = alert_df[
    "Change"
].apply(
    lambda x:
    "BUYING MOMENTUM"
    if x > 0
    else (
        "WEAKENING"
        if x < 0
        else "NEUTRAL"
    )
)

st.dataframe(
    alert_df,
    use_container_width=True,
    hide_index=True
)

# ==================================================
# STRATEGIC RECOMMENDATION
# ==================================================

st.subheader(
    "🎯 Strategic Recommendation"
)

focus_sectors = (
    positive_df
    .head(3)["Sector"]
    .tolist()
)

risk_sectors = (
    negative_df
    .head(3)["Sector"]
    .tolist()
)

st.success(
    f"""
✅ Focus On

{', '.join(focus_sectors) if focus_sectors else 'None'}

These sectors are improving and deserve priority research.
"""
)

st.warning(
    f"""
👀 Monitor Carefully

{', '.join(risk_sectors) if risk_sectors else 'None'}

These sectors are showing weakening momentum.
"""
)

# ==================================================
# FINAL INSIGHT
# ==================================================

st.info(
    """
📌 Alerts are generated by comparing the latest two historical sector snapshots.

📌 Positive score changes may indicate emerging opportunities.

📌 Negative score changes may indicate weakening sector strength.

📌 Use alerts together with Sector Comparison and Stock Drilldown for better decision-making.
"""
)