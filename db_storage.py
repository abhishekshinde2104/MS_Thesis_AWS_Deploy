import sqlite3
import csv
import json
import time
import logging

import sys

# Increase field size limit
csv.field_size_limit(2**31 - 1)


# File and DB paths
# DB_FILE = ""
# CSV_FILE = "yt_measurements/default_output.csv"

# Define the table schema
TABLE_NAME = "yt_data"
TABLE_SCHEMA = f"""
CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    video_id TEXT,
    yt_url TEXT,
    yt_title TEXT,
    phase TEXT,
    cookies TEXT,
    js_cookies TEXT,
    local_storage TEXT,
    session_storage TEXT,
    web_requests TEXT,
    landing_page_url TEXT
);
"""

# Initialize SQLite database
def initialize_db(session_db_path):
    logging.info("Initializing SQLite database")
    conn = sqlite3.connect(session_db_path)
    cursor = conn.cursor()
    cursor.execute(TABLE_SCHEMA)
    conn.commit()
    conn.close()
    
def store_csv_in_db(csv_file, db_file):
    logging.info("Storing CSV data in SQLite database")
    
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        headers = next(reader)  # Skip header row

        for row in reader:
            try:
                cursor.execute(f"""
                    INSERT INTO yt_data (
                        timestamp, video_id, yt_url, yt_title, phase, 
                        cookies, js_cookies, local_storage, session_storage, web_requests, landing_page_url
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, row)
            except sqlite3.Error as e:
                logging.error(f"Error inserting row: {e}")

    conn.commit()
    logging.info("Data stored in SQLite database")
    conn.close()
    
# initialize_db("yt_measurements/2025-02-27_18-40-10/measurements.db")
# store_csv_in_db("yt_measurements/2025-02-27_18-40-10/session.csv", "yt_measurements/2025-02-27_18-40-10/measurements.db")


# import sqlite3

# DB_FILE = "yt_measurements/2025-02-27_18-40-10/measurements.db"

# def fetch_all_rows():
#     conn = sqlite3.connect(DB_FILE)
#     cursor = conn.cursor()
    
#     cursor.execute("SELECT * FROM yt_data")  # Fetch all rows
#     rows = cursor.fetchall()
    
#     conn.close()
    
#     for row in rows:
#         print(row)  # Print each row

# fetch_all_rows()


