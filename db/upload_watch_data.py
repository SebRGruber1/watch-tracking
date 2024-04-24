import json
import sqlite3

def upload_json_to_db(json_file, db_file):
    # Connect to the SQLite database
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # Read the JSON file
    with open(json_file, 'r') as file:
        watches = json.load(file)

    # Iterate over each watch and insert its details into the database
    for watch in watches:
        cursor.execute('''
            INSERT OR REPLACE INTO watches (inventory, title, year, brand, model, reference, serial)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (watch['Inventory'], watch['Title'], watch['Year'], watch['Brand'], watch['Model'], watch['Reference'], watch['Serial']))

        # Insert each price history record
        for price_record in watch['PriceHistory']:
            # Determine price and status
            if isinstance(price_record['Price'], str) and price_record['Price'].lower() == "sold":
                price = None  # or a special value like 0 or -1
                status = "sold"
            else:
                price = price_record['Price']
                status = "available"

            cursor.execute('''
                INSERT INTO price_history (inventory, date, price, status)
                VALUES (?, ?, ?, ?)
            ''', (watch['Inventory'], price_record['Date'], price, status))

    # Commit the changes and close the database connection
    conn.commit()
    conn.close()

if __name__ == '__main__':
    json_file = './watch_data.json'  # Replace with the path to your JSON file
    db_file = 'watch_data.db'  # Path to your SQLite database file
    upload_json_to_db(json_file, db_file)


