# utils/youtube_api.py
import os
import googleapiclient.discovery
from googleapiclient.errors import HttpError
from django.conf import settings
from videos.models import Category, Video, Subcategory

def determine_category(title, description):
    """
    Determine the appropriate category for a video based on its title and description.
    
    Parameters:
    title (str): The title of the video
    description (str): The description of the video
    
    Returns:
    Category: The most appropriate category object
    """
    # Convert to lowercase for easier matching
    title_lower = title.lower()
    description_lower = description.lower()
    
    # Define keywords for each category
    programming_keywords = ['python', 'javascript', 'django', 'programming', 
                           'code', 'coding', 'developer', 'web development', 
                           'html', 'css', 'framework', 'algorithm']
    
    ecommerce_keywords = ['ecommerce', 'e-commerce', 'online store', 'shop', 
                         'marketplace', 'shopify', 'woocommerce', 'amazon', 
                         'ebay', 'selling online', 'digital marketing']
    
    entertainment_keywords = ['entertainment', 'funny', 'comedy', 'movie', 
                             'music', 'game', 'gaming', 'play', 'fun']
    
    # Count keyword matches in title and description
    programming_score = sum(1 for kw in programming_keywords if kw in title_lower or kw in description_lower)
    ecommerce_score = sum(1 for kw in ecommerce_keywords if kw in title_lower or kw in description_lower)
    entertainment_score = sum(1 for kw in entertainment_keywords if kw in title_lower or kw in description_lower)
    
    # Get or create the default category (for videos that don't match any keywords)
    default_category, _ = Category.objects.get_or_create(
        name="Uncategorized",
        defaults={"description": "Videos that haven't been categorized yet"}
    )
    
    # Find the category with the highest score
    max_score = max(programming_score, ecommerce_score, entertainment_score)
    
    # If no significant matches, return default category
    if max_score == 0:
        return default_category
    
    # Return the category with the highest score
    if programming_score == max_score:
        category, _ = Category.objects.get_or_create(
            name="Programming",
            defaults={"description": "Programming tutorials and coding content"}
        )
    elif ecommerce_score == max_score:
        category, _ = Category.objects.get_or_create(
            name="E-commerce",
            defaults={"description": "E-commerce strategies and online business content"}
        )
    elif entertainment_score == max_score:
        category, _ = Category.objects.get_or_create(
            name="Entertainment",
            defaults={"description": "Entertainment videos and fun content"}
        )
    else:
        category = default_category
        
    return category

def fetch_channel_videos(channel_id):
    """
    Fetch videos from YouTube channel and categorize them.
    
    Parameters:
    channel_id (str): The YouTube channel ID to fetch videos from
    
    Returns:
    int: Number of videos processed
    """
    api_service_name = "youtube"
    api_version = "v3"
    api_key = settings.YOUTUBE_API_KEY
    
    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, developerKey=api_key)
    
    videos_processed = 0
    next_page_token = None
    
    try:
        # Fetch channel uploads
        while True:
            # Get channel's uploads playlist
            channels_response = youtube.channels().list(
                part="contentDetails",
                id=channel_id
            ).execute()
            
            if not channels_response.get("items"):
                break
                
            # Get the uploads playlist ID
            uploads_playlist_id = channels_response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
            
            # Get playlist items (videos)
            playlist_items_response = youtube.playlistItems().list(
                part="snippet,contentDetails",
                playlistId=uploads_playlist_id,
                maxResults=50,
                pageToken=next_page_token
            ).execute()
            
            # Process each video
            for item in playlist_items_response.get("items", []):
                video_id = item["contentDetails"]["videoId"]
                snippet = item["snippet"]
                
                # Get detailed video information
                video_response = youtube.videos().list(
                    part="contentDetails,statistics",
                    id=video_id
                ).execute()
                
                if not video_response.get("items"):
                    continue
                    
                video_details = video_response["items"][0]
                content_details = video_details["contentDetails"]
                statistics = video_details.get("statistics", {})
                
                # Parse duration (in ISO 8601 format)
                duration_str = content_details.get("duration", "PT0M0S")
                hours, minutes, seconds = 0, 0, 0
                
                if "H" in duration_str:
                    hours = int(duration_str.split("H")[0].split("PT")[1])
                    duration_str = duration_str.split("H")[1]
                else:
                    duration_str = duration_str.split("PT")[1]
                    
                if "M" in duration_str:
                    minutes = int(duration_str.split("M")[0])
                    duration_str = duration_str.split("M")[1]
                    
                if "S" in duration_str:
                    seconds = int(duration_str.split("S")[0])
                
                import datetime
                duration = datetime.timedelta(hours=hours, minutes=minutes, seconds=seconds)
                
                # Determine category based on video metadata
                category = determine_category(snippet["title"], snippet["description"])
                
                # Get publish date
                from django.utils.dateparse import parse_datetime
                publish_date = parse_datetime(snippet["publishedAt"])
                
                # Create or update video in database
                Video.objects.update_or_create(
                    youtube_id=video_id,
                    defaults={
                        'title': snippet["title"],
                        'description': snippet["description"],
                        'thumbnail_url': snippet["thumbnails"]["high"]["url"] if "high" in snippet["thumbnails"] else snippet["thumbnails"]["default"]["url"],
                        'category': category,
                        'duration': duration,
                        'publish_date': publish_date,
                        'views_count': int(statistics.get("viewCount", 0)),
                        'likes_count': int(statistics.get("likeCount", 0)),
                    }
                )
                
                videos_processed += 1
            
            # Check if there are more videos
            next_page_token = playlist_items_response.get("nextPageToken")
            if not next_page_token:
                break
                
        return videos_processed
                
    except HttpError as e:
        print(f"An HTTP error {e.resp.status} occurred: {e.content}")
        return videos_processed

def update_video_statistics(days=7):
    """
    Update statistics for videos that were updated within the last X days.
    
    Parameters:
    days (int): Number of days to look back for videos to update
    
    Returns:
    int: Number of videos updated
    """
    api_service_name = "youtube"
    api_version = "v3"
    api_key = settings.YOUTUBE_API_KEY
    
    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, developerKey=api_key)
    
    # Get videos updated within the specified time period
    from django.utils import timezone
    import datetime
    
    cutoff_date = timezone.now() - datetime.timedelta(days=days)
    videos_to_update = Video.objects.filter(publish_date__gte=cutoff_date)
    
    videos_updated = 0
    
    try:
        # Update videos in batches of 50 (YouTube API limitation)
        for i in range(0, videos_to_update.count(), 50):
            batch = videos_to_update[i:i+50]
            video_ids = [video.youtube_id for video in batch]
            
            if not video_ids:
                continue
                
            # Get updated statistics
            video_response = youtube.videos().list(
                part="statistics",
                id=",".join(video_ids)
            ).execute()
            
            # Update each video
            for item in video_response.get("items", []):
                video_id = item["id"]
                statistics = item.get("statistics", {})
                
                Video.objects.filter(youtube_id=video_id).update(
                    views_count=int(statistics.get("viewCount", 0)),
                    likes_count=int(statistics.get("likeCount", 0)),
                )
                
                videos_updated += 1
                
        return videos_updated
                
    except HttpError as e:
        print(f"An HTTP error {e.resp.status} occurred: {e.content}")
        return videos_updated

