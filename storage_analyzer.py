"""
Storage Analyzer Engine (Instant Cache & Persistence V2)
Provides granular analytics on disk storage usage, category distribution,
file counts, extension breakdown, and top largest space-consuming files.
Uses disk-persisted cache (storage_cache.json) to eliminate startup delays completely.
"""

import os
import json
import time

APP_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_FILE = os.path.join(APP_DIR, 'storage_cache.json')

class StorageAnalyzer:
    _cache = {}
    _cache_time = 0
    CACHE_TTL = 300.0  # 5 dakika

    IGNORED_DIRS = {
        '.git', '.svn', '.hg', 'node_modules', '__pycache__', 
        '.vs', '.vscode', '.idea', 'venv', 'env', '.cache'
    }

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

    @classmethod
    def load_persisted_cache(cls):
        """Uygulama açılışında kayıtlı önbelleği anında yükler."""
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    base_folder = data.get('_base_folder', '')
                    if base_folder and os.path.exists(base_folder):
                        cls._cache[base_folder] = data
                        cls._cache_time = time.time()
                        return data
            except Exception:
                pass
        return None

    @classmethod
    def save_persisted_cache(cls, base_folder, data):
        """Hesaplanan önbelleği diske yazar."""
        try:
            data['_base_folder'] = base_folder
            with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    @classmethod
    def invalidate_cache(cls):
        """Dosya taşındığında veya kullanıcı yenilediğinde önbelleği temizler."""
        cls._cache.clear()
        cls._cache_time = 0
        if os.path.exists(CACHE_FILE):
            try:
                os.remove(CACHE_FILE)
            except Exception:
                pass

    @classmethod
    def analyze_folder(cls, base_folder, force_refresh=False):
        """
        Belirtilen ana klasörün (Folders) depolama dağılımını hesaplar.
        Diskte kayıtlı önbellek varsa 0.1 ms hızında anında döner.
        """
        now = time.time()
        if not force_refresh:
            if (now - cls._cache_time < cls.CACHE_TTL) and base_folder in cls._cache:
                return cls._cache[base_folder]
            persisted = cls.load_persisted_cache()
            if persisted and persisted.get('_base_folder') == base_folder:
                return persisted

        if not os.path.exists(base_folder):
            return {
                'total_size_bytes': 0,
                'total_size_human': '0 B',
                'total_files': 0,
                'total_dirs': 0,
                'categories': [],
                'category_map': {},
                'extensions': [],
                'largest_files': []
            }

        total_size = 0
        total_files = 0
        total_dirs = 0

        category_stats = {}
        ext_stats = {}
        all_files = []

        try:
            top_entries = sorted(os.listdir(base_folder))
        except Exception:
            top_entries = []

        for entry in top_entries:
            entry_path = os.path.join(base_folder, entry)
            if os.path.isdir(entry_path):
                total_dirs += 1
                cat_name = entry
                category_stats[cat_name] = {'size': 0, 'count': 0, 'path': entry_path}

                for root, dirs, files in os.walk(entry_path):
                    dirs[:] = [d for d in dirs if not d.startswith('.') and d.lower() not in cls.IGNORED_DIRS]
                    total_dirs += len(dirs)

                    for f in files:
                        p = os.path.join(root, f)
                        try:
                            sz = os.path.getsize(p)
                            total_size += sz
                            total_files += 1
                            category_stats[cat_name]['size'] += sz
                            category_stats[cat_name]['count'] += 1

                            ext = os.path.splitext(f)[1].lower() or 'uzantısız'
                            ext_entry = ext_stats.setdefault(ext, {'size': 0, 'count': 0})
                            ext_entry['size'] += sz
                            ext_entry['count'] += 1

                            all_files.append((sz, f, p, cat_name))
                        except Exception:
                            continue
            else:
                try:
                    sz = os.path.getsize(entry_path)
                    total_size += sz
                    total_files += 1
                    cat_name = 'Kök Dizin'
                    category_stats.setdefault(cat_name, {'size': 0, 'count': 0, 'path': base_folder})
                    category_stats[cat_name]['size'] += sz
                    category_stats[cat_name]['count'] += 1

                    ext = os.path.splitext(entry)[1].lower() or 'uzantısız'
                    ext_entry = ext_stats.setdefault(ext, {'size': 0, 'count': 0})
                    ext_entry['size'] += sz
                    ext_entry['count'] += 1

                    all_files.append((sz, entry, entry_path, cat_name))
                except Exception:
                    pass

        categories_list = []
        for cat, data in category_stats.items():
            pct = round((data['size'] / total_size * 100), 1) if total_size > 0 else 0
            categories_list.append({
                'name': cat,
                'path': data['path'],
                'size_bytes': data['size'],
                'size_human': cls._format_bytes(data['size']),
                'count': data['count'],
                'percentage': pct
            })

        categories_list.sort(key=lambda x: x['size_bytes'], reverse=True)

        ext_list = []
        for ext, data in ext_stats.items():
            pct = round((data['size'] / total_size * 100), 1) if total_size > 0 else 0
            ext_list.append({
                'ext': ext,
                'size_bytes': data['size'],
                'size_human': cls._format_bytes(data['size']),
                'count': data['count'],
                'percentage': pct
            })
        ext_list.sort(key=lambda x: x['size_bytes'], reverse=True)

        all_files.sort(key=lambda x: x[0], reverse=True)
        largest_files = []
        for sz, name, path, cat in all_files[:10]:
            largest_files.append({
                'name': name,
                'path': path,
                'category': cat,
                'size_bytes': sz,
                'size_human': cls._format_bytes(sz)
            })

        result = {
            'total_size_bytes': total_size,
            'total_size_human': cls._format_bytes(total_size),
            'total_files': total_files,
            'total_dirs': total_dirs,
            'categories': categories_list,
            'category_map': {c['name']: c for c in categories_list},
            'extensions': ext_list[:8],
            'largest_files': largest_files
        }

        cls._cache[base_folder] = result
        cls._cache_time = now
        cls.save_persisted_cache(base_folder, result)
        return result

# Uygulama içe aktarıldığında önbelleği diski yormadan doğrudan yükle
StorageAnalyzer.load_persisted_cache()
