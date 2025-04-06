# Intégration d'une Passerelle de Paiement Multi-options dans votre Projet Django

Je vais vous guider à travers l'ajout d'un système de passerelle de paiement flexible à votre site éducatif Django, qui permettra aux utilisateurs de choisir parmi plusieurs méthodes de paiement, y compris l'option "Cash on Delivery" (paiement à la livraison).

## 1. Structure du Modèle de Données

Commençons par les modèles nécessaires pour gérer le système de paiement :

```python
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
```

## 2. Configuration des Méthodes de Paiement

Nous allons définir un système flexible pour gérer différentes passerelles de paiement :

```python
# payments/gateways.py
from abc import ABC, abstractmethod
from django.conf import settings
import stripe
import paypalrestsdk
from .models import Order, PaymentMethod

class PaymentGateway(ABC):
    """Classe abstraite pour les passerelles de paiement"""
    
    @abstractmethod
    def process_payment(self, order, request):
        """Traite un paiement et retourne un résultat"""
        pass
    
    @abstractmethod
    def verify_payment(self, order, request_data):
        """Vérifie et confirme un paiement"""
        pass

class StripeGateway(PaymentGateway):
    """Implémentation de Stripe"""
    
    def __init__(self):
        stripe.api_key = settings.STRIPE_SECRET_KEY
    
    def process_payment(self, order, request):
        # Création d'une intention de paiement Stripe
        try:
            intent = stripe.PaymentIntent.create(
                amount=int(order.amount * 100),  # Conversion en centimes
                currency='eur',
                metadata={'order_id': order.id},
                description=f"Commande #{order.id} - {order.subscription_plan.name if order.subscription_plan else 'Achat'}"
            )
            
            return {
                'success': True,
                'client_secret': intent.client_secret,
                'redirect_url': None
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'redirect_url': None
            }
    
    def verify_payment(self, order, request_data):
        # Vérification du paiement Stripe
        try:
            payment_intent_id = request_data.get('payment_intent')
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            if intent.status == 'succeeded':
                order.status = 'paid'
                order.transaction_id = payment_intent_id
                order.payment_details = {
                    'payment_method_type': intent.payment_method_type,
                    'stripe_status': intent.status,
                }
                order.save()
                return True
            return False
        except Exception:
            return False

class PayPalGateway(PaymentGateway):
    """Implémentation de PayPal"""
    
    def __init__(self):
        # Configuration PayPal SDK
        paypalrestsdk.configure({
            "mode": settings.PAYPAL_MODE,  # "sandbox" ou "live"
            "client_id": settings.PAYPAL_CLIENT_ID,
            "client_secret": settings.PAYPAL_CLIENT_SECRET
        })
    
    def process_payment(self, order, request):
        # Création d'un paiement PayPal
        try:
            base_url = request.build_absolute_uri('/').rstrip('/')
            payment = paypalrestsdk.Payment({
                "intent": "sale",
                "payer": {
                    "payment_method": "paypal"
                },
                "redirect_urls": {
                    "return_url": f"{base_url}/payments/paypal/success/",
                    "cancel_url": f"{base_url}/payments/paypal/cancel/"
                },
                "transactions": [{
                    "amount": {
                        "total": str(order.amount),
                        "currency": "EUR"
                    },
                    "description": f"Commande #{order.id}"
                }]
            })
            
            if payment.create():
                # Récupération de l'URL de redirection
                for link in payment.links:
                    if link.rel == "approval_url":
                        redirect_url = link.href
                        break
                
                order.transaction_id = payment.id
                order.save()
                
                return {
                    'success': True,
                    'redirect_url': redirect_url
                }
            else:
                return {
                    'success': False,
                    'error': payment.error,
                    'redirect_url': None
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'redirect_url': None
            }
    
    def verify_payment(self, order, request_data):
        # Vérification du paiement PayPal
        try:
            payment_id = order.transaction_id
            payer_id = request_data.get('PayerID')
            
            payment = paypalrestsdk.Payment.find(payment_id)
            
            if payment.execute({"payer_id": payer_id}):
                order.status = 'paid'
                order.payment_details = {
                    'payer_id': payer_id,
                    'paypal_status': payment.state,
                }
                order.save()
                return True
            return False
        except Exception:
            return False

class CashOnDeliveryGateway(PaymentGateway):
    """Implémentation du paiement à la livraison (Cash on Delivery)"""
    
    def process_payment(self, order, request):
        # Pas de traitement réel pour COD, juste un changement de statut
        order.status = 'processing'  # La commande est traitée mais pas encore payée
        order.save()
        
        return {
            'success': True,
            'redirect_url': None
        }
    
    def verify_payment(self, order, request_data):
        # Pas de vérification nécessaire pour COD
        return True

# Registre des passerelles de paiement
PAYMENT_GATEWAYS = {
    'stripe': StripeGateway,
    'paypal': PayPalGateway,
    'cod': CashOnDeliveryGateway,
}

def get_gateway(payment_method_code):
    """Récupère l'instance de passerelle appropriée selon la méthode de paiement"""
    gateway_class = PAYMENT_GATEWAYS.get(payment_method_code)
    if gateway_class:
        return gateway_class()
    return None
```

## 3. Vues pour Gérer les Paiements

Maintenant, créons les vues nécessaires pour gérer le processus de paiement :

```python
# payments/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

from .models import PaymentMethod, SubscriptionPlan, Order, UserSubscription
from .gateways import get_gateway

@login_required
def subscription_plans(request):
    """Affiche les plans d'abonnement disponibles"""
    plans = SubscriptionPlan.objects.filter(is_active=True)
    return render(request, 'payments/subscription_plans.html', {
        'plans': plans
    })

@login_required
def checkout(request, plan_id):
    """Page de paiement pour un plan spécifique"""
    plan = get_object_or_404(SubscriptionPlan, id=plan_id, is_active=True)
    payment_methods = PaymentMethod.objects.filter(is_active=True)
    
    # Créer une commande temporaire si elle n'existe pas
    order, created = Order.objects.get_or_create(
        user=request.user,
        status='pending',
        subscription_plan=plan,
        defaults={
            'amount': plan.price
        }
    )
    
    if request.method == 'POST':
        payment_method_id = request.POST.get('payment_method')
        
        # Récupérer la méthode de paiement sélectionnée
        payment_method = get_object_or_404(PaymentMethod, id=payment_method_id, is_active=True)
        
        # Mettre à jour les informations de commande
        shipping_address = request.POST.get('shipping_address', '')
        billing_address = request.POST.get('billing_address', '')
        order_notes = request.POST.get('order_notes', '')
        
        order.payment_method = payment_method
        order.shipping_address = shipping_address
        order.billing_address = billing_address
        order.order_notes = order_notes
        order.save()
        
        # Rediriger vers la page de traitement du paiement
        return redirect('process_payment', order_id=order.id)
    
    return render(request, 'payments/checkout.html', {
        'plan': plan,
        'payment_methods': payment_methods,
        'order': order
    })

@login_required
def process_payment(request, order_id):
    """Traite le paiement en fonction de la méthode choisie"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # Vérifier si la commande a déjà été payée
    if order.status == 'paid':
        messages.success(request, "Cette commande a déjà été payée.")
        return redirect('payment_success', order_id=order.id)
    
    # Récupérer la passerelle de paiement
    gateway = get_gateway(order.payment_method.code)
    
    if not gateway:
        messages.error(request, "Méthode de paiement non disponible.")
        return redirect('checkout', plan_id=order.subscription_plan.id)
    
    # Traiter le paiement
    result = gateway.process_payment(order, request)
    
    if not result['success']:
        messages.error(request, f"Erreur de paiement: {result.get('error', 'Une erreur s'est produite')}")
        return redirect('checkout', plan_id=order.subscription_plan.id)
    
    # Si c'est Cash on Delivery, rediriger directement vers la page de succès
    if order.payment_method.code == 'cod':
        return redirect('payment_success', order_id=order.id)
    
    # Si une redirection est nécessaire (PayPal par exemple)
    if result.get('redirect_url'):
        return redirect(result['redirect_url'])
    
    # Pour Stripe et autres paiements côté client
    return render(request, 'payments/process_payment.html', {
        'order': order,
        'payment_method': order.payment_method,
        'client_data': result.get('client_secret'),
        'stripe_public_key': settings.STRIPE_PUBLIC_KEY if order.payment_method.code == 'stripe' else None
    })

@login_required
def payment_success(request, order_id):
    """Page de confirmation après un paiement réussi"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # Si la commande est payée, créer un abonnement
    if order.status == 'paid' and order.subscription_plan:
        # Calculer les dates d'abonnement
        start_date = timezone.now()
        end_date = start_date + timedelta(days=order.subscription_plan.duration_days)
        
        # Créer ou mettre à jour l'abonnement
        subscription, created = UserSubscription.objects.update_or_create(
            user=request.user,
            is_active=True,
            defaults={
                'subscription_plan': order.subscription_plan,
                'order': order,
                'start_date': start_date,
                'end_date': end_date,
                'auto_renew': False  # Par défaut pas de renouvellement automatique
            }
        )
    
    return render(request, 'payments/success.html', {
        'order': order
    })

@login_required
def payment_cancel(request, order_id):
    """Page d'annulation de paiement"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order.status = 'cancelled'
    order.save()
    
    messages.warning(request, "Votre paiement a été annulé.")
    return redirect('subscription_plans')

@csrf_exempt
@require_POST
def stripe_webhook(request):
    """Webhook pour les notifications Stripe"""
    import stripe
    import json
    from django.conf import settings
    
    payload = request.body
    event = None
    
    try:
        event = stripe.Event.construct_from(
            json.loads(payload), settings.STRIPE_SECRET_KEY
        )
    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=400)
    
    # Traiter les événements pertinents
    if event.type == 'payment_intent.succeeded':
        payment_intent = event.data.object
        order_id = payment_intent.metadata.get('order_id')
        
        if order_id:
            try:
                order = Order.objects.get(id=order_id)
                order.status = 'paid'
                order.transaction_id = payment_intent.id
                order.save()
            except Order.DoesNotExist:
                return JsonResponse({'error': 'Order not found'}, status=404)
    
    return JsonResponse({'status': 'success'})
```

## 4. Templates HTML pour les Paiements

Voici les templates principaux pour le processus de paiement :

### Sélection de Plan d'Abonnement

```html
<!-- payments/templates/payments/subscription_plans.html -->
{% extends 'base.html' %}

{% block content %}
<div class="container my-5">
    <h1 class="text-center mb-5">Choisissez votre Plan d'Abonnement</h1>
    
    <div class="row justify-content-center">
        {% for plan in plans %}
        <div class="col-md-4 mb-4">
            <div class="card h-100 shadow">
                <div class="card-header bg-primary text-white text-center py-3">
                    <h2 class="h4">{{ plan.name }}</h2>
                </div>
                <div class="card-body d-flex flex-column">
                    <h3 class="text-center">{{ plan.price }}€</h3>
                    <p class="text-muted text-center">pour {{ plan.duration_days }} jours</p>
                    
                    <div class="mt-3">
                        {% for feature in plan.features.split %}
                        <p><i class="fas fa-check text-success me-2"></i> {{ feature }}</p>
                        {% endfor %}
                    </div>
                    
                    <div class="mt-auto text-center">
                        <a href="{% url 'checkout' plan.id %}" class="btn btn-primary btn-lg">
                            S'abonner maintenant
                        </a>
                    </div>
                </div>
            </div>
        </div>
        {% empty %}
        <div class="col-12 text-center">
            <p>Aucun plan d'abonnement disponible pour le moment.</p>
        </div>
        {% endfor %}
    </div>
</div>
{% endblock %}
```

### Page de Checkout

```html
<!-- payments/templates/payments/checkout.html -->
{% extends 'base.html' %}

{% block content %}
<div class="container my-5">
    <h1 class="mb-4">Finaliser votre achat</h1>
    
    <div class="row">
        <div class="col-md-8">
            <div class="card mb-4 shadow">
                <div class="card-header bg-light">
                    <h2 class="h5 mb-0">Méthode de Paiement</h2>
                </div>
                <div class="card-body">
                    <form method="post" id="checkout-form">
                        {% csrf_token %}
                        
                        <div class="mb-4">
                            <h3 class="h6 mb-3">Choisissez votre méthode de paiement</h3>
                            
                            <div class="row">
                                {% for method in payment_methods %}
                                <div class="col-md-6 mb-3">
                                    <div class="form-check payment-method-card p-3 border rounded {% if method.code == 'cod' %}bg-light{% endif %}">
                                        <input class="form-check-input" type="radio" name="payment_method" 
                                               id="payment-{{ method.code }}" value="{{ method.id }}" 
                                               {% if method.code == 'cod' %}checked{% endif %} required>
                                        <label class="form-check-label d-flex align-items-center" for="payment-{{ method.code }}">
                                            {% if method.icon %}
                                                <img src="{{ method.icon.url }}" alt="{{ method.name }}" height="30" class="me-2">
                                            {% else %}
                                                <i class="fas {% if method.code == 'stripe' %}fa-credit-card{% elif method.code == 'paypal' %}fa-paypal{% elif method.code == 'cod' %}fa-money-bill-wave{% else %}fa-money-check-alt{% endif %} me-2 fa-2x"></i>
                                            {% endif %}
                                            <span>{{ method.name }}</span>
                                        </label>
                                        <small class="d-block text-muted mt-1">{{ method.description|truncatechars:60 }}</small>
                                    </div>
                                </div>
                                {% endfor %}
                            </div>
                        </div>
                        
                        <div class="mb-4">
                            <h3 class="h6 mb-3">Informations de livraison</h3>
                            
                            <div class="mb-3">
                                <label for="shipping-address" class="form-label">Adresse de livraison</label>
                                <textarea class="form-control" id="shipping-address" name="shipping_address" rows="3" 
                                          {% if not any_method.requires_shipping %}disabled{% endif %}>{{ order.shipping_address }}</textarea>
                                
                                {% if not any_method.requires_shipping %}
                                <small class="text-muted">Non requis pour un contenu numérique</small>
                                {% endif %}
                            </div>
                        </div>
                        
                        <div class="mb-4">
                            <h3 class="h6 mb-3">Informations de facturation</h3>
                            
                            <div class="mb-3">
                                <label for="billing-address" class="form-label">Adresse de facturation</label>
                                <textarea class="form-control" id="billing-address" name="billing_address" rows="3">{{ order.billing_address }}</textarea>
                            </div>
                            
                            <div class="mb-3">
                                <label for="order-notes" class="form-label">Notes pour votre commande (optionnel)</label>
                                <textarea class="form-control" id="order-notes" name="order_notes" rows="2">{{ order.order_notes }}</textarea>
                            </div>
                        </div>
                        
                        <div class="d-grid">
                            <button type="submit" class="btn btn-primary btn-lg">Procéder au paiement</button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
        
        <div class="col-md-4">
            <div class="card shadow">
                <div class="card-header bg-light">
                    <h2 class="h5 mb-0">Récapitulatif de commande</h2>
                </div>
                <div class="card-body">
                    <h3 class="h6">{{ plan.name }}</h3>
                    <p>{{ plan.description|truncatechars:100 }}</p>
                    
                    <hr>
                    
                    <div class="d-flex justify-content-between mb-3">
                        <span>Prix de l'abonnement</span>
                        <span>{{ plan.price }}€</span>
                    </div>
                    
                    <div class="d-flex justify-content-between">
                        <span class="fw-bold">Total</span>
                        <span class="fw-bold">{{ plan.price }}€</span>
                    </div>
                    
                    <hr>
                    
                    <p class="mb-0 small">
                        Accès pendant {{ plan.duration_days }} jours après confirmation du paiement.
                    </p>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

### Page de Traitement du Paiement

```html
<!-- payments/templates/payments/process_payment.html -->
{% extends 'base.html' %}

{% block extra_head %}
{% if payment_method.code == 'stripe' %}
<script src="https://js.stripe.com/v3/"></script>
{% endif %}
{% endblock %}

{% block content %}
<div class="container my-5">
    <div class="row justify-content-center">
        <div class="col-md-8">
            <div class="card shadow">
                <div class="card-header bg-light">
                    <h1 class="h3 mb-0">Traitement du paiement</h1>
                </div>
                <div class="card-body">
                    {% if payment_method.code == 'stripe' %}
                        <div id="payment-element">
                            <!-- Stripe Elements sera injecté ici -->
                        </div>
                        <div id="payment-message" class="mt-3 text-danger"></div>
                        <div class="d-grid mt-4">
                            <button id="stripe-submit" class="btn btn-primary btn-lg">Payer {{ order.amount }}€</button>
                        </div>
                    {% else %}
                        <div class="text-center py-5">
                            <div class="spinner-border text-primary" role="status">
                                <span class="visually-hidden">Chargement...</span>
                            </div>
                            <p class="mt-3">Traitement de votre paiement en cours...</p>
                            <p>Veuillez ne pas actualiser la page.</p>
                        </div>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
</div>

{% if payment_method.code == 'stripe' %}
<script>
    const stripe = Stripe('{{ stripe_public_key }}');
    const clientSecret = '{{ client_data }}';
    const elements = stripe.elements({
        clientSecret: clientSecret,
        appearance: {
            theme: 'stripe',
        }
    });

    const paymentElement = elements.create('payment');
    paymentElement.mount('#payment-element');

    const form = document.getElementById('stripe-submit');
    const paymentMessage = document.getElementById('payment-message');
    
    form.addEventListener('click', async (e) => {
        e.preventDefault();
        form.disabled = true;
        
        const {error} = await stripe.confirmPayment({
            elements,
            confirmParams: {
                return_url: '{{ request.build_absolute_uri|safe }}{{ request.get_full_path }}success/'
            }
        });
        
        if (error) {
            paymentMessage.textContent = error.message;
            form.disabled = false;
        }
    });
</script>
{% endif %}
{% endblock %}
```

### Page de Confirmation de Paiement

```html
<!-- payments/templates/payments/success.html -->
{% extends 'base.html' %}

{% block content %}
<div class="container my-5">
    <div class="row justify-content-center">
        <div class="col-md-8">
            <div class="card shadow text-center">
                <div class="card-body p-5">
                    <div class="mb-4">
                        {% if order.status == 'paid' %}
                            <div class="bg-success text-white rounded-circle mx-auto p-3 d-flex align-items-center justify-content-center" style="width: 80px; height: 80px;">
                                <i class="fas fa-check fa-3x"></i>
                            </div>
                            <h1 class="h3 mt-4">Paiement réussi !</h1>
                            <p class="text-muted">Votre transaction a été complétée avec succès.</p>
                        {% elif order.payment_method.code == 'cod' %}
                            <div class="bg-primary text-white rounded-circle mx-auto p-3 d-flex align-items-center justify-content-center" style="width: 80px; height: 80px;">
                                <i class="fas fa-money-bill-wave fa-3x"></i>
                            </div>
                            <h1 class="h3 mt-4">Commande confirmée !</h1>
                            <p class="text-muted">Votre commande a été enregistrée avec succès.</p>
                            <p>Vous effectuerez le paiement à la livraison.</p>
                        {% else %}
                            <div class="bg-primary text-white rounded-circle mx-auto p-3 d-flex align-items-center justify-content-center" style="width: 80px; height: 80px;">
                                <i class="fas fa-clock fa-3x"></i>
                            </div>
                            <h1 class="h3 mt-4">Commande en traitement</h1>
                            <p class="text-muted">Votre commande est en cours de traitement.</p>
                        {% endif %}
                    </div>
                    
                    <div class="border rounded p-4 bg-light text-start my-4">
                        <h2 class="h5 mb-3">Détails de la commande</h2>
                        
                        <div class="row mb-2">
                            <div class="col-sm-4 fw-bold">Numéro de commande:</div>
                            <div class="col-sm-8">{{ order.id }}</div>
                        </div>
                        
                        <div class="row mb-2">
                            <div class="col-sm-4 fw-bold">Date:</div>
                            <div class="col-sm-8">{{ order.created_at|date:"d/m/Y H:i" }}</div>
                
