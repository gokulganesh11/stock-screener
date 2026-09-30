import streamlit as st

from storage import list_snapshots, load_snapshot, compare_snapshots

st.set_page_config(page_title="History", page_icon="🕘", layout="wide")
st.title("🕘 Historical Tracking")
st.caption("Compare saved research snapshots to see how sector scores changed over time.")

snapshots = list_snapshots()
if not snapshots:
    st.info("No snapshots have been saved yet. Run a sector analysis and save a snapshot first.")
    st.stop()

labels = [path.name for path in snapshots]
selected = st.selectbox("Snapshot", labels)
current = load_snapshot(snapshots[labels.index(selected)])
st.subheader("Selected snapshot")
st.dataframe(current, use_container_width=True, hide_index=True)

if len(snapshots) >= 2:
    older = st.selectbox("Compare with older snapshot", labels[1:])
    old_df = load_snapshot(snapshots[labels.index(older)])
    comparison = compare_snapshots(old_df, current)
    st.subheader("📈 Score changes")
    if comparison.empty:
        st.warning("The two snapshots do not contain comparable sector score data.")
    else:
        st.dataframe(comparison, use_container_width=True, hide_index=True)
else:
    st.info("Save at least two snapshots to compare changes over time.")
