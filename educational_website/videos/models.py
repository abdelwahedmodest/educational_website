# Create your models here.# videos/models.py
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

