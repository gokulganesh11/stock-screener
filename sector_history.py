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
    page_title="Sector History Dashboard",
    page_icon="📜",
    layout="wide"
)

# ==================================================
# HEADER
# ==================================================

st.title(
    "📜 Sector History Dashboard"
)

st.caption(
    "Track sector performance and score changes over time."
)

# ==================================================
# LOAD HISTORY FILES
# ==================================================

history_files = get_history_files()

if len(history_files) < 2:

    st.warning(
        """
At least 2 history files are required.

Run sector_compare_live.py on different days
to generate comparison history.
"""
    )

    st.stop()

# ==================================================
# FILE SELECTION
# ==================================================

st.subheader(
    "📂 Compare Snapshots"
)

col1, col2 = st.columns(2)

with col1:

    old_file = st.selectbox(
        "Previous Snapshot",
        history_files,
        index=max(
            0,
            len(history_files) - 2
        )
    )

with col2:

    new_file = st.selectbox(
        "Current Snapshot",
        history_files,
        index=len(history_files) - 1
    )

# ==================================================
# LOAD DATA
# ==================================================

old_df = load_history(
    old_file
)

new_df = load_history(
    new_file
)

# ==================================================
# COMPARISON
# ==================================================

comparison_df = compare_history(
    old_df,
    new_df
)

if comparison_df.empty:

    st.warning(
        """
Unable to compare history.

Check if both history files contain:
- Sector
- Average Score
"""
    )

    st.stop()

# ==================================================
# SUMMARY
# ==================================================

st.subheader(
    "📈 Summary"
)

top_gainer = comparison_df.iloc[0]
top_loser = comparison_df.iloc[-1]

c1, c2 = st.columns(2)

c1.metric(
    "Top Gaining Sector",
    top_gainer["Sector"],
    round(
        top_gainer["Change"],
        2
    )
)

c2.metric(
    "Top Losing Sector",
    top_loser["Sector"],
    round(
        top_loser["Change"],
        2
    )
)

# ==================================================
# CHANGES TABLE
# ==================================================

st.subheader(
    "📋 Sector Changes"
)

st.dataframe(
    comparison_df,
    use_container_width=True,
    hide_index=True
)

# ==================================================
# IMPROVING SECTORS
# ==================================================

st.subheader(
    "🚀 Improving Sectors"
)

for _, row in comparison_df.head(5).iterrows():

    st.success(
        f"""
{row['Sector']}

Previous Score: {round(row['Average Score_Old'], 2)}

Current Score: {round(row['Average Score_New'], 2)}

Change: +{round(row['Change'], 2)}
"""
    )

# ==================================================
# WEAKENING SECTORS
# ==================================================

st.subheader(
    "📉 Weakening Sectors"
)

for _, row in comparison_df.tail(5).iterrows():

    st.error(
        f"""
{row['Sector']}

Previous Score: {round(row['Average Score_Old'], 2)}

Current Score: {round(row['Average Score_New'], 2)}

Change: {round(row['Change'], 2)}
"""
    )

# ==================================================
# INSIGHTS
# ==================================================

st.subheader(
    "💡 Historical Insights"
)

improving_count = len(
    comparison_df[
        comparison_df["Change"] > 0
    ]
)

declining_count = len(
    comparison_df[
        comparison_df["Change"] < 0
    ]
)

stable_count = len(
    comparison_df[
        comparison_df["Change"] == 0
    ]
)

st.info(
    f"""
📈 Improving Sectors: {improving_count}

📉 Declining Sectors: {declining_count}

➖ Stable Sectors: {stable_count}

Focus on sectors showing consistent positive momentum.

Avoid making decisions based on a single snapshot.
"""
)

# ==================================================
# BEST MOMENTUM
# ==================================================

st.subheader(
    "🏅 Best Momentum Sector"
)

best_sector = comparison_df.iloc[0]

st.success(
    f"""
Sector: {best_sector['Sector']}

Previous Score: {round(best_sector['Average Score_Old'], 2)}

Current Score: {round(best_sector['Average Score_New'], 2)}

Change: +{round(best_sector['Change'], 2)}
"""
)

# ==================================================
# WEAKEST MOMENTUM
# ==================================================

st.subheader(
    "⚠️ Weakest Momentum Sector"
)

weak_sector = comparison_df.iloc[-1]

st.error(
    f"""
Sector: {weak_sector['Sector']}

Previous Score: {round(weak_sector['Average Score_Old'], 2)}

Current Score: {round(weak_sector['Average Score_New'], 2)}

Change: {round(weak_sector['Change'], 2)}
"""
)

# ==================================================
# TREND TABLE
# ==================================================

st.subheader(
    "📊 Trend Analysis"
)

trend_df = comparison_df.copy()

trend_df["Trend"] = trend_df[
    "Change"
].apply(
    lambda x:
    "📈 Improving"
    if x > 0
    else (
        "📉 Weakening"
        if x < 0
        else "➖ Stable"
    )
)

st.dataframe(
    trend_df,
    use_container_width=True,
    hide_index=True
)

# ==================================================
# RECOMMENDATION
# ==================================================

st.subheader(
    "🎯 Recommendation"
)

focus_list = (
    comparison_df[
        comparison_df["Change"] > 0
    ]["Sector"]
    .head(3)
    .tolist()
)

watch_list = (
    comparison_df[
        comparison_df["Change"] < 0
    ]["Sector"]
    .tail(3)
    .tolist()
)

st.success(
    f"""
✅ Focus On

{', '.join(focus_list) if focus_list else 'None'}

These sectors are improving.
"""
)

st.warning(
    f"""
👀 Watch Carefully

{', '.join(watch_list) if watch_list else 'None'}

These sectors are weakening.
"""
)

# ==================================================
# FINAL SUMMARY