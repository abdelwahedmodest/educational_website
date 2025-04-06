# payments/models.py
from django.db import models
from django.conf import settings
from videos.models import Video

class PaymentMethod(models.Model):
    """Méthodes de paiement disponibles sur la plateforme"""
    name = models.CharField(max_length=100)
    code = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    icon = models.ImageField(upload_to='payment_icons/', blank=True)
    is_active = models.BooleanField(default=True)
    requires_shipping = models.BooleanField(default=False)
    sort_order = models.IntegerField(default=0)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['sort_order', 'name']

class SubscriptionPlan(models.Model):
    """Plans d'abonnement disponibles pour l'accès au contenu premium"""
    name = models.CharField(max_length=100)
    code = models.SlugField(unique=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_days = models.IntegerField()
    is_active = models.BooleanField(default=True)
    features = models.TextField(help_text="Liste des fonctionnalités séparées par des sauts de ligne")
    
    def __str__(self):
        return f"{self.name} ({self.price}€)"

class Order(models.Model):
    """Commande d'un utilisateur"""
    STATUS_CHOICES = (
        ('pending', 'En attente'),
        ('processing', 'En cours de traitement'),
        ('paid', 'Payé'),
        ('shipped', 'Expédié'),
        ('delivered', 'Livré'),
        ('cancelled', 'Annulé'),
        ('refunded', 'Remboursé'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    subscription_plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True, blank=True)
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_address = models.TextField(blank=True)
    billing_address = models.TextField(blank=True)
    order_notes = models.TextField(blank=True)
    
    # Horodatage
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    
    # Données de transaction
    transaction_id = models.CharField(max_length=255, blank=True)
    payment_details = models.JSONField(default=dict, blank=True)
    
    def __str__(self):
        return f"Order #{self.id} - {self.user.username} - {self.status}"
    
    class Meta:
        ordering = ['-created_at']

class UserSubscription(models.Model):
    """Abonnement actif d'un utilisateur"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='subscriptions')
    subscription_plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    auto_renew = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.user.username} - {self.subscription_plan.name} - {self.is_active}"
    
    class Meta:
        ordering = ['-end_date']
