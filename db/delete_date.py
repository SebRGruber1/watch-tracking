import sqlite3

def clear_database_data(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Retrieve a list of all tables in the database
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    # Iterate over the list of tables and delete all records from each
    for table in tables:
        print(f"Clearing data from table: {table[0]}")
        cursor.execute(f"DELETE FROM {table[0]};")

    # Commit the changes and close the connection
    conn.commit()
    conn.close()
    print("All data has been cleared while keeping the schema intact.")

# Path to your SQLite database
db_file_path = './watch_data.db'

clear_database_data(db_file_path)
