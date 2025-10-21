"""
Commande Django pour initialiser les groupes et permissions
"""

from django.core.management.base import BaseCommand
from gestion.permissions import create_groups


class Command(BaseCommand):
    help = 'Crée les groupes et permissions de base pour SchoolPro'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('🔧 Configuration des groupes et permissions...'))
        
        try:
            create_groups()
            self.stdout.write(self.style.SUCCESS('✅ Groupes et permissions créés avec succès !'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erreur : {str(e)}'))