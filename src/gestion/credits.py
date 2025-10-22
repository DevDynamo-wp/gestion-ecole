"""
Système de crédits avec paiement en ligne pour SchoolPro
Gestion des abonnements et activation des fonctionnalités
"""

import uuid
import hashlib
import requests
import json
from datetime import datetime, timedelta
from django.db import models
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from .models import Credit, Journal
import logging

logger = logging.getLogger(__name__)


class PaymentProcessor:
    """Processeur de paiement pour différents fournisseurs"""
    
    def __init__(self):
        self.providers = {
            'orange_money': OrangeMoneyProcessor(),
            'mtn_mobile_money': MTNMobileMoneyProcessor(),
            'visa_mastercard': VisaMastercardProcessor(),
            'paypal': PayPalProcessor(),
        }
    
    def process_payment(self, provider, amount, currency, description, callback_url):
        """Traite un paiement via le fournisseur spécifié"""
        if provider not in self.providers:
            raise ValueError(f"Fournisseur de paiement non supporté: {provider}")
        
        processor = self.providers[provider]
        return processor.create_payment(amount, currency, description, callback_url)
    
    def verify_payment(self, provider, transaction_id):
        """Vérifie le statut d'un paiement"""
        if provider not in self.providers:
            raise ValueError(f"Fournisseur de paiement non supporté: {provider}")
        
        processor = self.providers[provider]
        return processor.verify_payment(transaction_id)


class OrangeMoneyProcessor:
    """Processeur Orange Money"""
    
    def __init__(self):
        self.api_url = getattr(settings, 'ORANGE_MONEY_API_URL', 'https://api.orange.com/orange-money-webpay')
        self.client_id = getattr(settings, 'ORANGE_MONEY_CLIENT_ID', '')
        self.client_secret = getattr(settings, 'ORANGE_MONEY_CLIENT_SECRET', '')
    
    def create_payment(self, amount, currency, description, callback_url):
        """Crée un paiement Orange Money"""
        try:
            # Génération d'un token d'accès
            token = self._get_access_token()
            
            # Création du paiement
            payment_data = {
                'merchant_key': getattr(settings, 'ORANGE_MONEY_MERCHANT_KEY', ''),
                'currency': currency,
                'order_id': str(uuid.uuid4()),
                'amount': amount,
                'return_url': callback_url,
                'cancel_url': callback_url,
                'notif_url': callback_url,
                'lang': 'fr',
                'reference': f"SchoolPro-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            }
            
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            response = requests.post(
                f"{self.api_url}/cm/v1/webpayment",
                json=payment_data,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 201:
                result = response.json()
                return {
                    'success': True,
                    'payment_url': result.get('payment_url'),
                    'transaction_id': result.get('pay_token'),
                    'provider': 'orange_money'
                }
            else:
                logger.error(f"Erreur Orange Money: {response.text}")
                return {
                    'success': False,
                    'error': 'Erreur lors de la création du paiement Orange Money'
                }
        
        except Exception as e:
            logger.error(f"Erreur Orange Money: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def verify_payment(self, transaction_id):
        """Vérifie un paiement Orange Money"""
        try:
            token = self._get_access_token()
            headers = {
                'Authorization': f'Bearer {token}',
                'Accept': 'application/json'
            }
            
            response = requests.get(
                f"{self.api_url}/cm/v1/webpayment/{transaction_id}",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'status': result.get('status'),
                    'amount': result.get('amount'),
                    'currency': result.get('currency')
                }
            else:
                return {
                    'success': False,
                    'error': 'Impossible de vérifier le paiement'
                }
        
        except Exception as e:
            logger.error(f"Erreur vérification Orange Money: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_access_token(self):
        """Obtient un token d'accès Orange Money"""
        try:
            auth_data = {
                'grant_type': 'client_credentials'
            }
            
            response = requests.post(
                f"{self.api_url}/oauth/v2/token",
                data=auth_data,
                auth=(self.client_id, self.client_secret),
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json().get('access_token')
            else:
                raise Exception("Impossible d'obtenir le token d'accès")
        
        except Exception as e:
            logger.error(f"Erreur token Orange Money: {str(e)}")
            raise


class MTNMobileMoneyProcessor:
    """Processeur MTN Mobile Money"""
    
    def __init__(self):
        self.api_url = getattr(settings, 'MTN_MOMO_API_URL', 'https://sandbox.momodeveloper.mtn.com')
        self.subscription_key = getattr(settings, 'MTN_MOMO_SUBSCRIPTION_KEY', '')
        self.api_user = getattr(settings, 'MTN_MOMO_API_USER', '')
        self.api_key = getattr(settings, 'MTN_MOMO_API_KEY', '')
    
    def create_payment(self, amount, currency, description, callback_url):
        """Crée un paiement MTN Mobile Money"""
        try:
            # Génération de l'UUID et du token
            uuid_str = str(uuid.uuid4())
            token = self._get_collection_token()
            
            payment_data = {
                'amount': str(int(amount)),
                'currency': currency,
                'externalId': str(uuid.uuid4()),
                'payer': {
                    'partyIdType': 'MSISDN',
                    'partyId': '237123456789'  # À remplacer par le numéro réel
                },
                'payerMessage': description,
                'payeeNote': f"SchoolPro - {description}"
            }
            
            headers = {
                'Authorization': f'Bearer {token}',
                'X-Target-Environment': 'sandbox',
                'Content-Type': 'application/json',
                'X-Reference-Id': uuid_str
            }
            
            response = requests.post(
                f"{self.api_url}/collection/v1_0/requesttopay",
                json=payment_data,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 202:
                return {
                    'success': True,
                    'transaction_id': uuid_str,
                    'provider': 'mtn_mobile_money',
                    'status': 'pending'
                }
            else:
                logger.error(f"Erreur MTN MoMo: {response.text}")
                return {
                    'success': False,
                    'error': 'Erreur lors de la création du paiement MTN MoMo'
                }
        
        except Exception as e:
            logger.error(f"Erreur MTN MoMo: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def verify_payment(self, transaction_id):
        """Vérifie un paiement MTN Mobile Money"""
        try:
            token = self._get_collection_token()
            headers = {
                'Authorization': f'Bearer {token}',
                'X-Target-Environment': 'sandbox'
            }
            
            response = requests.get(
                f"{self.api_url}/collection/v1_0/requesttopay/{transaction_id}",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'status': result.get('status'),
                    'amount': result.get('amount'),
                    'currency': result.get('currency')
                }
            else:
                return {
                    'success': False,
                    'error': 'Impossible de vérifier le paiement'
                }
        
        except Exception as e:
            logger.error(f"Erreur vérification MTN MoMo: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_collection_token(self):
        """Obtient un token MTN Mobile Money"""
        try:
            auth_string = f"{self.api_user}:{self.api_key}"
            auth_bytes = auth_string.encode('utf-8')
            auth_b64 = hashlib.sha256(auth_bytes).hexdigest()
            
            headers = {
                'Authorization': f'Basic {auth_b64}',
                'X-Target-Environment': 'sandbox',
                'Ocp-Apim-Subscription-Key': self.subscription_key
            }
            
            response = requests.post(
                f"{self.api_url}/collection/token/",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json().get('access_token')
            else:
                raise Exception("Impossible d'obtenir le token MTN MoMo")
        
        except Exception as e:
            logger.error(f"Erreur token MTN MoMo: {str(e)}")
            raise


class VisaMastercardProcessor:
    """Processeur Visa/Mastercard (simulation)"""
    
    def create_payment(self, amount, currency, description, callback_url):
        """Crée un paiement Visa/Mastercard (simulation)"""
        # Simulation d'un paiement carte bancaire
        transaction_id = str(uuid.uuid4())
        
        return {
            'success': True,
            'transaction_id': transaction_id,
            'provider': 'visa_mastercard',
            'payment_url': f"{callback_url}?transaction_id={transaction_id}&status=success",
            'message': 'Paiement par carte bancaire simulé'
        }
    
    def verify_payment(self, transaction_id):
        """Vérifie un paiement Visa/Mastercard (simulation)"""
        # Simulation de vérification
        return {
            'success': True,
            'status': 'completed',
            'amount': '100.00',
            'currency': 'XAF'
        }


class PayPalProcessor:
    """Processeur PayPal (simulation)"""
    
    def create_payment(self, amount, currency, description, callback_url):
        """Crée un paiement PayPal (simulation)"""
        transaction_id = str(uuid.uuid4())
        
        return {
            'success': True,
            'transaction_id': transaction_id,
            'provider': 'paypal',
            'payment_url': f"{callback_url}?transaction_id={transaction_id}&status=success",
            'message': 'Paiement PayPal simulé'
        }
    
    def verify_payment(self, transaction_id):
        """Vérifie un paiement PayPal (simulation)"""
        return {
            'success': True,
            'status': 'completed',
            'amount': '100.00',
            'currency': 'USD'
        }


class CreditManager:
    """Gestionnaire des crédits SchoolPro"""
    
    def __init__(self):
        self.payment_processor = PaymentProcessor()
    
    def create_credit_package(self, package_type, duration_months, price, currency='XAF'):
        """Crée un package de crédit"""
        packages = {
            'basic': {
                'name': 'Package Basique',
                'duration': duration_months,
                'price': price,
                'features': ['Gestion des étudiants', 'Gestion des notes', 'Bulletins PDF']
            },
            'standard': {
                'name': 'Package Standard',
                'duration': duration_months,
                'price': price,
                'features': ['Toutes les fonctionnalités Basique', 'Rapports avancés', 'Sauvegarde cloud']
            },
            'premium': {
                'name': 'Package Premium',
                'duration': duration_months,
                'price': price,
                'features': ['Toutes les fonctionnalités Standard', 'API complète', 'Support prioritaire']
            }
        }
        
        return packages.get(package_type, packages['basic'])
    
    def initiate_payment(self, package_type, duration_months, price, provider, user_email):
        """Initie un processus de paiement"""
        try:
            # Création du package
            package = self.create_credit_package(package_type, duration_months, price)
            
            # URL de callback
            callback_url = f"{getattr(settings, 'BASE_URL', 'http://localhost:8000')}/api/credits/payment-callback/"
            
            # Traitement du paiement
            payment_result = self.payment_processor.process_payment(
                provider=provider,
                amount=price,
                currency='XAF',
                description=f"SchoolPro {package['name']} - {duration_months} mois",
                callback_url=callback_url
            )
            
            if payment_result['success']:
                # Création d'une entrée temporaire de crédit
                credit = Credit.objects.create(
                    solde=0,  # Sera mis à jour après confirmation du paiement
                    date_activation=timezone.now(),
                    date_expiration=timezone.now() + timedelta(days=30 * duration_months),
                    is_active=False  # Activé après confirmation du paiement
                )
                
                # Enregistrement des détails du paiement
                payment_data = {
                    'credit_id': credit.id,
                    'transaction_id': payment_result['transaction_id'],
                    'provider': payment_result['provider'],
                    'package_type': package_type,
                    'duration_months': duration_months,
                    'price': price,
                    'user_email': user_email,
                    'status': 'pending'
                }
                
                # Stockage temporaire (en production, utiliser Redis ou une table dédiée)
                self._store_payment_data(payment_data)
                
                return {
                    'success': True,
                    'payment_url': payment_result.get('payment_url'),
                    'transaction_id': payment_result['transaction_id'],
                    'credit_id': credit.id
                }
            else:
                return {
                    'success': False,
                    'error': payment_result['error']
                }
        
        except Exception as e:
            logger.error(f"Erreur lors de l'initiation du paiement: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def verify_and_activate_credit(self, transaction_id, provider):
        """Vérifie un paiement et active le crédit"""
        try:
            # Vérification du paiement
            verification_result = self.payment_processor.verify_payment(provider, transaction_id)
            
            if verification_result['success'] and verification_result['status'] == 'completed':
                # Récupération des données du paiement
                payment_data = self._get_payment_data(transaction_id)
                
                if payment_data:
                    # Activation du crédit
                    credit = Credit.objects.get(id=payment_data['credit_id'])
                    credit.solde = 1000  # Crédits accordés
                    credit.is_active = True
                    credit.save()
                    
                    # Envoi d'email de confirmation
                    self._send_confirmation_email(payment_data['user_email'], credit)
                    
                    # Enregistrement dans le journal
                    Journal.objects.create(
                        utilisateur=None,  # Système
                        action='create',
                        entite='credit',
                        entite_id=credit.id,
                        description=f"Crédit activé: {payment_data['package_type']} - {payment_data['duration_months']} mois"
                    )
                    
                    return {
                        'success': True,
                        'credit_id': credit.id,
                        'message': 'Crédit activé avec succès'
                    }
                else:
                    return {
                        'success': False,
                        'error': 'Données de paiement non trouvées'
                    }
            else:
                return {
                    'success': False,
                    'error': 'Paiement non confirmé'
                }
        
        except Exception as e:
            logger.error(f"Erreur lors de l'activation du crédit: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def check_credit_status(self):
        """Vérifie le statut des crédits et désactive ceux expirés"""
        try:
            expired_credits = Credit.objects.filter(
                is_active=True,
                date_expiration__lt=timezone.now()
            )
            
            for credit in expired_credits:
                credit.is_active = False
                credit.save()
                
                # Enregistrement dans le journal
                Journal.objects.create(
                    utilisateur=None,
                    action='update',
                    entite='credit',
                    entite_id=credit.id,
                    description="Crédit expiré automatiquement"
                )
            
            return {
                'success': True,
                'expired_count': expired_credits.count()
            }
        
        except Exception as e:
            logger.error(f"Erreur lors de la vérification des crédits: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_available_packages(self):
        """Retourne les packages disponibles"""
        packages = [
            {
                'type': 'basic',
                'name': 'Package Basique',
                'duration_months': 1,
                'price': 5000,
                'currency': 'XAF',
                'features': ['Gestion des étudiants', 'Gestion des notes', 'Bulletins PDF']
            },
            {
                'type': 'basic',
                'name': 'Package Basique',
                'duration_months': 6,
                'price': 25000,
                'currency': 'XAF',
                'features': ['Gestion des étudiants', 'Gestion des notes', 'Bulletins PDF']
            },
            {
                'type': 'standard',
                'name': 'Package Standard',
                'duration_months': 1,
                'price': 10000,
                'currency': 'XAF',
                'features': ['Toutes les fonctionnalités Basique', 'Rapports avancés', 'Sauvegarde cloud']
            },
            {
                'type': 'standard',
                'name': 'Package Standard',
                'duration_months': 12,
                'price': 100000,
                'currency': 'XAF',
                'features': ['Toutes les fonctionnalités Basique', 'Rapports avancés', 'Sauvegarde cloud']
            },
            {
                'type': 'premium',
                'name': 'Package Premium',
                'duration_months': 12,
                'price': 200000,
                'currency': 'XAF',
                'features': ['Toutes les fonctionnalités Standard', 'API complète', 'Support prioritaire']
            }
        ]
        
        return packages
    
    def _store_payment_data(self, payment_data):
        """Stocke les données de paiement (simulation)"""
        # En production, utiliser Redis ou une table dédiée
        # Pour la simulation, on utilise un dictionnaire en mémoire
        if not hasattr(self, '_payment_storage'):
            self._payment_storage = {}
        
        self._payment_storage[payment_data['transaction_id']] = payment_data
    
    def _get_payment_data(self, transaction_id):
        """Récupère les données de paiement"""
        if hasattr(self, '_payment_storage'):
            return self._payment_storage.get(transaction_id)
        return None
    
    def _send_confirmation_email(self, user_email, credit):
        """Envoie un email de confirmation"""
        try:
            subject = 'SchoolPro - Confirmation d\'achat de crédits'
            message = f"""
            Bonjour,
            
            Votre achat de crédits SchoolPro a été confirmé avec succès !
            
            Détails de votre abonnement :
            - Date d'activation : {credit.date_activation.strftime('%d/%m/%Y')}
            - Date d'expiration : {credit.date_expiration.strftime('%d/%m/%Y')}
            - Solde de crédits : {credit.solde}
            
            Vous pouvez maintenant utiliser toutes les fonctionnalités de SchoolPro.
            
            Cordialement,
            L'équipe SchoolPro
            """
            
            send_mail(
                subject,
                message,
                getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@schoolpro.cm'),
                [user_email],
                fail_silently=False,
            )
        
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'email: {str(e)}")


# ========== INSTANCE GLOBALE ==========

credit_manager = CreditManager()
