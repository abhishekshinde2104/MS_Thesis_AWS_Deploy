import google_auth_oauthlib.flow
from googleapiclient.discovery import build
import googleapiclient.errors
from datetime import timedelta

import os
import json
from datetime import datetime
import logging
import isodate


api_key = 'AIzaSyCJCTCpYcp1aYsTKOJBEZB2liRyadRuX3w'

api_key2 = 'AIzaSyBYEoBrNOvL2P16ayh66gwO5v5_0uED_Zs'

# Directory to store results
output_dir = "yt_api_results"
os.makedirs(output_dir, exist_ok=True)

youtube = build('youtube', 'v3', developerKey=api_key2)


video_ids_with_title = {}
video_ids_with_duration = {}

final_video_ids_with_title = {}

alpha2code = {
    'germany': 'DE',
    'india': 'IN',
    'usa': 'US',
    'brazil': 'BR',
    'sweden': 'SE',
    'australia': 'AU',
    'south africa': 'ZA',
}

# Converting duration to minutes
def get_duration_in_minutes(duration):
    parsed_duration = isodate.parse_duration(duration)
    return parsed_duration.total_seconds() / 60

# Shortlisting videos
def shortlist_videos(video_id, duration):
    minutes = get_duration_in_minutes(duration)
    
    if 5 <= minutes:
        final_video_ids_with_title[video_id] = video_ids_with_title[video_id]
    # final_video_ids_with_title[video_id] = video_ids_with_title[video_id]

# Getting most Popular videos
def video_list(country, maxResults=10):
    request = youtube.videos().list(
        part='contentDetails, snippet',
        chart="mostPopular",
        # myRating = "like", # Only for authorized requests
        maxResults=maxResults,
        regionCode=alpha2code[country],
    )
    response = request.execute()
    return response

# Parsing the returned json from youtube api
def parse_video_list_response(response):
    for item in response['items']:
        video_ids_with_title[item['id']] = item['snippet']['title']
        video_ids_with_duration[item['id']] = item['contentDetails']['duration']
    
    
def youtube_api_call(country, maxResults=20):
    
    # Create a filename using the country, maxResults, and current date
    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"{country}_{maxResults}_{date_str}.json"
    filepath = os.path.join(output_dir, filename)
    
     # Check if the file exists
    if os.path.exists(filepath):
        # Load the results from the file
        with open(filepath, 'r') as file:
            results = json.load(file)
        logging.info(f"Loaded results from {filepath}")
        return results
    
    # If file doesn't exist, call the YouTube API
    logging.info(f"YT API results file not found. Fetching results for {country} and {maxResults}...")
    response = video_list(country, maxResults=maxResults)
    
    # Parse the response:
    parse_video_list_response(response)

    # Shortlisting videos within duration
    for id, duration in video_ids_with_duration.items():
        shortlist_videos(id, duration)
    
    # Save the result in a final dictionary # comment this if you want to use duration shortlisting
    # for id, title in video_ids_with_title.items():
    #     final_video_ids_with_title[id] = title
        
    # Save the results to a file
    with open(filepath, 'w') as file:
        json.dump(final_video_ids_with_title, file, indent=4)
    logging.info(f"YT API results saved to {filepath}")

    return final_video_ids_with_title


# ret = youtube_api_call('germany', maxResults=49)
# print(ret)

# MAXIMUM RESULTS = 50 for this youtube api call

# List of countries to process
# countries = ['sweden', 'germany', 'usa', 'brazil', 'south africa', 'australia', 'india']

# # Run the API call for each country
# for country in countries:
#     result = youtube_api_call(country, maxResults=50)
#     print(f"Results for {country}:", result)
