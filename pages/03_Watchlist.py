import streamlit as st
import pandas as pd

from storage import load_watchlist, save_watchlist

st.set_page_config(page_title="Watchlist", page_icon="⭐", layout="wide")
st.title("⭐ Watchlist")
st.caption("Keep a lightweight research list with notes and review dates.")

watchlist = load_watchlist()

with st.form("add_watchlist"):
    c1, c2 = st.columns(2)
    stock = c1.text_input("Stock / Company")
    notes = c2.text_input("Research note")
    submitted = st.form_submit_button("Add to Watchlist", use_container_width=True)

if submitted:
    stock = stock.strip()
    if not stock:
        st.warning("Enter a company name.")
    elif stock.casefold() in watchlist["Stock"].astype(str).str.casefold().tolist():
        st.warning("That company is already in the watchlist.")
    else:
        watchlist = pd.concat([
            watchlist,
            pd.DataFrame([{"Stock": stock, "Notes": notes.strip(), "Date Added": pd.Timestamp.now().date().isoformat()}]),
        ], ignore_index=True)
        save_watchlist(watchlist)
        st.success(f"Added {stock}.")
        st.rerun()

c1, c2 = st.columns(2)
c1.metric("Stocks", len(watchlist))
query = c2.text_input("Search")

shown = watchlist.copy()
if query:
    shown = shown[shown["Stock"].astype(str).str.contains(query, case=False, na=False)]

st.dataframe(shown, use_container_width=True, hide_index=True)

if not watchlist.empty:
    st.subheader("Manage")
    selected = st.selectbox("Remove company", watchlist["Stock"].tolist())
    if st.button("Remove selected", type="secondary"):
        watchlist = watchlist[watchlist["Stock"] != selected].reset_index(drop=True)
        save_watchlist(watchlist)
        st.rerun()

    if st.button("Clear entire watchlist"):
        save_watchlist(pd.DataFrame(columns=["Stock", "Notes", "Date Added"]))
        st.rerun()

st.download_button("Download CSV", watchlist.to_csv(index=False), "watchlist.csv", "text/csv")
