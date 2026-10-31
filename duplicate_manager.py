"""
Duplicate File Detection & Management Engine
Implements a high-speed multithreaded 3-tier algorithm:
1. Exact file size grouping (O(1) memory filter)
2. Fast multithreaded Head+Tail 8KB chunk hash comparison
3. SHA-256 verification with 1MB blocks for identical chunks
"""

import os
import hashlib
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

class DuplicateManager:
    IGNORED_DIRS = {
        '.git', '.svn', '.hg', 'node_modules', '__pycache__', 
        '.vs', '.vscode', '.idea', 'venv', 'env', '.cache'
    }

    @staticmethod
    def _get_chunk_hash(file_path, chunk_size=8192):
        """Dosyanın başından ve sonundan 8KB okuyarak hızlı özet üretir."""
        try:
            sz = os.path.getsize(file_path)
            hasher = hashlib.md5()
            with open(file_path, 'rb') as f:
                head = f.read(chunk_size)
                hasher.update(head)
                if sz > chunk_size * 2:
                    f.seek(-chunk_size, os.SEEK_END)
                    tail = f.read(chunk_size)
                    hasher.update(tail)
            return (file_path, hasher.hexdigest())
        except Exception:
            return (file_path, None)

    @staticmethod
    def _get_full_hash(file_path, block_size=1048576):
        """Dosyanın tam SHA-256 özetini 1MB bloklarla yüksek hızda hesaplar."""
        hasher = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                while True:
                    block = f.read(block_size)
                    if not block:
                        break
                    hasher.update(block)
            return (file_path, hasher.hexdigest())
        except Exception:
            return (file_path, None)

    @classmethod
    def scan_directory(cls, directory_path, progress_callback=None):
        """
        Belirtilen dizindeki tüm yinelenen (mükerrer) dosyaları tespit eder.
        Gereksiz disk okumalarını önlemek için 3 aşamalı filtreleme uygular.
        """
        if not os.path.exists(directory_path):
            return {'total_duplicates': 0, 'total_groups': 0, 'wasted_bytes': 0, 'wasted_human': '0 B', 'groups': [], 'total_scanned': 0}

        # 1. Aşama: Dosyaları boyutlarına göre grupla
        size_groups = {}
        total_files_scanned = 0

        for root, dirs, files in os.walk(directory_path):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d.lower() not in cls.IGNORED_DIRS]

            for f in files:
                if f.lower().startswith(('desktop.ini', 'thumbs.db', '~$')) or f.endswith(('.tmp', '.crdownload')):
                    continue
                file_path = os.path.join(root, f)
                try:
                    stat = os.stat(file_path)
                    sz = stat.st_size
                    if sz > 0:
                        size_groups.setdefault(sz, []).append(file_path)
                        total_files_scanned += 1
                except Exception:
                    continue

        if progress_callback:
            progress_callback(f"Boyut filtresi tamamlandı. {total_files_scanned} dosya analiz ediliyor...")

        # Sadece 2 veya daha fazla dosya olan boyutları filtrele
        candidate_sizes = {sz: paths for sz, paths in size_groups.items() if len(paths) > 1}
        all_candidate_paths = [p for paths in candidate_sizes.values() for p in paths]

        # 2. Aşama: Çoklu iş parçacığıyla Hızlı 8KB Head+Tail parça hash denetimi
        chunk_map = {}
        with ThreadPoolExecutor(max_workers=8) as executor:
            results = executor.map(cls._get_chunk_hash, all_candidate_paths)
            for path, c_hash in results:
                if c_hash:
                    chunk_map[path] = c_hash

        # Chunk ve boyuta göre grupla
        chunk_groups = {}
        for sz, paths in candidate_sizes.items():
            for p in paths:
                c_hash = chunk_map.get(p)
                if c_hash:
                    chunk_groups.setdefault((sz, c_hash), []).append(p)

        candidate_chunks = {k: paths for k, paths in chunk_groups.items() if len(paths) > 1}

        # 3. Aşama: Tam Doğrulama (Sadece chunk'ları tam eşleşenler için)
        final_groups = {}
        large_files_to_hash = []
        for (sz, c_hash), paths in candidate_chunks.items():
            if sz <= 8192:
                # 8KB altı dosyalar için chunk zaten dosyanın tamamıdır
                f_hash = f"fast_{c_hash}"
                for p in paths:
                    try:
                        mtime = os.path.getmtime(p)
                    except Exception:
                        mtime = 0
                    final_groups.setdefault(f_hash, []).append({
                        'path': p,
                        'name': os.path.basename(p),
                        'size': sz,
                        'modified': datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M') if mtime else ''
                    })
            else:
                large_files_to_hash.extend((p, sz) for p in paths)

        if large_files_to_hash:
            if progress_callback:
                progress_callback(f"{len(large_files_to_hash)} büyük dosya için tam doğrulama yapılıyor...")
            
            with ThreadPoolExecutor(max_workers=8) as executor:
                hash_results = executor.map(lambda item: (item[1], cls._get_full_hash(item[0])), large_files_to_hash)
                for sz, (p, f_hash) in hash_results:
                    if f_hash:
                        try:
                            mtime = os.path.getmtime(p)
                        except Exception:
                            mtime = 0
                        final_groups.setdefault(f_hash, []).append({
                            'path': p,
                            'name': os.path.basename(p),
                            'size': sz,
                            'modified': datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M') if mtime else ''
                        })

        # Sonuçları derle
        duplicate_groups = []
        total_wasted_bytes = 0
        total_dup_count = 0

        for f_hash, file_list in final_groups.items():
            if len(file_list) > 1:
                sz = file_list[0]['size']
                wasted_for_group = sz * (len(file_list) - 1)
                total_wasted_bytes += wasted_for_group
                total_dup_count += (len(file_list) - 1)

                duplicate_groups.append({
                    'hash': f_hash,
                    'file_name': file_list[0]['name'],
                    'size_bytes': sz,
                    'size_human': cls._format_bytes(sz),
                    'wasted_bytes': wasted_for_group,
                    'wasted_human': cls._format_bytes(wasted_for_group),
                    'files': file_list
                })

        # İsraf edilen alana göre en büyükten küçüğe sırala
        duplicate_groups.sort(key=lambda g: g['wasted_bytes'], reverse=True)

        return {
            'total_duplicates': total_dup_count,
            'total_groups': len(duplicate_groups),
            'wasted_bytes': total_wasted_bytes,
            'wasted_human': cls._format_bytes(total_wasted_bytes),
            'groups': duplicate_groups,
            'total_scanned': total_files_scanned
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
    def delete_file(cls, file_path):
        """Tek bir kopya dosyayı güvenle siler."""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True, "Dosya başarıyla silindi."
            return False, "Dosya bulunamadı."
        except Exception as e:
            return False, str(e)
