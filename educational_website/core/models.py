from django.db import models
from django.utils.text import slugify

class StaticPage(models.Model):
    """Pages statiques du site (à propos, contact, etc.)"""
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    content = models.TextField()
    meta_description = models.CharField(max_length=160, blank=True, help_text="Description pour les moteurs de recherche")
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

class SiteConfiguration(models.Model):
    """Configuration générale du site"""
    site_name = models.CharField(max_length=100)
    site_description = models.TextField(blank=True)
    contact_email = models.EmailField()
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    
    # Réseaux sociaux
    facebook_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    youtube_url = models.URLField(blank=True)
    
    # SEO
    google_analytics_id = models.CharField(max_length=50, blank=True)
    seo_keywords = models.TextField(blank=True, help_text="Mots-clés pour le référencement, séparés par des virgules")
    
    # Logo et favicon
    logo = models.ImageField(upload_to='site/', blank=True)
    favicon = models.ImageField(upload_to='site/', blank=True)
    
    # Paramètres généraux
    show_trending_videos = models.BooleanField(default=True)
    videos_per_page = models.PositiveIntegerField(default=12)
    enable_comments = models.BooleanField(default=True)
    
    # Un seul enregistrement autorisé
    class Meta:
        verbose_name = "Configuration du site"
        verbose_name_plural = "Configuration du site"
    
    def __str__(self):
        return self.site_name
    
    def save(self, *args, **kwargs):
        if SiteConfiguration.objects.exists() and not self.pk:
            # Si un enregistrement existe déjà et que celui-ci est nouveau, ne pas sauvegarder
            return
        super().save(*args, **kwargs)

class FAQ(models.Model):
    """Questions fréquemment posées"""
    question = models.CharField(max_length=255)
    answer = models.TextField()
    category = models.CharField(max_length=100, blank=True)
    order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['order', 'question']
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"
    
    def __str__(self):
        return self.question

class ContactMessage(models.Model):
    """Messages reçus via le formulaire de contact"""
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    received_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-received_at']
    
    def __str__(self):
        return f"{self.name} - {self.subject}"

