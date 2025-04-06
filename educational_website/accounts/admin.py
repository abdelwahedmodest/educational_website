from django.contrib import admin
from .models import Profile, UserVideoHistory, Bookmark

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'date_of_birth', 'account_created')
    search_fields = ('user__username', 'user__email', 'phone_number')
    list_filter = ('email_notifications', 'account_created')
    readonly_fields = ('account_created',)

@admin.register(UserVideoHistory)
class UserVideoHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'video', 'watch_date', 'watch_duration', 'completed')
    list_filter = ('completed', 'watch_date')
    search_fields = ('user__user__username', 'video__title')
    date_hierarchy = 'watch_date'

@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    list_display = ('user', 'video', 'date_added')
    list_filter = ('date_added',)
    search_fields = ('user__username', 'video__title', 'notes')

