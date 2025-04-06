from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('category/<slug:slug>/', views.category_page, name='category'),
    path('search/', views.search, name='search'),
    path('contact/', views.contact, name='contact'),
    path('about/', views.about, name='about'),
    path('faq/', views.faq, name='faq'),
    path('page/<slug:slug>/', views.static_page, name='static_page'),
]
