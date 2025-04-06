from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Profile(models.Model):
    """Profil utilisateur étendu"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='profile_avatars/', blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    
    # Préférences
    preferred_categories = models.ManyToManyField('videos.Category', blank=True, related_name='interested_users')
    email_notifications = models.BooleanField(default=True)
    
    # Réseaux sociaux
    website = models.URLField(blank=True)
    facebook = models.URLField(blank=True)
    twitter = models.URLField(blank=True)
    linkedin = models.URLField(blank=True)
    
    # Statistiques
    videos_watched = models.ManyToManyField('videos.Video', through='UserVideoHistory', blank=True)
    account_created = models.DateTimeField(auto_now_add=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"

class UserVideoHistory(models.Model):
    """Historique des vidéos regardées par un utilisateur"""
    user = models.ForeignKey('Profile', on_delete=models.CASCADE)
    video = models.ForeignKey('videos.Video', on_delete=models.CASCADE)
    watch_date = models.DateTimeField(auto_now_add=True)
    watch_duration = models.PositiveIntegerField(default=0, help_text="Durée de visionnage en secondes")
    completed = models.BooleanField(default=False)
    
    class Meta:
        verbose_name_plural = "User video histories"
        ordering = ['-watch_date']
        unique_together = ['user', 'video', 'watch_date']
    
    def __str__(self):
        return f"{self.user.user.username} - {self.video.title}"

class Bookmark(models.Model):
    """Vidéos mises en favoris par les utilisateurs"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookmarks')
    video = models.ForeignKey('videos.Video', on_delete=models.CASCADE, related_name='bookmarked_by')
    date_added = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-date_added']
        unique_together = ['user', 'video']
    
    def __str__(self):
        return f"{self.user.username} - {self.video.title}"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Crée automatiquement un profil quand un utilisateur est créé"""
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Sauvegarde le profil quand l'utilisateur est sauvegardé"""
    instance.profile.save()

