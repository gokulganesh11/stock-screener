import streamlit as st
import pandas as pd

# ==================================================
# PAGE CONFIG
# ==================================================

st.set_page_config(
    page_title="Sector Comparison Dashboard",
    page_icon="📊",
    layout="wide"
)

# ==================================================
# SAMPLE DATA
# ==================================================

sector_data = [

    {
        "Sector": "Capital Markets",
        "Average Score": 13.44,
        "Strong Buy Count": 11
    },

    {
        "Sector": "Defence",
        "Average Score": 11.20,
        "Strong Buy Count": 7
    },

    {
        "Sector": "Railways",
        "Average Score": 10.10,
        "Strong Buy Count": 5
    },

    {
        "Sector": "Power",
        "Average Score": 9.80,
        "Strong Buy Count": 4
    },

    {
        "Sector": "EMS",
        "Average Score": 8.90,
        "Strong Buy Count": 3
    }
]

# ==================================================
# DATAFRAME
# ==================================================

df = pd.DataFrame(
    sector_data
)

df = df.sort_values(
    "Average Score",
    ascending=False
)

df.insert(
    0,
    "Rank",
    range(
        1,
        len(df) + 1
    )
)

# ==================================================
# HEADER
# ==================================================

st.title(
    "📊 Sector Comparison Dashboard"
)

st.markdown(
    """
Compare sector strength using average scores generated
by the Multibagger Screener.
"""
)

# ==================================================
# OVERVIEW
# ==================================================

st.subheader(
    "📈 Overview"
)

c1, c2, c3 = st.columns(3)

c1.metric(
    "Sectors Compared",
    len(df)
)

c2.metric(
    "Best Sector",
    df.iloc[0]["Sector"]
)

c3.metric(
    "Highest Avg Score",
    round(
        df.iloc[0]["Average Score"],
        2
    )
)

# ==================================================
# LEADERBOARD
# ==================================================

st.subheader(
    "🏆 Sector Leaderboard"
)

cols = st.columns(5)

for idx, row in enumerate(
    df.head(5).itertuples()
):

    cols[idx].metric(
        row.Sector,
        row._3
    )

# ==================================================
# SECTOR RANKINGS
# ==================================================

st.subheader(
    "📋 Sector Rankings"
)

st.dataframe(
    df,
    use_container_width=True,
    hide_index=True
)

# ==================================================
# BEST VS WORST
# ==================================================

st.subheader(
    "⚔️ Top vs Bottom Sector"
)

best_sector = df.iloc[0]
worst_sector = df.iloc[-1]

col1, col2 = st.columns(2)

with col1:

    st.success(
        f"""
### 🥇 Best Sector

Sector: {best_sector['Sector']}

Average Score: {best_sector['Average Score']}

Strong Buy Count: {best_sector['Strong Buy Count']}
"""
    )

with col2:

    st.error(
        f"""
### 📉 Weakest Sector

Sector: {worst_sector['Sector']}

Average Score: {worst_sector['Average Score']}

Strong Buy Count: {worst_sector['Strong Buy Count']}
"""
    )

# ==================================================
# SECTOR OPPORTUNITIES
# ==================================================

st.subheader(
    "🎯 Sector Opportunities"
)

for _, row in df.iterrows():

    score = row["Average Score"]

    if score >= 12:

        rating = "⭐⭐⭐⭐⭐"

    elif score >= 10:

        rating = "⭐⭐⭐⭐"

    elif score >= 8:

        rating = "⭐⭐⭐"

    else:

        rating = "⭐⭐"

    st.write(
        f"**{row['Sector']}**  |  Opportunity Rating: {rating}"
    )

# ==================================================
# MARKET LEADERS
# ==================================================

st.subheader(
    "📈 Current Market Leaders"
)

leaders = df.head(3)

for _, row in leaders.iterrows():

    st.success(
        f"{row['Rank']}. {row['Sector']} ({row['Average Score']})"
    )

# ==================================================
# SECTOR CLASSIFICATION
# ==================================================

st.subheader(
    "🎯 Sector Classification"
)

strong_sectors = []
average_sectors = []
weak_sectors = []

for _, row in df.iterrows():

    score = row["Average Score"]

    if score >= 12:

        strong_sectors.append(
            f"🟢 {row['Sector']} ({score})"
        )

    elif score >= 8:

        average_sectors.append(
            f"🟡 {row['Sector']} ({score})"
        )

    else:

        weak_sectors.append(
            f"🔴 {row['Sector']} ({score})"
        )

col1, col2, col3 = st.columns(3)

with col1:

    st.success(
        "### Strong Sectors\n\n"
        + (
            "\n".join(strong_sectors)
            if strong_sectors
            else "None"
        )
    )

with col2:

    st.warning(
        "### Moderate Sectors\n\n"
        + (
            "\n".join(average_sectors)
            if average_sectors
            else "None"
        )
    )

with col3:

    st.error(
        "### Weak Sectors\n\n"
        + (
            "\n".join(weak_sectors)
            if weak_sectors
            else "None"
        )
    )

# ==================================================
# INVESTMENT INSIGHT
# ==================================================

st.subheader(
    "💡 Investment Insight"
)

st.info(
    f"""
Current leader is **{best_sector['Sector']}**
with an average score of **{best_sector['Average Score']}**.

The sector has **{best_sector['Strong Buy Count']} Strong Buy**
opportunities and currently ranks as the most attractive area
for further stock analysis.
"""
)

# ==================================================
# ACTION SUMMARY
# ==================================================

st.subheader(
    "✅ Action Summary"
)

focus_sectors = (
    df[df["Average Score"] >= 12]
    ["Sector"]
    .tolist()
)

watch_sectors = (
    df[
        (df["Average Score"] >= 8)
        &
        (df["Average Score"] < 12)
    ]["Sector"]
    .tolist()
)

st.success(
    f"""
🎯 Focus On

{', '.join(focus_sectors)}
"""
)

st.warning(
    f"""
👀 Watch Closely

{', '.join(watch_sectors)}
"""
)

# ==================================================
# FINAL RECOMMENDATION
# ==================================================

st.subheader(
    "🚀 Final Recommendation"
)

st.info(
    """
1. Prioritize sectors with the highest average scores.

2. Focus on sectors having more Strong Buy candidates.

3. Re-run the comparison weekly to identify sector rotation.

4. Analyze individual stocks only after selecting strong sectors.

5. Avoid allocating large capital to the weakest sectors.
"""
)