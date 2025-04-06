from django.contrib import admin
from .models import StaticPage, SiteConfiguration, FAQ, ContactMessage

@admin.register(StaticPage)
class StaticPageAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'is_published', 'updated_at')
    list_filter = ('is_published', 'updated_at')
    search_fields = ('title', 'content')
    prepopulated_fields = {'slug': ('title',)}

@admin.register(SiteConfiguration)
class SiteConfigurationAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Informations générales', {
            'fields': ('site_name', 'site_description', 'contact_email', 'address', 'phone')
        }),
        ('Réseaux sociaux', {
            'fields': ('facebook_url', 'twitter_url', 'instagram_url', 'youtube_url')
        }),
        ('SEO', {
            'fields': ('google_analytics_id', 'seo_keywords')
        }),
        ('Médias', {
            'fields': ('logo', 'favicon')
        }),
        ('Paramètres', {
            'fields': ('show_trending_videos', 'videos_per_page', 'enable_comments')
        }),
    )
    
    def has_add_permission(self, request):
        # N'autoriser qu'un seul enregistrement
        return not SiteConfiguration.objects.exists()

@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'category', 'order', 'is_published')
    list_filter = ('is_published', 'category')
    search_fields = ('question', 'answer')
    list_editable = ('order', 'is_published')

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'received_at', 'is_read')
    list_filter = ('is_read', 'received_at')
    search_fields = ('name', 'email', 'subject', 'message')
    readonly_fields = ('name', 'email', 'subject', 'message', 'received_at')
    
    def has_add_permission(self, request):
        # Ne pas autoriser l'ajout manuel de messages
        return False
    
    def mark_as_read(modeladmin, request, queryset):
        queryset.update(is_read=True)
    mark_as_read.short_description = "Marquer comme lu"
    
    def mark_as_unread(modeladmin, request, queryset):
        queryset.update(is_read=False)
    mark_as_unread.short_description = "Marquer comme non lu"
    
    actions = [mark_as_read, mark_as_unread]

