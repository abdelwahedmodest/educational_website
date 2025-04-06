# urls.py
from django.urls import path
from videos import views

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('category/<slug:slug>/', views.CategoryView.as_view(), name='category_detail'),
    path('video/<int:pk>/', views.VideoDetailView.as_view(), name='video_detail'),
    # Additional URL patterns
]
