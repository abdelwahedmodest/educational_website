from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.generic import ListView, DetailView
from django.views.decorators.http import require_POST

from videos.models import Category, Video, Subcategory
from .models import StaticPage, SiteConfiguration, FAQ, ContactMessage
from .forms import ContactForm, SearchForm

def get_site_config():
    """Récupère ou crée la configuration du site"""
    config, created = SiteConfiguration.objects.get_or_create(
        pk=1, 
        defaults={
            'site_name': 'Educational Website',
            'contact_email': 'contact@example.com',
        }
    )
    return config

def home(request):
    """Page d'accueil du site"""
    # Récupérer toutes les catégories avec le nombre de vidéos
    categories = Category.objects.annotate(video_count=Count('videos'))
    
    # Récupérer les vidéos mises en avant
    featured_videos = Video.objects.filter(featured=True).order_by('-publish_date')[:6]
    
    # Récupérer les vidéos récentes
    recent_videos = Video.objects.order_by('-publish_date')[:12]
    
    # Récupérer la configuration du site
    site_config = get_site_config()
    
    # Formulaire de recherche
    search_form = SearchForm()
    
    context = {
        'categories': categories,
        'featured_videos': featured_videos,
        'recent_videos': recent_videos,
        'site_config': site_config,
        'search_form': search_form,
    }
    
    return render(request, 'core/home.html', context)

def category_page(request, slug):
    """Page d'une catégorie"""
    category = get_object_or_404(Category, slug=slug)
    subcategories = category.subcategories.all()
    
    # Récupérer les vidéos de cette catégorie
    videos = Video.objects.filter(category=category).order_by('-publish_date')
    
    # Filtrer par sous-catégorie si spécifiée
    subcategory_slug = request.GET.get('subcategory')
    if subcategory_slug:
        subcategory = get_object_or_404(Subcategory, slug=subcategory_slug, category=category)
        videos = videos.filter(subcategory=subcategory)
    
    # Pagination
    site_config = get_site_config()
    paginator = Paginator(videos, site_config.videos_per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'category': category,
        'subcategories': subcategories,
        'page_obj': page_obj,
        'videos_count': videos.count(),
        'site_config': site_config,
    }
    
    return render(request, 'core/category.html', context)

def search(request):
    """Recherche de vidéos"""
    form = SearchForm(request.GET)
    query = request.GET.get('query', '')
    category_slug = request.GET.get('category', '')
    
    videos = Video.objects.all()
    
    # Filtrer par recherche
    if query:
        videos = videos.filter(
            Q(title__icontains=query) | 
            Q(description__icontains=query)
        )
    
    # Filtrer par catégorie si spécifiée
    if category_slug:
        videos = videos.filter(category__slug=category_slug)
    
    # Pagination
    site_config = get_site_config()
    paginator = Paginator(videos, site_config.videos_per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'query': query,
        'category_slug': category_slug,
        'page_obj': page_obj,
        'videos_count': videos.count(),
        'site_config': site_config,
        'form': form,
    }
    
    return render(request, 'core/search_results.html', context)

def static_page(request, slug):
    """Affichage d'une page statique"""
    page = get_object_or_404(StaticPage, slug=slug, is_published=True)
    site_config = get_site_config()
    
    context = {
        'page': page,
        'site_config': site_config,
    }
    
    return render(request, 'core/static_page.html', context)

def contact(request):
    """Page de contact"""
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Votre message a été envoyé avec succès! Nous vous répondrons dans les plus brefs délais.")
            return redirect('contact')
    else:
        form = ContactForm()
    
    site_config = get_site_config()
    faqs = FAQ.objects.filter(is_published=True).order_by('order')
    
    context = {
        'form': form,
        'site_config': site_config,
        'faqs': faqs,
    }
    
    return render(request, 'core/contact.html', context)

def about(request):
    """Page à propos"""
    site_config = get_site_config()
    
    # Statistiques
    videos_count = Video.objects.count()
    categories_count = Category.objects.count()
    
    context = {
        'site_config': site_config,
        'videos_count': videos_count,
        'categories_count': categories_count,
    }
    
    return render(request, 'core/about.html', context)

def faq(request):
    """Page FAQ"""
    site_config = get_site_config()
    
    # Récupérer toutes les FAQs et les regrouper par catégorie
    faqs = FAQ.objects.filter(is_published=True).order_by('category', 'order')
    
    # Créer un dictionnaire pour regrouper les FAQs par catégorie
    faq_by_category = {}
    for faq in faqs:
        category = faq.category or "Général"  # Catégorie par défaut
        if category not in faq_by_category:
            faq_by_category[category] = []
        faq_by_category[category].append(faq)
    
    context = {
        'site_config': site_config,
        'faq_by_category': faq_by_category,
    }
    
    return render(request, 'core/faq.html', context)

