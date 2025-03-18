import logging
from datetime import datetime


def start_logging(log_filename):
    """
    Log the current date and time when logging is started.
    """
    logging.basicConfig(
        filename=log_filename,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    logging.info(f"Logging started at {datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}")

def log_video_info(video_url, video_title):
    """
    Log the YouTube video URL and title.
    """
    logging.info(f"Playing YouTube video: {video_title}")
    logging.info(f"Video URL: {video_url}")