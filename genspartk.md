# Educational Website Project Based on YouTube Content

Based on your requirements, I'll now outline a comprehensive plan for creating an educational website using Django with SQL as the backend and HTML/CSS/JavaScript as the frontend. This website will organize your YouTube content into different categories that users can choose from.

## Project Overview

The website will allow users to browse and learn from your educational content organized by categories including programming, entertainment, e-commerce, and potentially others. Users will be able to select their preferred category and access relevant videos and educational materials.

## Technical Architecture

### Backend
- **Framework**: Django (Python web framework)
- **Database**: SQL (can use PostgreSQL, MySQL, or SQLite)
- **API Integration**: YouTube Data API to fetch and sync your channel content

### Frontend
- **Languages**: HTML, CSS, JavaScript
- **Framework Options**: 
  - Pure Django templates with Bootstrap for styling
  - Or enhanced with a JavaScript framework like React or Vue.js

## Database Schema

```
┌───────────────────┐       ┌───────────────────┐       ┌───────────────────┐
│     Category      │       │      Video        │       │      Comment      │
├───────────────────┤       ├───────────────────┤       ├───────────────────┤
│ id (PK)           │       │ id (PK)           │       │ id (PK)           │
│ name              │◄──────┤ category_id (FK)  │       │ video_id (FK)     │
│ description       │       │ title             │◄──────┤ user_id (FK)      │
│ icon              │       │ description       │       │ content           │
│ slug              │       │ youtube_id        │       │ created_at        │
└───────────────────┘       │ thumbnail_url     │       └───────────────────┘
                            │ duration          │
                            │ publish_date      │       ┌───────────────────┐
┌───────────────────┐       │ views_count       │       │       User        │
│    Subcategory    │       │ likes_count       │       ├───────────────────┤
├───────────────────┤       │ featured          │       │ id (PK)           │
│ id (PK)           │       └───────────────────┘       │ username          │
│ category_id (FK)  │                                   │ email             │
│ name              │       ┌───────────────────┐       │ password          │
│ description       │       │     Resource      │       │ profile_pic       │
│ slug              │       ├───────────────────┤       │ date_joined       │
└───────────────────┘       │ id (PK)           │       │ is_staff          │
                            │ video_id (FK)     │       │ is_active         │
                            │ title             │       └───────────────────┘
                            │ file_type         │
                            │ file_url          │
                            │ description       │
                            └───────────────────┘
```

## Key Features

1. **Category Selection System**
   - Homepage with visually appealing category cards for Programming, Entertainment, E-commerce, etc.
   - Interactive UI allowing users to select and explore their area of interest

2. **Content Organization**
   - Videos categorized by main topics and subtopics
   - Search functionality to find specific content
   - Related videos and recommended learning paths

3. **User Features**
   - User registration and profiles
   - Bookmarking favorite videos
   - Progress tracking across courses/videos
   - Comments and discussion sections

4. **Admin Panel**
   - Custom Django admin interface to manage content
   - Tools to classify and organize videos
   - Analytics dashboard for content performance

5. **Responsive Design**
   - Mobile-friendly interface
   - Consistent experience across devices

## Project Implementation Steps

### 1. Project Setup and Configuration

```python
# Initial Django project setup
django-admin startproject educational_website
cd educational_website
python manage.py startapp core
python manage.py startapp accounts
python manage.py startapp videos
```

### 2. Database Models Design

Here's an example of how the models would be structured in Django:

```python
# videos/models.py
from django.db import models
from django.utils.text import slugify

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    icon = models.ImageField(upload_to='category_icons/', blank=True)
    slug = models.SlugField(unique=True)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Categories"

class Subcategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subcategories')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    slug = models.SlugField()
    
    def __str__(self):
        return f"{self.name} ({self.category.name})"
    
    class Meta:
        unique_together = ('category', 'slug')
        verbose_name_plural = "Subcategories"

class Video(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='videos')
    subcategory = models.ForeignKey(Subcategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='videos')
    title = models.CharField(max_length=200)
    description = models.TextField()
    youtube_id = models.CharField(max_length=20, unique=True)
    thumbnail_url = models.URLField()
    duration = models.DurationField(null=True, blank=True)
    publish_date = models.DateTimeField()
    views_count = models.IntegerField(default=0)
    likes_count = models.IntegerField(default=0)
    featured = models.BooleanField(default=False)
    
    def __str__(self):
        return self.title

class Resource(models.Model):
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='resources')
    title = models.CharField(max_length=100)
    file_type = models.CharField(max_length=20)  # pdf, code, link, etc.
    file_url = models.URLField()
    description = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.title} ({self.file_type})"
```

### 3. YouTube Data Integration

```python
# utils/youtube_api.py
import os
import googleapiclient.discovery
from googleapiclient.errors import HttpError
from django.conf import settings
from videos.models import Category, Video

def fetch_channel_videos(channel_id):
    """Fetch videos from YouTube channel and categorize them"""
    api_service_name = "youtube"
    api_version = "v3"
    api_key = settings.YOUTUBE_API_KEY
    
    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, developerKey=api_key)
    
    # Logic to fetch videos and categorize them based on titles, descriptions, etc.
    # This would involve multiple API calls to get videos, details, etc.
    # Then categorizing them based on keywords or manual classification
    
    # Example processing logic (simplified)
    for item in response_items:
        video_id = item["id"]["videoId"]
        snippet = item["snippet"]
        
        # Determine category based on video metadata
        category = determine_category(snippet["title"], snippet["description"])
        
        # Create or update video in database
        Video.objects.update_or_create(
            youtube_id=video_id,
            defaults={
                'title': snippet["title"],
                'description': snippet["description"],
                'thumbnail_url': snippet["thumbnails"]["high"]["url"],
                'category': category,
                # Add other fields
            }
        )
```

### 4. Frontend Views and Templates

```python
# videos/views.py
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from .models import Category, Video

class HomeView(ListView):
    model = Category
    template_name = 'videos/home.html'
    context_object_name = 'categories'

class CategoryView(DetailView):
    model = Category
    template_name = 'videos/category.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['videos'] = self.object.videos.all().order_by('-publish_date')
        return context

class VideoDetailView(DetailView):
    model = Video
    template_name = 'videos/video_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['related_videos'] = Video.objects.filter(
            category=self.object.category
        ).exclude(id=self.object.id)[:5]
        return context
```

### 5. URLs Configuration

```python
# urls.py
from django.urls import path
from videos import views

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('category/<slug:slug>/', views.CategoryView.as_view(), name='category_detail'),
    path('video/<int:pk>/', views.VideoDetailView.as_view(), name='video_detail'),
    # Additional URL patterns
]
```

### 6. Frontend Design with HTML/CSS/JavaScript

Here's a simplified example of how the homepage might look:

```html
<!-- templates/videos/home.html -->
{% extends 'base.html' %}

{% block content %}
<div class="hero-section">
    <h1>Welcome to Educational Hub</h1>
    <p>Choose a category to start learning</p>
</div>

<div class="category-grid">
    {% for category in categories %}
    <div class="category-card" onclick="location.href='{% url 'category_detail' category.slug %}'">
        <div class="category-icon">
            {% if category.icon %}
                <img src="{{ category.icon.url }}" alt="{{ category.name }}">
            {% else %}
                <i class="fas fa-graduation-cap"></i>
            {% endif %}
        </div>
        <h2>{{ category.name }}</h2>
        <p>{{ category.description|truncatechars:100 }}</p>
    </div>
    {% endfor %}
</div>
{% endblock %}
```

```css
/* static/css/styles.css */
.category-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 2rem;
    padding: 2rem;
}

.category-card {
    background: white;
    border-radius: 8px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    padding: 2rem;
    text-align: center;
    transition: transform 0.3s ease;
    cursor: pointer;
}

.category-card:hover {
    transform: translateY(-10px);
    box-shadow: 0 10px 20px rgba(0,0,0,0.15);
}
```

## User Flow

1. User visits the homepage and sees all available categories
2. User selects a category (e.g., Programming)
3. User is presented with subcategories and featured videos in that category
4. User can browse videos, search for specific topics, or filter by subcategory
5. User views a video, which includes:
   - Embedded YouTube player
   - Video description and metadata
   - Related videos
   - Downloadable resources (if available)
   - Comments section

## Site Map

```
Home
├── Category: Programming
│   ├── Subcategory: Python
│   ├── Subcategory: JavaScript
│   ├── Subcategory: Web Development
│   └── Individual Video Pages
│
├── Category: E-commerce
│   ├── Subcategory: Online Store Setup
│   ├── Subcategory: Marketing
│   ├── Subcategory: Payment Systems
│   └── Individual Video Pages
│
├── Category: Entertainment
│   ├── Subcategory: [Topic 1]
│   ├── Subcategory: [Topic 2]
│   └── Individual Video Pages
│
├── User Account
│   ├── Dashboard
│   ├── Bookmarked Videos
│   ├── Learning Progress
│   └── Profile Settings
│
└── About/Contact
```

## Implementation Timeline

1. **Week 1**: Project setup, database schema design, and initial models
2. **Week 2**: YouTube API integration and data import
3. **Week 3**: Core views, templates, and frontend development
4. **Week 4**: User authentication and profile features
5. **Week 5**: Admin interface customization and content management
6. **Week 6**: Testing, bug fixing, and deployment preparation

## Next Steps and Recommendations

1. **Start with a simplified version** focusing on core features (category browsing and video display)
2. **Consider content synchronization** - automatic or manual process to keep website in sync with YouTube channel
3. **Plan for scalability** - ensure the database design can handle growing content
4. **Implement analytics** to track user engagement and popular content
5. **Consider adding a blog section** for additional educational content
====================================================================================
To implement the YouTube API integration code, you'll need to create a utility module within your Django project. Here's how to set it up properly:

## Creating the YouTube API Utility Module

1. First, create a utils directory in your Django project:

```
educational_website/
├── educational_website/  # Project directory
├── core/                 # Core app
├── accounts/             # Accounts app
├── videos/               # Videos app
└── utils/                # Create this directory for utility functions
    ├── __init__.py       # Empty file to make utils a Python package
    └── youtube_api.py    # The YouTube API integration code will go here
```

2. Create an empty `__init__.py` file in the utils directory to make it a proper Python package.

3. Create the `youtube_api.py` file with the complete implementation:

```python
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
```

## Setting Up API Key in Django Settings

To use the YouTube API, you need to configure your API key in Django settings:

1. Add this to your `settings.py` file:

```python
# settings.py

# YouTube API Key
YOUTUBE_API_KEY = 'YOUR_YOUTUBE_API_KEY'  # Replace with your actual API key
```

2. For production, it's better to use environment variables:

```python
# settings.py
import os

# YouTube API Key
YOUTUBE_API_KEY = os.environ.get('YOUTUBE_API_KEY')
```

## Using the YouTube API Utility

To call this utility from your Django applications, you would do the following:

1. In a Django management command:

```python
# videos/management/commands/import_youtube_videos.py
from django.core.management.base import BaseCommand
from utils.youtube_api import fetch_channel_videos

class Command(BaseCommand):
    help = 'Import videos from YouTube channel'

    def add_arguments(self, parser):
        parser.add_argument('channel_id', type=str, help='YouTube channel ID')

    def handle(self, *args, **options):
        channel_id = options['channel_id']
        count = fetch_channel_videos(channel_id)
        self.stdout.write(self.style.SUCCESS(f'Successfully processed {count} videos'))
```

2. From a view or other Django code:

```python
# videos/views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from utils.youtube_api import fetch_channel_videos

def import_videos(request):
    if request.method == 'POST':
        channel_id = request.POST.get('channel_id')

        try:
            count = fetch_channel_videos(channel_id)
            messages.success(request, f'Successfully imported {count} videos from YouTube')
        except Exception as e:
            messages.error(request, f'Error importing videos: {str(e)}')

    return redirect('admin:videos_video_changelist')
```

## Additional Requirements

Make sure you have the required Python packages installed:

```
pip install google-api-python-client
```

## Getting a YouTube API Key

To get a YouTube API key:

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable the YouTube Data API v3
4. Create credentials (API Key)
5. Restrict the API key to only the YouTube Data API

This implementation provides a robust way to fetch videos from your YouTube channel, categorize them automatically using keyword detection, and maintain their statistics. The code is structured to be extensible, allowing you to add more categories or refine the categorization logic as needed.
=====================================================================================
Would you like me to generate the Python code for implementing this Django project? I can provide you with the specific files and code needed to get started.
