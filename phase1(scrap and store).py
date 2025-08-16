import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random


# List of different user agents to rotate
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Mozilla/5.0 (X11; Linux x86_64)",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)",
    "Mozilla/5.0 (iPad; CPU OS 14_0 like Mac OS X)"
]

# Create a session object
session = requests.Session()

def fetch_page(url):
    for attempt in range(3):
        try:
            # scraper_url = f"http://api.scraperapi.com/?api_key={SCRAPER_API_KEY}&url={url}"
            scraper_url = url
            response = requests.get(scraper_url, timeout=15)
            if response.status_code == 200:
                return BeautifulSoup(response.text, "html.parser")
            elif response.status_code == 429:
                print("rate limit reached sleeping for 10-15s")
                # sleep_time= random.uniform(10, 15)
                sleep_time = 10
                time.sleep(sleep_time)
                raise Exception(f"retyring after{sleep_time} seconds")
            else:
                print(f"⚠️ Status {response.status_code} for {url}")
        except Exception as e:
            print(f"⚠️ Error: {e} on attempt {attempt+1}")
    return None

def get_page_soup(stock):
    url = f"https://www.screener.in/company/{stock}/"
    soup = fetch_page(url)
    return soup

def get_table_data(soup, selector, section_name):

    if not soup:
        print(f"❌ Could not fetch {section_name} data for {stock}")
        return None

    table = soup.select_one(selector)
    if not table:
        print(f"❌ {section_name} table not found for {stock}")
        return None

    headers = [th.get_text(strip=True) for th in table.select("thead th")]
    rows = []
    for tr in table.select("tbody tr"):
        first_cell = tr.select_one("td.text")
        if section_name != "Quarterly Results" and not first_cell:
            continue
        row = [first_cell.get_text(strip=True)] if first_cell else []
        row += [td.get_text(strip=True) for td in tr.select("td")[1:]] if first_cell else [td.get_text(strip=True) for td in tr.select("td")]
        rows.append(row)

    df = pd.DataFrame(rows, columns=headers)
    df.insert(0, "Stock", stock)
    return df

# Load stock list
stock_excel = pd.read_excel("stock_list_full.xlsx")
stock_list = stock_excel["Symbol"]

quarterly_data = []
profit_loss_data = []
balance_sheet_data = []

for i, stock in enumerate(stock_list, 1):
    print(f"\n📊 ({i}/{len(stock_list)}) Fetching data for {stock}...")
    # if i % 5 ==0:
    #     print("sleeping for 2s")
    #     time.sleep(2)
    # time.sleep(0.75)
    soup = get_page_soup(stock)
    qr = get_table_data(soup, "#quarters table", "Quarterly Results")
    if qr is not None:
        quarterly_data.append(qr)

    pl = get_table_data(soup, "#profit-loss table", "Profit & Loss")
    if pl is not None:
        profit_loss_data.append(pl)

    bs = get_table_data(soup, "#balance-sheet table", "Balance Sheet")
    if bs is not None:
        balance_sheet_data.append(bs)

    # time.sleep(random.uniform(1, 3))  # Sleep between 3 to 6 seconds

# Save results
if quarterly_data or profit_loss_data or balance_sheet_data:
    with pd.ExcelWriter("financial_data.xlsx", engine="xlsxwriter") as writer:
        if quarterly_data:
            pd.concat(quarterly_data, ignore_index=True).to_excel(writer, sheet_name="Quarterly_Results", index=False)
        if profit_loss_data:
            pd.concat(profit_loss_data, ignore_index=True).to_excel(writer, sheet_name="Profit_Loss", index=False)
        if balance_sheet_data:
            pd.concat(balance_sheet_data, ignore_index=True).to_excel(writer, sheet_name="Balance_Sheet", index=False)

    print("\n✅ All financial data saved to 'financial_data.xlsx'")
else:
    print("❌ No data scraped.")
