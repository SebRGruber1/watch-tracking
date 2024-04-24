import requests
from bs4 import BeautifulSoup
from datetime import datetime as dt
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures
import sqlite3
import time

BASE_URL = "https://tropicalwatch.com"
SESSION = requests.Session()
DB_CONNECTION = None

def init_db():
    conn = sqlite3.connect('watch_data.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS watches (
            inventory TEXT PRIMARY KEY,
            title TEXT,
            year INTEGER,
            brand TEXT,
            model TEXT,
            reference TEXT,
            serial TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS price_history (
            inventory TEXT,
            date TEXT,
            price REAL,
            status TEXT,
            FOREIGN KEY(inventory) REFERENCES watches(inventory)
        )
    ''')
    conn.commit()

# Establish a persistent database connection
def get_db_connection(db_file):
    global DB_CONNECTION
    if DB_CONNECTION is None:
        try:
            DB_CONNECTION = sqlite3.connect(db_file)
        except sqlite3.Error as e:
            print(f"Database connection error: {e}")
            raise
    return DB_CONNECTION

def insert_or_update_watch(watch, cursor):
    cursor.execute('''
        INSERT OR REPLACE INTO watches (inventory, title, year, brand, model, reference, serial)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (watch['Inventory'], watch['Title'], watch['Year'], watch['Brand'], watch['Model'], watch['Reference'], watch['Serial']))

    price = watch['PriceHistory'][0]['Price']
    status = 'sold' if price == 'sold' else 'available'
    actual_price = None if status == 'sold' else price

    cursor.execute('''
        SELECT status FROM price_history 
        WHERE inventory = ? 
        ORDER BY date DESC 
        LIMIT 1
    ''', (watch['Inventory'],))
    result = cursor.fetchone()
    last_status = result[0] if result else None

    if last_status != status:
        cursor.execute('''
            INSERT INTO price_history (inventory, date, price, status)
            VALUES (?, ?, ?, ?)
        ''', (watch['Inventory'], dt.today().isoformat(), actual_price, status))


def extract_watch_details(watch_soup):
    title = watch_soup.find("h2").text.strip().title()
    details_url = watch_soup.find("a")["href"]
    details_page = fetch_watch_details_page(BASE_URL + details_url)
    details_soup = BeautifulSoup(details_page, "html.parser")
    additional_details = extract_additional_details(details_soup)

    # Normalize text data
    brand = additional_details.get("Brand", "").capitalize()
    model = additional_details.get("Model", "").capitalize()

    # Validate year data
    year = additional_details.get("Year")
    year = int(year) if year and year.isdigit() else None

    # Handle price data
    price_text = additional_details.get("Price", "").replace('$', '').replace(',', '').lower()
    price = "sold" if price_text == "sold" else float(price_text) if price_text.isdigit() else None

    return {
        "Title": title,
        "Year": year,
        "Brand": brand,
        "Model": model,
        "Reference": additional_details.get("Reference"),
        "Serial": additional_details.get("Serial"),
        "Inventory": details_url,
        "PriceHistory": [{"Date": dt.today().isoformat(), "Price": price}]
    }

def extract_additional_details(details_soup):
    details_table = details_soup.find("table", {"class": "watch-main-details-table"})
    price_element = details_soup.find("h2", {"class": "watch-main-price"})
    price_text = price_element.text.strip() if price_element else "N/A"
    details = {
        "Price": price_text.lower(),
        "Year": "N/A",
        "Brand": "N/A",
        "Model": "N/A",
        "Reference": "N/A",
        "Serial": "N/A"
    }
    for key in details.keys():
        try:
            details[key] = details_table.find("th", string=key).find_next("td").text.strip()
        except AttributeError:
            pass
    return details

def fetch_watch_details_page(url):
    try:
        response = SESSION.get(url)
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException as e:
        print(f"Error fetching page: {e}")
        return None

def fetch_page_data(url):
    try:
        response = SESSION.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        watch_list = soup.find("ol", {"id": "watch-list"})

        # Return an empty list if no watch list is found on the page
        if watch_list is None:
            return []

        with ThreadPoolExecutor() as executor:
            return list(executor.map(extract_watch_details, watch_list.find_all("li", {"class": "watch"})))
    except requests.exceptions.RequestException as e:
        print(f"Error fetching page data: {e}")
        return []


def main():
    init_db()
    conn = get_db_connection('watch_data.db')
    cursor = conn.cursor()
    start_page = 1
    end_page = 100
    start_time = time.time()

    try:
        while True:
            # Use ThreadPoolExecutor to fetch multiple pages concurrently
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future_to_url = {executor.submit(fetch_page_data, f"{BASE_URL}/?page={i}"): i for i in range(start_page, end_page + 1)}
                all_page_data = []

                for future in concurrent.futures.as_completed(future_to_url):
                    page_data = future.result()
                    if not page_data:
                        break
                    all_page_data.extend(page_data)

            if not all_page_data:
                break

            for watch in all_page_data:
                insert_or_update_watch(watch, cursor)
            conn.commit()

            # Update the page range for the next batch of pages
            start_page = end_page + 1
            end_page += 100

        print(f"The code executed in {(time.time() - start_time)/60} mins")
        print("Data saved to watch_data.db")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    try:
        main()
    finally:
        if DB_CONNECTION:
            DB_CONNECTION.close()