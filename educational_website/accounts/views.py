from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from .forms import RegisterForm, ProfileUpdateForm, UserUpdateForm, CustomLoginForm
from .models import Profile, Bookmark, UserVideoHistory
from videos.models import Video

def register(request):
    """Vue d'inscription utilisateur"""
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            messages.success(request, f'Votre compte a été créé avec succès! Vous êtes maintenant connecté.')
            return redirect('home')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})

class CustomLoginView(LoginView):
    """Vue de connexion personnalisée"""
    authentication_form = CustomLoginForm
    template_name = 'accounts/login.html'
    
    def form_valid(self, form):
        messages.success(self.request, f'Vous êtes maintenant connecté!')
        return super().form_valid(form)

@login_required
def profile(request):
    """Vue de profil utilisateur"""
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, f'Votre profil a été mis à jour!')
            return redirect('profile')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)
    
    # Récupérer l'historique des vidéos et les favoris
    video_history = UserVideoHistory.objects.filter(user=request.user.profile).order_by('-watch_date')[:10]
    bookmarks = Bookmark.objects.filter(user=request.user).order_by('-date_added')
    
    context = {
        'u_form': u_form,
        'p_form': p_form,
        'video_history': video_history,
        'bookmarks': bookmarks
    }
    
    return render(request, 'accounts/profile.html', context)

@login_required
def bookmark_video(request, video_id):
    """Ajouter/supprimer une vidéo des favoris"""
    video = get_object_or_404(Video, id=video_id)
    bookmark, created = Bookmark.objects.get_or_create(user=request.user, video=video)
    
    if not created:
        # Si le favori existait déjà, le supprimer
        bookmark.delete()
        messages.info(request, f'"{video.title}" a été retiré de vos favoris')
    else:
        messages.success(request, f'"{video.title}" a été ajouté à vos favoris')
    
    # Rediriger vers la page d'où venait la requête
    next_page = request.POST.get('next', '/')
    return redirect(next_page)

@login_required
def my_videos(request):
    """Afficher toutes les vidéos marquées comme favoris et l'historique complet"""
    bookmarks = Bookmark.objects.filter(user=request.user).order_by('-date_added')
    video_history = UserVideoHistory.objects.filter(user=request.user.profile).order_by('-watch_date')
    
    context = {
        'bookmarks': bookmarks,
        'video_history': video_history
    }
    
    return render(request, 'accounts/my_videos.html', context)

@login_required
def record_video_watch(request, video_id):
    """Enregistrer qu'un utilisateur a regardé une vidéo (appelé via AJAX)"""
    if request.method == 'POST' and request.is_ajax():
        video = get_object_or_404(Video, id=video_id)
        duration = request.POST.get('duration', 0)
        completed = request.POST.get('completed', False) == 'true'
        
        # Créer un nouvel enregistrement d'historique
        UserVideoHistory.objects.create(
            user=request.user.profile,
            video=video,
            watch_duration=duration,
            completed=completed
        )
        
        return JsonResponse({'status': 'success'})
    
    return JsonResponse({'status': 'error'}, status=400)

