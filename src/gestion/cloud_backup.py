"""
Système de sauvegarde automatique vers le cloud pour SchoolPro
Support OneDrive et Google Drive
"""

import os
import json
import requests
import shutil
import zipfile
from datetime import datetime, timedelta
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from .models import Journal
import logging

logger = logging.getLogger(__name__)


class CloudBackupManager:
    """Gestionnaire de sauvegarde cloud"""
    
    def __init__(self):
        self.onedrive = OneDriveBackup()
        self.google_drive = GoogleDriveBackup()
    
    def backup_to_cloud(self, provider='both', backup_type='full'):
        """
        Effectue une sauvegarde vers le cloud
        Args:
            provider: 'onedrive', 'google_drive', ou 'both'
            backup_type: 'full' ou 'incremental'
        """
        try:
            # Création du fichier de sauvegarde
            backup_file = self._create_backup_file(backup_type)
            
            results = {}
            
            # Sauvegarde OneDrive
            if provider in ['onedrive', 'both']:
                try:
                    onedrive_result = self.onedrive.upload_backup(backup_file)
                    results['onedrive'] = onedrive_result
                except Exception as e:
                    logger.error(f"Erreur sauvegarde OneDrive: {str(e)}")
                    results['onedrive'] = {'success': False, 'error': str(e)}
            
            # Sauvegarde Google Drive
            if provider in ['google_drive', 'both']:
                try:
                    gdrive_result = self.google_drive.upload_backup(backup_file)
                    results['google_drive'] = gdrive_result
                except Exception as e:
                    logger.error(f"Erreur sauvegarde Google Drive: {str(e)}")
                    results['google_drive'] = {'success': False, 'error': str(e)}
            
            # Nettoyage du fichier temporaire
            if os.path.exists(backup_file):
                os.remove(backup_file)
            
            # Enregistrement dans le journal
            Journal.objects.create(
                utilisateur=None,
                action='create',
                entite='backup',
                description=f"Sauvegarde cloud effectuée - Provider: {provider}, Type: {backup_type}",
                adresse_ip='127.0.0.1'
            )
            
            return {
                'success': True,
                'results': results,
                'timestamp': timezone.now()
            }
        
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde cloud: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _create_backup_file(self, backup_type):
        """Crée un fichier de sauvegarde"""
        try:
            # Répertoire de sauvegarde
            backup_dir = os.path.join(settings.BASE_DIR, 'backups')
            os.makedirs(backup_dir, exist_ok=True)
            
            # Nom du fichier
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"schoolpro_backup_{backup_type}_{timestamp}.zip"
            backup_path = os.path.join(backup_dir, backup_filename)
            
            # Création de l'archive ZIP
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Sauvegarde de la base de données
                db_path = os.path.join(settings.BASE_DIR, 'db.sqlite3')
                if os.path.exists(db_path):
                    zipf.write(db_path, 'db.sqlite3')
                
                # Sauvegarde des fichiers média
                media_path = os.path.join(settings.BASE_DIR, 'media')
                if os.path.exists(media_path):
                    for root, dirs, files in os.walk(media_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, media_path)
                            zipf.write(file_path, f'media/{arcname}')
                
                # Sauvegarde des fichiers de configuration
                config_files = ['settings.py', 'urls.py']
                for config_file in config_files:
                    config_path = os.path.join(settings.BASE_DIR, 'schoolpro_config', config_file)
                    if os.path.exists(config_path):
                        zipf.write(config_path, f'config/{config_file}')
                
                # Sauvegarde des migrations
                migrations_path = os.path.join(settings.BASE_DIR, 'gestion', 'migrations')
                if os.path.exists(migrations_path):
                    for root, dirs, files in os.walk(migrations_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, migrations_path)
                            zipf.write(file_path, f'migrations/{arcname}')
            
            return backup_path
        
        except Exception as e:
            logger.error(f"Erreur lors de la création du fichier de sauvegarde: {str(e)}")
            raise


class OneDriveBackup:
    """Gestionnaire de sauvegarde OneDrive"""
    
    def __init__(self):
        self.client_id = getattr(settings, 'ONEDRIVE_CLIENT_ID', '')
        self.client_secret = getattr(settings, 'ONEDRIVE_CLIENT_SECRET', '')
        self.redirect_uri = getattr(settings, 'ONEDRIVE_REDIRECT_URI', '')
        self.refresh_token = getattr(settings, 'ONEDRIVE_REFRESH_TOKEN', '')
        self.api_url = 'https://graph.microsoft.com/v1.0'
    
    def upload_backup(self, backup_file):
        """Upload un fichier de sauvegarde vers OneDrive"""
        try:
            # Obtention du token d'accès
            access_token = self._get_access_token()
            
            # Lecture du fichier
            with open(backup_file, 'rb') as f:
                file_content = f.read()
            
            # Nom du fichier sur OneDrive
            filename = os.path.basename(backup_file)
            onedrive_filename = f"SchoolPro_Backup/{filename}"
            
            # Upload vers OneDrive
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/octet-stream'
            }
            
            url = f"{self.api_url}/me/drive/root:/{onedrive_filename}:/content"
            
            response = requests.put(
                url,
                data=file_content,
                headers=headers,
                timeout=300  # 5 minutes timeout
            )
            
            if response.status_code in [200, 201]:
                return {
                    'success': True,
                    'file_id': response.json().get('id'),
                    'file_name': filename,
                    'size': len(file_content)
                }
            else:
                logger.error(f"Erreur upload OneDrive: {response.text}")
                return {
                    'success': False,
                    'error': f"Erreur upload: {response.status_code}"
                }
        
        except Exception as e:
            logger.error(f"Erreur OneDrive backup: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_access_token(self):
        """Obtient un token d'accès OneDrive"""
        try:
            token_url = 'https://login.microsoftonline.com/common/oauth2/v2.0/token'
            
            data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'redirect_uri': self.redirect_uri,
                'refresh_token': self.refresh_token,
                'grant_type': 'refresh_token'
            }
            
            response = requests.post(token_url, data=data, timeout=30)
            
            if response.status_code == 200:
                return response.json().get('access_token')
            else:
                raise Exception(f"Erreur token OneDrive: {response.text}")
        
        except Exception as e:
            logger.error(f"Erreur token OneDrive: {str(e)}")
            raise
    
    def list_backups(self):
        """Liste les sauvegardes disponibles sur OneDrive"""
        try:
            access_token = self._get_access_token()
            
            headers = {
                'Authorization': f'Bearer {access_token}'
            }
            
            url = f"{self.api_url}/me/drive/root:/SchoolPro_Backup:/children"
            
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                items = response.json().get('value', [])
                backups = []
                
                for item in items:
                    if item.get('name', '').endswith('.zip'):
                        backups.append({
                            'id': item.get('id'),
                            'name': item.get('name'),
                            'size': item.get('size'),
                            'created': item.get('createdDateTime'),
                            'modified': item.get('lastModifiedDateTime')
                        })
                
                return {
                    'success': True,
                    'backups': backups
                }
            else:
                return {
                    'success': False,
                    'error': f"Erreur liste OneDrive: {response.status_code}"
                }
        
        except Exception as e:
            logger.error(f"Erreur liste OneDrive: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }


class GoogleDriveBackup:
    """Gestionnaire de sauvegarde Google Drive"""
    
    def __init__(self):
        self.client_id = getattr(settings, 'GOOGLE_DRIVE_CLIENT_ID', '')
        self.client_secret = getattr(settings, 'GOOGLE_DRIVE_CLIENT_SECRET', '')
        self.refresh_token = getattr(settings, 'GOOGLE_DRIVE_REFRESH_TOKEN', '')
        self.api_url = 'https://www.googleapis.com'
    
    def upload_backup(self, backup_file):
        """Upload un fichier de sauvegarde vers Google Drive"""
        try:
            # Obtention du token d'accès
            access_token = self._get_access_token()
            
            # Création du dossier de sauvegarde s'il n'existe pas
            folder_id = self._get_or_create_backup_folder(access_token)
            
            # Lecture du fichier
            with open(backup_file, 'rb') as f:
                file_content = f.read()
            
            # Nom du fichier
            filename = os.path.basename(backup_file)
            
            # Métadonnées du fichier
            metadata = {
                'name': filename,
                'parents': [folder_id]
            }
            
            # Upload vers Google Drive
            headers = {
                'Authorization': f'Bearer {access_token}'
            }
            
            files = {
                'metadata': (None, json.dumps(metadata)),
                'file': (filename, file_content, 'application/zip')
            }
            
            url = f"{self.api_url}/upload/drive/v3/files?uploadType=multipart"
            
            response = requests.post(
                url,
                headers=headers,
                files=files,
                timeout=300  # 5 minutes timeout
            )
            
            if response.status_code == 200:
                file_data = response.json()
                return {
                    'success': True,
                    'file_id': file_data.get('id'),
                    'file_name': filename,
                    'size': len(file_content)
                }
            else:
                logger.error(f"Erreur upload Google Drive: {response.text}")
                return {
                    'success': False,
                    'error': f"Erreur upload: {response.status_code}"
                }
        
        except Exception as e:
            logger.error(f"Erreur Google Drive backup: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_access_token(self):
        """Obtient un token d'accès Google Drive"""
        try:
            token_url = 'https://oauth2.googleapis.com/token'
            
            data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'refresh_token': self.refresh_token,
                'grant_type': 'refresh_token'
            }
            
            response = requests.post(token_url, data=data, timeout=30)
            
            if response.status_code == 200:
                return response.json().get('access_token')
            else:
                raise Exception(f"Erreur token Google Drive: {response.text}")
        
        except Exception as e:
            logger.error(f"Erreur token Google Drive: {str(e)}")
            raise
    
    def _get_or_create_backup_folder(self, access_token):
        """Obtient ou crée le dossier de sauvegarde"""
        try:
            # Recherche du dossier existant
            headers = {
                'Authorization': f'Bearer {access_token}'
            }
            
            # Recherche par nom
            query = "name='SchoolPro_Backup' and mimeType='application/vnd.google-apps.folder'"
            url = f"{self.api_url}/drive/v3/files?q={query}"
            
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                folders = response.json().get('files', [])
                if folders:
                    return folders[0]['id']
            
            # Création du dossier s'il n'existe pas
            folder_metadata = {
                'name': 'SchoolPro_Backup',
                'mimeType': 'application/vnd.google-apps.folder'
            }
            
            url = f"{self.api_url}/drive/v3/files"
            
            response = requests.post(
                url,
                headers=headers,
                json=folder_metadata,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json().get('id')
            else:
                raise Exception(f"Erreur création dossier: {response.text}")
        
        except Exception as e:
            logger.error(f"Erreur dossier Google Drive: {str(e)}")
            raise
    
    def list_backups(self):
        """Liste les sauvegardes disponibles sur Google Drive"""
        try:
            access_token = self._get_access_token()
            
            # Obtention de l'ID du dossier
            folder_id = self._get_or_create_backup_folder(access_token)
            
            headers = {
                'Authorization': f'Bearer {access_token}'
            }
            
            # Recherche des fichiers dans le dossier
            query = f"'{folder_id}' in parents and name contains 'schoolpro_backup'"
            url = f"{self.api_url}/drive/v3/files?q={query}"
            
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                files = response.json().get('files', [])
                backups = []
                
                for file in files:
                    backups.append({
                        'id': file.get('id'),
                        'name': file.get('name'),
                        'size': file.get('size'),
                        'created': file.get('createdTime'),
                        'modified': file.get('modifiedTime')
                    })
                
                return {
                    'success': True,
                    'backups': backups
                }
            else:
                return {
                    'success': False,
                    'error': f"Erreur liste Google Drive: {response.status_code}"
                }
        
        except Exception as e:
            logger.error(f"Erreur liste Google Drive: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }


# ========== COMMANDE DJANGO POUR SAUVEGARDE AUTOMATIQUE ==========

class Command(BaseCommand):
    """Commande Django pour la sauvegarde automatique"""
    
    help = 'Effectue une sauvegarde automatique vers le cloud'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--provider',
            type=str,
            default='both',
            choices=['onedrive', 'google_drive', 'both'],
            help='Fournisseur cloud pour la sauvegarde'
        )
        
        parser.add_argument(
            '--type',
            type=str,
            default='full',
            choices=['full', 'incremental'],
            help='Type de sauvegarde'
        )
    
    def handle(self, *args, **options):
        provider = options['provider']
        backup_type = options['type']
        
        self.stdout.write(
            self.style.WARNING(f'Début de la sauvegarde cloud - Provider: {provider}, Type: {backup_type}')
        )
        
        # Initialisation du gestionnaire de sauvegarde
        backup_manager = CloudBackupManager()
        
        # Effectuation de la sauvegarde
        result = backup_manager.backup_to_cloud(provider=provider, backup_type=backup_type)
        
        if result['success']:
            self.stdout.write(
                self.style.SUCCESS('✅ Sauvegarde cloud effectuée avec succès !')
            )
            
            # Affichage des résultats détaillés
            for provider_name, provider_result in result['results'].items():
                if provider_result['success']:
                    self.stdout.write(
                        self.style.SUCCESS(f'  ✅ {provider_name}: {provider_result["file_name"]}')
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f'  ❌ {provider_name}: {provider_result["error"]}')
                    )
        else:
            self.stdout.write(
                self.style.ERROR(f'❌ Erreur lors de la sauvegarde: {result["error"]}')
            )


# ========== INSTANCE GLOBALE ==========

cloud_backup_manager = CloudBackupManager()
