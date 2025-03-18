import csv
import json
import time
import uuid
import logging

from utils import capture_browser_data


# CSV Headers
headers = [
    "timestamp", "video_id", "yt_url", "yt_title", "phase", "cookies", "js_cookies", "local_storage", "session_storage", "web_requests", "landing_page_url"
]

# Initialize CSV with headers
def initialize_csv(output_csv):
    logging.info(f"Initializing CSV file: {output_csv}")    
    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        

# Function to store data in the CSV file
def store_data_in_csv(timestamp, video_id, phase, yt_url, yt_title, driver, landing_page_url=None, output_csv_path="yt_measurements/default_output.csv"):
    logging.info(f"Storing data in CSV for phase: {phase}")
    data = capture_browser_data(driver)
    
    # Write to CSV
    with open(output_csv_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            timestamp,
            video_id, 
            yt_url, 
            yt_title, 
            phase,
            json.dumps(data['cookies']),
            json.dumps(data['js_cookies']),
            json.dumps(data['local_storage']),
            json.dumps(data['session_storage']),
            json.dumps(data['web_requests']),
            landing_page_url
        ])
