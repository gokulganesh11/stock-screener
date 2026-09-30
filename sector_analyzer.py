import pandas as pd

from screener import get_sector_stocks
from company_scraper import get_company_details
from score import calculate_stock_score


# ==================================================
# RECOMMENDATION
# ==================================================

def get_recommendation(score):

    if score >= 14:
        return "STRONG BUY"

    elif score >= 10:
        return "BUY"

    elif score >= 7:
        return "HOLD"

    return "AVOID"


# ==================================================
# ANALYZE SECTOR
# ==================================================

def analyze_sector(
    sector_name,
    sector_url
):

    try:

        sector_df = get_sector_stocks(
            sector_url
        )

        results = []

        for _, row in sector_df.iterrows():

            try:

                company_name = str(
                    row["Company"]
                )

                company_url = str(
                    row["Company URL"]
                )

                if company_url in [
                    "None",
                    "nan"
                ]:
                    continue

                details = get_company_details(
                    company_url
                )

                score_data = (
                    calculate_stock_score(
                        details
                    )
                )

                score = score_data[
                    "Total Score"
                ]

                results.append(
                    {
                        "Company":
                            company_name,

                        "Score":
                            score,

                        "Recommendation":
                            get_recommendation(
                                score
                            )
                    }
                )

            except Exception:
                continue

        if not results:

            return {
                "Sector":
                    sector_name,

                "Average Score":
                    0,

                "Strong Buy Count":
                    0,

                "Top Stock":
                    "N/A",

                "Companies Analyzed":
                    0
            }

        result_df = pd.DataFrame(
            results
        )

        avg_score = round(
            result_df[
                "Score"
            ].mean(),
            2
        )

        strong_buy_count = len(
            result_df[
                result_df[
                    "Recommendation"
                ]
                == "STRONG BUY"
            ]
        )

        top_stock = (
            result_df
            .sort_values(
                "Score",
                ascending=False
            )
            .iloc[0][
                "Company"
            ]
        )

        return {

            "Sector":
                sector_name,

            "Average Score":
                avg_score,

            "Strong Buy Count":
                strong_buy_count,

            "Top Stock":
                top_stock,

            "Companies Analyzed":
                len(result_df)
        }

    except Exception:

        return {

            "Sector":
                sector_name,

            "Average Score":
                0,

            "Strong Buy Count":
                0,

            "Top Stock":
                "N/A",

            "Companies Analyzed":
                0
        }


# ==================================================
# ANALYZE ALL SECTORS
# ==================================================

def analyze_all_sectors(
    sector_urls
):

    results = []

    for sector_name, sector_url in sector_urls.items():

        if not sector_url:
            continue

        sector_result = (
            analyze_sector(
                sector_name,
                sector_url
            )
        )

        results.append(
            sector_result
        )

    df = pd.DataFrame(
        results
    )

    if len(df):

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

    return df