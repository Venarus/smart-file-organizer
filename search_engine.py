"""
Semantic & Smart File Search Engine (In-Memory Indexed V2)
Provides ultra-fast multi-criteria search over organized Folders and monitored directories:
- In-memory index caching for sub-millisecond query results
- Background async pre-indexing on app launch
- Targeted category sub-tree traversal fallback
- Extension, date modified, and file size filtering
- Directory pruning for ignored packages and cache folders
"""

import os
import time
import threading
import subprocess
from datetime import datetime, timedelta

class SearchEngine:
    IGNORED_DIRS = {
        '.git', '.svn', '.hg', 'node_modules', '__pycache__', 
        '.vs', '.vscode', '.idea', 'venv', 'env', '.cache'
    }

    _index = []
    _indexed_base = None
    _index_time = 0
    _indexing_lock = threading.Lock()
    _is_indexing = False
    INDEX_TTL = 180.0  # 3 dakika

    @classmethod
    def invalidate_index(cls):
        """Dosya taşındığında veya silindiğinde arama indeksini geçersiz kılar."""
        with cls._indexing_lock:
            cls._index = []
            cls._index_time = 0

    @classmethod
    def build_index_async(cls, base_folder):
        """Arka planda sessizce arama indeksini oluşturur."""
        threading.Thread(target=lambda: cls.get_or_build_index(base_folder), daemon=True).start()

    @classmethod
    def get_or_build_index(cls, base_folder, force=False):
        """Arama indeksini döner veya gerekiyorsa oluşturur."""
        now = time.time()
        with cls._indexing_lock:
            if not force and cls._index and cls._indexed_base == base_folder and (now - cls._index_time < cls.INDEX_TTL):
                return cls._index
            if cls._is_indexing:
                return cls._index
            cls._is_indexing = True

        new_index = []
        try:
            if os.path.exists(base_folder):
                for root, dirs, files in os.walk(base_folder):
                    dirs[:] = [d for d in dirs if not d.startswith('.') and d.lower() not in cls.IGNORED_DIRS]
                    rel_folder = os.path.relpath(root, base_folder)
                    top_category = rel_folder.split(os.sep)[0] if rel_folder != '.' else 'Kök'

                    for f in files:
                        p = os.path.join(root, f)
                        try:
                            st = os.stat(p)
                            new_index.append({
                                'name': f,
                                'lower_name': f.lower(),
                                'path': p,
                                'rel_path': os.path.relpath(p, base_folder),
                                'lower_rel': rel_folder.lower(),
                                'category': top_category,
                                'lower_cat': top_category.lower(),
                                'size_bytes': st.st_size,
                                'size_human': cls._format_bytes(st.st_size),
                                'mtime': st.st_mtime,
                                'modified': datetime.fromtimestamp(st.st_mtime).strftime('%Y-%m-%d %H:%M')
                            })
                        except Exception:
                            continue
        except Exception:
            pass

        with cls._indexing_lock:
            cls._index = new_index
            cls._indexed_base = base_folder
            cls._index_time = time.time()
            cls._is_indexing = False

        return cls._index

    @classmethod
    def search(cls, base_folder, query="", category="Tümü", extension="Tümü", date_filter="Tümü", size_filter="Tümü"):
        """
        Kriterlere uygun dosyaları arar ve sonuçları listeler.
        Bellek içi indeks varsa 1-2 ms hızında arar, yoksa hedeflenmiş disk taraması yapar.
        """
        if not os.path.exists(base_folder):
            return []

        # Eğer bellek içi indeks hazırsa doğrudan bellekten ara
        if cls._index and cls._indexed_base == base_folder:
            return cls._search_in_memory(cls._index, query, category, extension, date_filter, size_filter)

        # İlk aramada indeksi arka planda başlat ve doğrudan hızlı disk araması yap
        cls.build_index_async(base_folder)
        return cls._search_disk(base_folder, query, category, extension, date_filter, size_filter)

    @classmethod
    def _search_in_memory(cls, index, query, category, extension, date_filter, size_filter):
        results = []
        now = time.time()
        q_lower = query.lower().strip()
        q_terms = [t for t in q_lower.split() if t]

        # Tarih filtre eşiği
        time_threshold = None
        if date_filter == "Bugün":
            time_threshold = now - 86400
        elif date_filter == "Bu Hafta":
            time_threshold = now - 7 * 86400
        elif date_filter == "Bu Ay":
            time_threshold = now - 30 * 86400

        target_ext = extension.lower().strip() if extension != "Tümü" else None
        target_cat = category.lower().strip() if category != "Tümü" else None

        for item in index:
            # Kategori
            if target_cat and target_cat not in item['lower_cat']:
                continue

            # Kelime eşleşmesi
            if q_terms:
                matched_all = True
                for term in q_terms:
                    if term not in item['lower_name'] and term not in item['lower_rel']:
                        matched_all = False
                        break
                if not matched_all:
                    continue

            # Uzantı
            if target_ext and not item['lower_name'].endswith(target_ext):
                continue

            # Tarih
            if time_threshold and item['mtime'] < time_threshold:
                continue

            # Boyut
            sz = item['size_bytes']
            if size_filter == "< 1 MB" and sz >= 1024 * 1024:
                continue
            elif size_filter == "1 MB - 50 MB" and (sz < 1024 * 1024 or sz > 50 * 1024 * 1024):
                continue
            elif size_filter == "> 50 MB" and sz <= 50 * 1024 * 1024:
                continue

            results.append(item)
            if len(results) >= 150:
                break

        return results

    @classmethod
    def _search_disk(cls, base_folder, query="", category="Tümü", extension="Tümü", date_filter="Tümü", size_filter="Tümü"):
        results = []
        now = datetime.now()
        q_lower = query.lower().strip()
        q_terms = [t for t in q_lower.split() if t]

        date_threshold = None
        if date_filter == "Bugün":
            date_threshold = now - timedelta(days=1)
        elif date_filter == "Bu Hafta":
            date_threshold = now - timedelta(days=7)
        elif date_filter == "Bu Ay":
            date_threshold = now - timedelta(days=30)

        target_ext = extension.lower().strip() if extension != "Tümü" else None

        search_root = base_folder
        if category != "Tümü":
            try:
                for entry in os.listdir(base_folder):
                    ep = os.path.join(base_folder, entry)
                    if os.path.isdir(ep) and category.lower() in entry.lower():
                        search_root = ep
                        break
            except Exception:
                search_root = base_folder

        for root, dirs, files in os.walk(search_root):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d.lower() not in cls.IGNORED_DIRS]

            rel_folder = os.path.relpath(root, base_folder)
            top_category = rel_folder.split(os.sep)[0] if rel_folder != '.' else 'Kök'

            if category != "Tümü" and category.lower() not in top_category.lower():
                continue

            for f in files:
                f_lower = f.lower()

                if q_terms:
                    matched_all = True
                    for term in q_terms:
                        if term not in f_lower and term not in rel_folder.lower():
                            matched_all = False
                            break
                    if not matched_all:
                        continue

                if target_ext and not f_lower.endswith(target_ext):
                    continue

                file_path = os.path.join(root, f)

                try:
                    stat = os.stat(file_path)
                    mod_time = datetime.fromtimestamp(stat.st_mtime)

                    if date_threshold and mod_time < date_threshold:
                        continue

                    sz = stat.st_size
                    if size_filter == "< 1 MB" and sz >= 1024 * 1024:
                        continue
                    elif size_filter == "1 MB - 50 MB" and (sz < 1024 * 1024 or sz > 50 * 1024 * 1024):
                        continue
                    elif size_filter == "> 50 MB" and sz <= 50 * 1024 * 1024:
                        continue

                    results.append({
                        'name': f,
                        'path': file_path,
                        'rel_path': os.path.relpath(file_path, base_folder),
                        'category': top_category,
                        'size_bytes': sz,
                        'size_human': cls._format_bytes(sz),
                        'modified': mod_time.strftime('%Y-%m-%d %H:%M')
                    })
                except Exception:
                    continue

                if len(results) >= 150:
                    break

            if len(results) >= 150:
                break

        return results

    @staticmethod
    def _format_bytes(size_bytes):
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

    @staticmethod
    def open_file(file_path):
        """Dosyayı Windows varsayılan uygulamasıyla açar."""
        if os.path.exists(file_path):
            try:
                os.startfile(file_path)
                return True
            except Exception as e:
                print(f"Dosya açma hatası: {e}")
        return False

    @staticmethod
    def reveal_in_explorer(file_path):
        """Dosyayı Windows Gezgini'nde seçili olarak gösterir."""
        if os.path.exists(file_path):
            try:
                subprocess.Popen(['explorer', '/select,', os.path.normpath(file_path)])
                return True
            except Exception as e:
                print(f"Gezginde gösterme hatası: {e}")
        return False
