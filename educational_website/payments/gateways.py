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