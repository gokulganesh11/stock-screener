import requests
import re
from bs4 import BeautifulSoup


def clean_text(value):

    if value is None:
        return None

    return re.sub(
        r"\s+",
        " ",
        str(value)
    ).strip()


def market_cap_to_cr(value):

    if not value:
        return 0

    try:

        value = (
            str(value)
            .replace("₹", "")
            .replace(",", "")
            .replace("Cr.", "")
            .replace("Cr", "")
            .strip()
        )

        return float(value)

    except:

        return 0


def get_company_details(company_url):

    company_url = str(company_url)

    print(f"CLEAN URL: {company_url}")

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(
        company_url,
        headers=headers,
        timeout=30
    )

    response.raise_for_status()

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    data = {
        "Company URL": company_url,
        "ROE": None,
        "ROCE": None,
        "PE": None,
        "Market Cap": None,
        "Market Cap Cr": 0,
        "Book Value": None,
        "Face Value": None,
        "Dividend Yield": None,
        "EPS": None,
        "Debt to Equity": None,
        "Current Price": None,
        "High Low": None,
        "Promoter Holding": None,
        "FII Holding": None,
        "DII Holding": None,
        "Government Holding": None,
        "Public Holding": None,
        "Sales Growth 3Y": None,
        "Sales Growth 5Y": None,
        "Profit Growth 3Y": None,
        "Profit Growth 5Y": None
    }

    # -----------------------------------
    # Top Ratios
    # -----------------------------------

    try:

        ratios = soup.select(
            "ul#top-ratios li"
        )

        for ratio in ratios:

            name = ratio.select_one(".name")
            value = ratio.select_one(".value")

            if not name or not value:
                continue

            metric = clean_text(
                name.get_text()
            )

            metric_value = clean_text(
                value.get_text()
            )

            print(
                f"{metric} => {metric_value}"
            )

            if metric == "ROE":
                data["ROE"] = metric_value

            elif metric == "ROCE":
                data["ROCE"] = metric_value

            elif metric == "Stock P/E":
                data["PE"] = metric_value

            elif metric == "Market Cap":

                data["Market Cap"] = metric_value

                data["Market Cap Cr"] = (
                    market_cap_to_cr(
                        metric_value
                    )
                )

            elif metric == "Book Value":
                data["Book Value"] = metric_value

            elif metric == "Face Value":
                data["Face Value"] = metric_value

            elif metric == "Dividend Yield":
                data["Dividend Yield"] = metric_value

            elif metric == "Current Price":
                data["Current Price"] = metric_value

            elif metric == "High / Low":
                data["High Low"] = metric_value

            elif metric == "EPS":
                data["EPS"] = metric_value

            elif metric in [
                "Debt",
                "Debt to equity",
                "Debt to Equity"
            ]:
                data["Debt to Equity"] = metric_value

    except Exception as e:

        print(
            f"Ratio Error: {e}"
        )

    # -----------------------------------
    # Shareholding Pattern
    # -----------------------------------

    try:

        rows = soup.select(
            "#shareholding table tbody tr"
        )

        for row in rows:

            cells = row.find_all("td")

            if len(cells) < 2:
                continue

            category = clean_text(
                cells[0].get_text()
            )

            value = clean_text(
                cells[-1].get_text()
            )

            print(
                f"{category} => {value}"
            )

            if "Promoter" in category:
                data["Promoter Holding"] = value

            elif "FII" in category:
                data["FII Holding"] = value

            elif "DII" in category:
                data["DII Holding"] = value

            elif "Government" in category:
                data["Government Holding"] = value

            elif "Public" in category:
                data["Public Holding"] = value

    except Exception as e:

        print(
            f"Shareholding Error: {e}"
        )

    # -----------------------------------
    # Growth Metrics
    # -----------------------------------

    try:

        page_text = clean_text(
            soup.get_text(
                separator=" "
            )
        )

        sales = re.search(
            r"Compounded Sales Growth.*?5 Years:\s*([0-9]+%).*?3 Years:\s*([0-9]+%)",
            page_text,
            re.DOTALL
        )

        if sales:

            data["Sales Growth 5Y"] = sales.group(1)
            data["Sales Growth 3Y"] = sales.group(2)

        profit = re.search(
            r"Compounded Profit Growth.*?5 Years:\s*([0-9]+%).*?3 Years:\s*([0-9]+%)",
            page_text,
            re.DOTALL
        )

        if profit:

            data["Profit Growth 5Y"] = profit.group(1)
            data["Profit Growth 3Y"] = profit.group(2)

    except Exception as e:

        print(
            f"Growth Error: {e}"
        )

    return data