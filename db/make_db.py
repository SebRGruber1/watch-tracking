import sqlite3

def init_db(db_file):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # Create the 'watches' table without the 'price' field
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

    # Create the 'price_history' table with an added 'status' field
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS price_history (
            inventory TEXT,
            date TEXT,
            price REAL,
            status TEXT,  -- New column for status (e.g., 'sold', 'available')
            FOREIGN KEY(inventory) REFERENCES watches(inventory)
        )
    ''')

    conn.commit()
    conn.close()

if __name__ == '__main__':
    db_file = 'watch_data.db'  # Path to your SQLite database file
    init_db(db_file)

