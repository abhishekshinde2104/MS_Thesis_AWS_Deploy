import json
import os

def merge_unique_videos(folder_path, output_file):
    unique_videos = {}
    
    # Get list of JSON files in the folder
    json_files = [f for f in os.listdir(folder_path) if f.endswith(".json")]
    
    for json_file in json_files:
        file_path = os.path.join(folder_path, json_file)
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
            unique_videos.update(data)  # Ensuring uniqueness
    
    # Save merged unique videos to output file
    with open(output_file, "w", encoding="utf-8") as merged_file:
        json.dump(unique_videos, merged_file, indent=4, ensure_ascii=False)
    
    print(f"Merged {len(json_files)} files. Unique videos saved to {output_file}")

# Example usage
folder_path = "video_list"  
output_file = "videos_to_watch.json"
merge_unique_videos(folder_path, output_file)
