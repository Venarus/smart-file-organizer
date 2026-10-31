"""
Organizer Core Engine (V2)
Powered by AIFileIntelligence and SecurityBackupEngine:
- Multi-dimensional intelligent classification
- Transaction logging with 1-click Undo capability
- Complete download & file-lock safety
- Baseline protection for desktop
- Collision-free safe movement
"""

import os
import time
import shutil
from datetime import datetime
from intelligence import AIFileIntelligence
from security_backup import SecurityBackupEngine
from storage_analyzer import StorageAnalyzer
from search_engine import SearchEngine

INCOMPLETE_EXTENSIONS = {
    '.crdownload', '.tmp', '.part', '.download', '.~tmp', '.opdownload'
}

IGNORED_FILENAMES = {
    'desktop.ini', 'thumbs.db', '.ds_store'
}

def is_file_ready(file_path):
    """
    Dosyanın indirilmesinin bitip bitmediğini ve kilitli olup olmadığını yüksek hızda test eder.
    Yalnızca son 2 saniyede değiştirilmiş dosyalarda bekleme yapar.
    """
    try:
        stat = os.stat(file_path)
        # Dosya son 2 saniye içinde yazılmışsa aktif indirme ihtimaline karşı kontrol et
        if time.time() - stat.st_mtime < 2.0:
            initial_size = stat.st_size
            time.sleep(0.1)
            current_size = os.path.getsize(file_path)
            if initial_size != current_size:
                return False

        # Dosya kilidi kontrolü (Hemen denenir, kilitliyse PermissionError fırlatır)
        with open(file_path, 'r+b'):
            pass
        return True
    except (OSError, PermissionError):
        return False

def get_unique_path(target_path):
    """Hedefte aynı isimde dosya varsa üzerine yazmaz, sonuna (1), (2) ekler."""
    if not os.path.exists(target_path):
        return target_path
    
    dir_name, file_name = os.path.split(target_path)
    base_name, ext = os.path.splitext(file_name)
    counter = 1
    while True:
        new_name = f"{base_name} ({counter}){ext}"
        new_path = os.path.join(dir_name, new_name)
        if not os.path.exists(new_path):
            return new_path
        counter += 1

def organize_file(source_path, target_base_folder, allow_new_categories=True):
    """Tek bir dosyayı AI zekasıyla analiz eder, taşır ve geri alma günlüğüne kaydeder."""
    file_name = os.path.basename(source_path)
    lower_name = file_name.lower()
    _, ext = os.path.splitext(lower_name)

    if ext in INCOMPLETE_EXTENSIONS or lower_name in IGNORED_FILENAMES or lower_name.startswith('~$'):
        return None

    if not is_file_ready(source_path):
        return {
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'file': file_name,
            'status': 'wait',
            'message': 'Dosya henüz indirilmekte veya kullanımda'
        }

    # AI Analizi
    analysis = AIFileIntelligence.analyze(source_path, target_base_folder, allow_new_categories)
    category_folder = analysis['target_folder']
    os.makedirs(category_folder, exist_ok=True)

    dest_path = os.path.join(category_folder, file_name)
    dest_path = get_unique_path(dest_path)

    try:
        file_size = os.path.getsize(source_path)
        shutil.move(source_path, dest_path)
        StorageAnalyzer.invalidate_cache()
        SearchEngine.invalidate_index()
        rel_target = os.path.relpath(dest_path, target_base_folder)

        # Geri Alma ve Güvenlik sistemine kaydet
        tx = SecurityBackupEngine.record_move(
            original_path=source_path,
            target_path=dest_path,
            category=analysis['category'],
            detected_type=analysis['detected_type'],
            size_bytes=file_size
        )

        return {
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'file': file_name,
            'status': 'success',
            'target': rel_target,
            'category': analysis['category'],
            'subcategory': analysis['subcategory'],
            'detected_type': analysis['detected_type'],
            'tags': analysis['tags'],
            'tx_id': tx['id'],
            'message': f"Taşındı -> {rel_target}"
        }
    except Exception as e:
        return {
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'file': file_name,
            'status': 'error',
            'message': f"Hata: {str(e)}"
        }

def organize_item(item_path, target_base_folder, allow_new_categories=True):
    """Manuel sürüklenen veya seçilen dosya VEYA klasörü organize eder."""
    if os.path.isfile(item_path):
        return organize_file(item_path, target_base_folder, allow_new_categories)
    elif os.path.isdir(item_path):
        norm_item = os.path.normpath(item_path).lower()
        norm_target = os.path.normpath(target_base_folder).lower()
        if norm_item == norm_target or norm_item.startswith(norm_target + os.sep):
            return None
        folder_name = os.path.basename(item_path)
        analysis = AIFileIntelligence.analyze(item_path, target_base_folder, allow_new_categories)
        category_folder = analysis['target_folder']
        os.makedirs(category_folder, exist_ok=True)
        dest_path = get_unique_path(os.path.join(category_folder, folder_name))
        try:
            shutil.move(item_path, dest_path)
            StorageAnalyzer.invalidate_cache()
            SearchEngine.invalidate_index()
            rel_target = os.path.relpath(dest_path, target_base_folder)
            tx = SecurityBackupEngine.record_move(
                original_path=item_path,
                target_path=dest_path,
                category=analysis['category'],
                detected_type='Klasör',
                size_bytes=0
            )
            return {
                'timestamp': datetime.now().strftime('%H:%M:%S'),
                'file': folder_name,
                'status': 'success',
                'target': rel_target,
                'category': analysis['category'],
                'subcategory': analysis['subcategory'],
                'detected_type': 'Klasör',
                'tags': analysis['tags'],
                'tx_id': tx['id'],
                'message': f"Klasör Taşındı -> {rel_target}"
            }
        except Exception as e:
            return {
                'timestamp': datetime.now().strftime('%H:%M:%S'),
                'file': folder_name,
                'status': 'error',
                'message': f"Hata: {str(e)}"
            }
    return None

def scan_and_organize(source_folders, target_base_folder, allow_new_categories=True, desktop_baseline=None):
    """Seçilen kaynak klasörleri tarar ve dosyaları AI zekasıyla düzenler."""
    events = []
    norm_target = os.path.normpath(target_base_folder).lower()
    norm_desktop = os.path.normpath(os.path.join(os.path.expanduser('~'), 'Desktop')).lower()

    for folder in source_folders:
        if not os.path.exists(folder):
            continue
        norm_source = os.path.normpath(folder).lower()
        if norm_source == norm_target or norm_source.startswith(norm_target + os.sep):
            continue

        is_desktop = (norm_source == norm_desktop)

        try:
            for item in os.listdir(folder):
                # Masaüstünde önceden mevcut olan dosyaları ASLA elleme!
                if is_desktop and desktop_baseline and item in desktop_baseline:
                    continue

                item_path = os.path.join(folder, item)
                if item.lower() in IGNORED_FILENAMES or item.startswith('.'):
                    continue

                if os.path.isfile(item_path):
                    res = organize_file(item_path, target_base_folder, allow_new_categories)
                    if res and res.get('status') in ('success', 'error'):
                        events.append(res)
        except Exception as e:
            print(f"Tarama hatası ({folder}): {e}")

    return events
