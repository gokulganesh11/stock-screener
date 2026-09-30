import os
import pandas as pd
from datetime import datetime

# ==================================================
# CONFIG
# ==================================================

HISTORY_FOLDER = "history"

os.makedirs(
    HISTORY_FOLDER,
    exist_ok=True
)

# ==================================================
# SAVE HISTORY
# ==================================================

def save_sector_history(df):

    today = datetime.now().strftime(
        "%Y-%m-%d"
    )

    file_path = os.path.join(
        HISTORY_FOLDER,
        f"{today}.csv"
    )

    df.to_csv(
        file_path,
        index=False
    )

    return file_path

# ==================================================
# LIST HISTORY FILES
# ==================================================

def get_history_files():

    files = [

        f
        for f in os.listdir(
            HISTORY_FOLDER
        )
        if f.endswith(".csv")

    ]

    files.sort()

    return files

# ==================================================
# LOAD HISTORY
# ==================================================

def load_history(file_name):

    file_path = os.path.join(
        HISTORY_FOLDER,
        file_name
    )

    if not os.path.exists(
        file_path
    ):

        return pd.DataFrame()

    return pd.read_csv(
        file_path
    )

# ==================================================
# GET LATEST FILE
# ==================================================

def get_latest_history():

    files = get_history_files()

    if not files:

        return pd.DataFrame()

    latest = files[-1]

    return load_history(
        latest
    )

# ==================================================
# COMPARE TWO FILES
# ==================================================

def compare_history(
    old_df,
    new_df
):

    if old_df.empty or new_df.empty:

        return pd.DataFrame()

    compare_df = pd.merge(
        old_df[
            [
                "Sector",
                "Average Score"
            ]
        ],
        new_df[
            [
                "Sector",
                "Average Score"
            ]
        ],
        on="Sector",
        suffixes=(
            "_Old",
            "_New"
        )
    )

    compare_df[
        "Change"
    ] = (
        compare_df[
            "Average Score_New"
        ]
        -
        compare_df[
            "Average Score_Old"
        ]
    )

    return compare_df.sort_values(
        "Change",
        ascending=False
    )