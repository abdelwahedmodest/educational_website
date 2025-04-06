# videos/views.py
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from .models import Category, Video
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
        return context# Create your views here.
