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
        messages.error(request, f"Erreur de paiement: {result.get('error', 'Une erreur s est produite')}")
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
