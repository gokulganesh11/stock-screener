import pandas as pd

from bs4 import BeautifulSoup
from company_scraper import get_company_details


def enrich_company_data(df):

    results = []

    for _, row in df.iterrows():

        company_url = str(
            row.get(
                "Company URL",
                ""
            )
        )

        # ---------------------------------
        # Clean HTML URL
        # ---------------------------------

        if "<a " in company_url:

            soup = BeautifulSoup(
                company_url,
                "html.parser"
            )

            link = soup.find("a")

            if link:

                company_url = link.get(
                    "href",
                    company_url
                )

        if (
            not company_url
            or company_url == "None"
        ):
            continue

        try:

            print(
                f"Scraping: {company_url}"
            )

            details = get_company_details(
                company_url
            )

            details["Company"] = row.get(
                "Company",
                ""
            )

            results.append(
                details
            )

        except Exception as e:

            print(
                f"Error scraping {company_url}"
            )

            print(e)

    if not results:

        return pd.DataFrame()

    return pd.DataFrame(
        results
    )