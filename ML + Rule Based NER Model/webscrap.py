import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the API key from the .env file
API_KEY = os.getenv("API_KEY")

def search_courses(topic, max_results=2):
    query = topic.strip()
    # Automatically append "full course" if not already included
    if "course" not in query.lower():
        query += " full course"
    
    # Build API URL with videoDuration filter for longer videos
    URL = (
        f"https://www.googleapis.com/youtube/v3/search?"
        f"part=snippet&q={query}&type=video&key={API_KEY}&maxResults={max_results}&videoDuration=long"
    )
    response = requests.get(URL).json()
    
    if "items" not in response:
        print(f"No results found for {topic} or API quota exceeded.")
        return []
    
    videos = []
    for item in response["items"]:
        video_title = item["snippet"]["title"]
        video_url = f"https://www.youtube.com/watch?v={item['id']['videoId']}"
        videos.append((video_title, video_url))
    
    return videos

# Predefined list of topics
topics = ["AI", "Python", "cpp"]

# Search and display 2 videos for each topic
for topic in topics:
    print(f"\n🔍 Top 2 YouTube Courses for {topic}:")
    results = search_courses(topic, max_results=2)
    if results:
        for i, (title, url) in enumerate(results, 1):
            print(f"{i}. {title}\n   {url}\n")
    else:
        print("No videos found!")
