import streamlit as st

from storage import list_snapshots, load_snapshot, compare_snapshots

st.set_page_config(page_title="Alerts", page_icon="🔔", layout="wide")
st.title("🔔 Research Alerts")
st.caption("Surface material changes between saved sector snapshots.")

snapshots = list_snapshots()
if len(snapshots) < 2:
    st.info("Save at least two sector snapshots before checking alerts.")
    st.stop()

latest = load_snapshot(snapshots[0])
previous = load_snapshot(snapshots[1])
changes = compare_snapshots(previous, latest)

threshold = st.slider("Score-change threshold", 0.0, 10.0, 2.0, 0.5)
if changes.empty:
    st.info("No comparable sector changes found.")
    st.stop()

alerts = changes[changes["Score Change"].abs() >= threshold].copy()

c1, c2, c3 = st.columns(3)
c1.metric("Sectors changed", len(alerts))
c2.metric("Improved", int((alerts["Score Change"] > 0).sum()))
c3.metric("Declined", int((alerts["Score Change"] < 0).sum()))

if alerts.empty:
    st.success("No sector crossed the selected change threshold.")
else:
    st.subheader("Detected changes")
    st.dataframe(alerts, use_container_width=True, hide_index=True)
    st.caption("These are data-change alerts, not buy/sell recommendations.")
