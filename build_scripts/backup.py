import shutil
import os
from datetime import datetime
from pathlib import Path

# Configuration
SRC_DB = r"D:\Projet\Python\App_gestion_ecole\gestion_ecole\src\db.sqlite3"
BACKUP_DIR = r"D:\Projet\Python\App_gestion_ecole\gestion_ecole\backups"
CLOUD_DIR = None  # À remplir si vous utilisez OneDrive/Google Drive

def create_backup():
    """Crée une sauvegarde de la base de données"""
    
    # Créer le dossier de sauvegarde s'il n'existe pas
    os.makedirs(BACKUP_DIR, exist_ok=True)
    
    # Vérifier que la DB existe
    if not os.path.exists(SRC_DB):
        print(f"❌ Erreur : La base de données n'existe pas à {SRC_DB}")
        return False
    
    # Créer un nom unique avec timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"db_backup_{timestamp}.sqlite3"
    backup_path = os.path.join(BACKUP_DIR, backup_filename)
    
    try:
        # Copier la DB
        shutil.copy2(SRC_DB, backup_path)
        print(f"✅ Sauvegarde créée : {backup_path}")
        
        # Optionnel : Copier vers le cloud
        if CLOUD_DIR and os.path.exists(CLOUD_DIR):
            cloud_backup = os.path.join(CLOUD_DIR, backup_filename)
            shutil.copy2(backup_path, cloud_backup)
            print(f"☁️  Sauvegarde cloud : {cloud_backup}")
        
        # Garder seulement les 10 dernières sauvegardes
        cleanup_old_backups()
        
        return True
    
    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde : {e}")
        return False

def cleanup_old_backups(keep_count=10):
    """Supprime les anciennes sauvegardes, garde les N dernières"""
    
    try:
        backups = sorted(
            [f for f in os.listdir(BACKUP_DIR) if f.startswith("db_backup_")],
            reverse=True
        )
        
        if len(backups) > keep_count:
            for old_backup in backups[keep_count:]:
                old_path = os.path.join(BACKUP_DIR, old_backup)
                os.remove(old_path)
                print(f"🗑️  Suppression ancienne sauvegarde : {old_backup}")
    
    except Exception as e:
        print(f"⚠️  Erreur lors du nettoyage : {e}")

def restore_backup(backup_filename):
    """Restaure une sauvegarde spécifique"""
    
    backup_path = os.path.join(BACKUP_DIR, backup_filename)
    
    if not os.path.exists(backup_path):
        print(f"❌ Erreur : Sauvegarde introuvable : {backup_path}")
        return False
    
    try:
        # Créer une copie de la DB actuelle avant restauration
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        current_backup = os.path.join(BACKUP_DIR, f"db_current_{timestamp}.sqlite3")
        shutil.copy2(SRC_DB, current_backup)
        print(f"💾 Copie de la DB actuelle : {current_backup}")
        
        # Restaurer la sauvegarde
        shutil.copy2(backup_path, SRC_DB)
        print(f"✅ Base de données restaurée depuis : {backup_filename}")
        return True
    
    except Exception as e:
        print(f"❌ Erreur lors de la restauration : {e}")
        return False

def list_backups():
    """Liste toutes les sauvegardes disponibles"""
    
    if not os.path.exists(BACKUP_DIR):
        print("Aucune sauvegarde disponible.")
        return
    
    backups = sorted(
        [f for f in os.listdir(BACKUP_DIR) if f.startswith("db_backup_")],
        reverse=True
    )
    
    if not backups:
        print("Aucune sauvegarde disponible.")
        return
    
    print(f"\n📋 Sauvegardes disponibles ({len(backups)} total):\n")
    for i, backup in enumerate(backups, 1):
        path = os.path.join(BACKUP_DIR, backup)
        size = os.path.getsize(path) / 1024 / 1024  # Taille en MB
        mtime = datetime.fromtimestamp(os.path.getmtime(path))
        print(f"{i}. {backup} ({size:.2f} MB) - {mtime}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "backup":
            create_backup()
        elif command == "restore" and len(sys.argv) > 2:
            restore_backup(sys.argv[2])
        elif command == "list":
            list_backups()
        else:
            print("Commandes disponibles :")
            print("  python backup.py backup          - Créer une sauvegarde")
            print("  python backup.py list            - Lister les sauvegardes")
            print("  python backup.py restore <file>  - Restaurer une sauvegarde")
    else:
        # Par défaut, créer une sauvegarde
        create_backup()