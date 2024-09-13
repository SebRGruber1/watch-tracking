import requests
from bs4 import BeautifulSoup
from datetime import datetime as dt
from concurrent.futures import ThreadPoolExecutor
import os, json

BASE_URL = "https://tropicalwatch.com"
JSON_FILE = "watch_data.json"
SESSION = requests.Session()

def extract_watch_details(watch_soup):
    title = watch_soup.find("h2").text.strip().title()
    details_url = watch_soup.find("a")["href"]
    details_page = fetch_watch_details_page(BASE_URL + details_url)
    
    if not details_page:
        return None  # If details_page is None due to an error, skip processing

    details_soup = BeautifulSoup(details_page, "html.parser")
    additional_details = extract_additional_details(details_soup)

    # Normalize text data
    brand = additional_details["Brand"].capitalize() if additional_details["Brand"] else None
    model = additional_details["Model"].capitalize() if additional_details["Model"] else None

    # Validate year data
    year = additional_details["Year"]
    try:
        year = int(year) if year.isdigit() else None
    except ValueError:
        year = None

    # Handle price data
    price_text = additional_details["Price"].replace('$', '').replace(',', '').lower()
    if price_text == "sold":
        price = "sold"
    else:
        try:
            price = float(price_text)
        except ValueError:
            price = None  # If price can't be converted to float, keep it as None

    return {
        "Title": title,
        "Year": year,
        "Brand": brand,
        "Model": model,
        "Reference": additional_details["Reference"],
        "Serial": additional_details["Serial"],
        "Inventory": details_url,
        "PriceHistory": [{"Date": dt.today().isoformat(), "Price": price}]
    }

def fetch_watch_details_page(url):
    try:
        response = SESSION.get(url)
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException as e:
        print(f"Error fetching page: {e}")
        return None

def extract_additional_details(details_soup):
    details_table = {row.th.text.strip(): row.td.text.strip() for row in details_soup.select("table.watch-main-details-table tr")}
    price_element = details_soup.find("h2", {"class": "watch-main-price"})
    price_text = price_element.text.strip() if price_element else "N/A"

    details = {
        "Price": price_text.lower(),
        "Year": details_table.get("Year", "N/A"),
        "Brand": details_table.get("Brand", "N/A"),
        "Model": details_table.get("Model", "N/A"),
        "Reference": details_table.get("Reference", "N/A"),
        "Serial": details_table.get("Serial", "N/A")
    }
    return details

def fetch_page_data(url):
    try:
        response = SESSION.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        watch_list = soup.find("ol", {"id": "watch-list"})

        # Return an empty list if no watch list is found on the page
        if watch_list is None:
            return []

        # Increase number of threads for concurrency
        with ThreadPoolExecutor(max_workers=10) as executor:  # Adjust max_workers as needed
            results = list(executor.map(extract_watch_details, watch_list.find_all("li", {"class": "watch"})))

        # Filter out any None results caused by failed detail page fetches
        return [result for result in results if result]

    except requests.exceptions.RequestException as e:
        print(f"Error fetching page data: {e}")
        return []

def save_to_json(data, json_file):
    existing_data_dict = {}
    if os.path.exists(json_file):
        with open(json_file, 'r', encoding='utf-8') as file:
            existing_data = json.load(file)
        existing_data_dict = {watch["Inventory"]: watch for watch in existing_data}

    current_date = dt.today().isoformat()

    for watch in data:
        inventory = watch["Inventory"]
        if inventory in existing_data_dict:
            existing_watch = existing_data_dict[inventory]
            last_price = existing_watch["PriceHistory"][-1]["Price"]
            new_price = watch["PriceHistory"][0]["Price"]
            if last_price != new_price:
                print(f"Price changed for {watch['Title']} (Inventory: {inventory}). Old Price: {last_price}, New Price: {new_price}. Updating...")
                existing_watch["PriceHistory"].append({"Date": current_date, "Price": new_price})
        else:
            print(f"New watch found: {watch['Title']} (Inventory: {inventory}). Adding to the JSON.")
            existing_data_dict[inventory] = watch

    # Write the updated data back to the JSON file
    with open(json_file, 'w', encoding='utf-8') as file:
        json.dump(list(existing_data_dict.values()), file, indent=4)

def main():
    page_number = 1
    all_watch_details = []

    while True:
        page_url = f"{BASE_URL}/?page={page_number}"
        page_data = fetch_page_data(page_url)

        if not page_data:
            break  # Break the loop if no data is returned (indicating the end of pages)

        all_watch_details.extend(page_data)
        page_number += 1  # Increment the page number

    # Save the data to a JSON file
    save_to_json(all_watch_details, JSON_FILE)
    print(f"Data saved to {JSON_FILE}")

if __name__ == "__main__":
    main()
