"""
Security, Backup & Transaction History Engine
Manages a persistent transaction ledger of all file movements,
allowing 1-click Undo (Geri Al) to restore files to their exact original location,
and providing safety verification.
"""

import os
import json
import uuid
import shutil
from datetime import datetime

APP_DIR = os.path.dirname(os.path.abspath(__file__))
HISTORY_FILE = os.path.join(APP_DIR, 'history.json')

class SecurityBackupEngine:
    _ledger_cache = None
    _last_mtime = -1.0
    _revision = 0

    @classmethod
    def get_revision(cls) -> int:
        """İşlem defterinin değişiklik revizyon numarasını döndürür (O(1) hızlı önbellek kontrolü)."""
        cls._load_ledger()
        return cls._revision

    @classmethod
    def _load_ledger(cls):
        if not os.path.exists(HISTORY_FILE):
            if cls._ledger_cache is None or cls._ledger_cache:
                cls._ledger_cache = []
                cls._last_mtime = -1.0
                cls._revision += 1
            return cls._ledger_cache
        try:
            mtime = os.path.getmtime(HISTORY_FILE)
            if cls._ledger_cache is not None and mtime == cls._last_mtime:
                return cls._ledger_cache
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                cls._ledger_cache = json.load(f)
            cls._last_mtime = mtime
            cls._revision += 1
            return cls._ledger_cache
        except Exception:
            if cls._ledger_cache is None:
                cls._ledger_cache = []
            return cls._ledger_cache

    @classmethod
    def _save_ledger(cls, ledger):
        try:
            cls._ledger_cache = list(ledger)
            with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(ledger, f, indent=2, ensure_ascii=False)
            cls._last_mtime = os.path.getmtime(HISTORY_FILE)
            cls._revision += 1
        except Exception as e:
            print(f"Geçmiş kaydetme hatası: {e}")

    @classmethod
    def record_move(cls, original_path, target_path, category='', detected_type='', size_bytes=0):
        """Her dosya taşıma işlemini geri alınabilir bir işlem olarak kaydeder."""
        ledger = cls._load_ledger()
        tx = {
            'id': str(uuid.uuid4())[:8],
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'file_name': os.path.basename(original_path),
            'original_path': original_path,
            'target_path': target_path,
            'category': category,
            'detected_type': detected_type,
            'size_bytes': size_bytes,
            'status': 'active' # 'active' veya 'undone'
        }
        # Başa ekle (en yeni en üstte)
        ledger.insert(0, tx)
        # Maksimum 1000 kayıt tut
        if len(ledger) > 1000:
            ledger = ledger[:1000]
        cls._save_ledger(ledger)
        return tx

    @classmethod
    def undo_transaction(cls, transaction_id):
        """Belirtilen ID'ye sahip işlemi geri alır ve dosyayı eski yerine taşır."""
        ledger = cls._load_ledger()
        target_tx = None
        for tx in ledger:
            if tx.get('id') == transaction_id:
                target_tx = tx
                break

        if not target_tx:
            return {'success': False, 'message': 'İşlem kaydı bulunamadı.'}

        if target_tx.get('status') == 'undone':
            return {'success': False, 'message': 'Bu işlem zaten daha önce geri alınmış.'}

        target_path = target_tx.get('target_path')
        orig_path = target_tx.get('original_path')

        if not os.path.exists(target_path):
            return {'success': False, 'message': f'Dosya hedef konumda bulunamadı: {target_path}'}

        # Orijinal klasör yoksa oluştur
        orig_dir = os.path.dirname(orig_path)
        os.makedirs(orig_dir, exist_ok=True)

        # Eğer orijinal konumda aynı isimde başka dosya varsa koru
        final_orig_path = orig_path
        if os.path.exists(orig_path):
            base, ext = os.path.splitext(orig_path)
            counter = 1
            while os.path.exists(f"{base}_geri_alindi_{counter}{ext}"):
                counter += 1
            final_orig_path = f"{base}_geri_alindi_{counter}{ext}"

        try:
            shutil.move(target_path, final_orig_path)
            try:
                from storage_analyzer import StorageAnalyzer
                StorageAnalyzer.invalidate_cache()
                from search_engine import SearchEngine
                SearchEngine.invalidate_index()
            except Exception:
                pass
            target_tx['status'] = 'undone'
            target_tx['undone_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            target_tx['restored_to'] = final_orig_path
            cls._save_ledger(ledger)
            return {
                'success': True,
                'message': f"Dosya başarıyla eski yerine geri taşındı -> {final_orig_path}",
                'restored_path': final_orig_path
            }
        except Exception as e:
            return {'success': False, 'message': f'Geri alma hatası: {str(e)}'}

    @classmethod
    def undo_last(cls):
        """En son yapılan aktif işlemi geri alır."""
        ledger = cls._load_ledger()
        for tx in ledger:
            if tx.get('status') == 'active':
                return cls.undo_transaction(tx.get('id'))
        return {'success': False, 'message': 'Geri alınabilecek aktif işlem bulunamadı.'}

    @classmethod
    def get_history(cls, limit=100, active_only=False):
        """İşlem geçmişini listeler."""
        ledger = cls._load_ledger()
        if active_only:
            ledger = [tx for tx in ledger if tx.get('status') == 'active']
        return ledger[:limit]

    @classmethod
    def clear_history(cls):
        """İşlem geçmişini sıfırlar."""
        cls._save_ledger([])
        return True
