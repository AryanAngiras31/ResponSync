# create_db.py
import sqlite3
import os # Import the os module

def initialize_database(db_file, init_sql_file):
    """Connects to an SQLite database and executes the SQL commands from the init file."""
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    try:
        with open(init_sql_file, "r") as f:
            sql_script = f.read()
            cursor.executescript(sql_script)
        conn.commit()
        print(f"Database '{db_file}' initialized successfully from '{init_sql_file}'.")
    except FileNotFoundError:
        print(f"Error: The file '{init_sql_file}' was not found.")
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    # Get the directory where the script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Construct the absolute path to the database file in the script's directory
    database_file = os.path.join(script_dir, "database.db")
    # Construct the absolute path to the init.sql file
    initialization_sql_file = os.path.join(script_dir, "init.sql")
    initialize_database(database_file, initialization_sql_file)