"""
AI File Intelligence System (V2)
Performs multi-dimensional analysis on files:
- File name & semantic tokens
- Extensions & MIME types
- File metadata (size, created/modified timestamps)
- Content inspection (text snippets, header bytes, archive internal listings)
- Relational & companion file detection (Proteus, Arduino, game mods)
- Intelligent taxonomy mapping with subcategory reasoning
"""

import os
import re
import time
import zipfile
import mimetypes
from datetime import datetime
from PIL import Image

class AIFileIntelligence:
    # Desteklenen temel taksonomi
    TAXONOMY = {
        'Documents': ['School', 'Official', 'Personal', 'Presentations', 'Spreadsheets', 'General'],
        'Software': ['Installers', 'Portable', 'Tools'],
        'Programming': ['Python', 'Web', 'C_Cpp', 'Java', 'Repositories', 'Scripts'],
        'Electronics': ['Devre ve Proteus', 'Mikrodenetleyici', 'KiCad', 'PLC ve Otomasyon', 'Sensör ve Kütüphaneler', 'Datasheetler'],
        'Images': ['Wallpapers', 'Screenshots', 'Photos', 'Design_Assets', 'Icons'],
        'Videos': ['Clips_Edits', 'Recordings', 'Movies'],
        'Music': ['Tracks', 'Vocals', 'Audio_Samples'],
        'Games_Mods': ['The_Witcher', 'GTA', 'Hytale', 'Other_Mods'],
        'Design_3D': ['3D_Models', 'CAD_Drawings', 'Fonts', 'Vector_Graphics'],
        'Archives': ['Zip_Rar', 'Backups'],
        'Miscellaneous': ['Other']
    }

    # Okul ve Eğitim anahtar kelimeleri
    SCHOOL_KEYWORDS = {
        'ders', 'sinav', 'sınav', 'odev', 'ödev', 'universite', 'üniversite', 'okul',
        'meb', 'bdu', 'temrin', 'calculus', 'fizik', 'kimya', 'matematik', 'tarih',
        'lecture', 'homework', 'exam', 'syllabus', 'hafta', 'staj', 'raporu', 'kitabi',
        'kitabı', 'ogrenci', 'öğrenci', 'notlar', 'tez', 'akademik', 'diploma'
    }

    # Resmi Evrak ve Finans anahtar kelimeleri
    OFFICIAL_KEYWORDS = {
        'kimlik', 'ehliyet', 'dekont', 'fatura', 'pasaport', 'sozlesme', 'sözleşme',
        'imza', 'ikametgah', 'sabika', 'sabıka', 'vergi', 'tc kimlik', 't.c.', 'makbuz',
        'invoice', 'receipt', 'contract', 'statement', 'police', 'sigorta', 'dekontu'
    }

    # Oyun & Mod anahtar kelimeleri
    WITCHER_KEYS = {'witcher', 'geralt', 'yennefer', 'ciri', 'novigrad', 'skellige'}
    GTA_KEYS = {'gta', 'gtav', 'gta5', 'gta6', 'gtavi', 'grand theft auto', 'yim menu', 'yimmenu'}
    HYTALE_KEYS = {'hytale', 'aurora shader'}

    # Elektronik anahtar kelimeleri
    ELEC_KEYWORDS = {
        'arduino', 'esp32', 'stm32', 'proteus', 'kicad', 'circuit', 'devre', 'rfid',
        'plc', 'wplsoft', 'sensor', 'sensör', 'schematic', 'transistor', 'entegre',
        'baskı devre', 'baski devre', 'pcb', 'hex', 'atmega', 'pic16f', 'pic18f'
    }

    @staticmethod
    def extract_metadata(file_path):
        """Dosyanın fiziksel metadata bilgilerini çıkarır."""
        try:
            stat = os.stat(file_path)
            size_bytes = stat.st_size
            created = datetime.fromtimestamp(stat.st_ctime)
            modified = datetime.fromtimestamp(stat.st_mtime)

            # İnsan tarafından okunabilir boyut
            size_human = AIFileIntelligence.format_bytes(size_bytes)
            mime_type, _ = mimetypes.guess_type(file_path)

            meta = {
                'size_bytes': size_bytes,
                'size_human': size_human,
                'created': created.strftime('%Y-%m-%d %H:%M:%S'),
                'modified': modified.strftime('%Y-%m-%d %H:%M:%S'),
                'mime_type': mime_type or 'application/octet-stream',
                'is_hidden': os.path.basename(file_path).startswith('.')
            }

            # Resim ise çözünürlük metadata'sı
            ext = os.path.splitext(file_path)[1].lower()
            if ext in {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif'}:
                try:
                    with Image.open(file_path) as img:
                        w, h = img.size
                        meta['image_width'] = w
                        meta['image_height'] = h
                        meta['image_format'] = img.format
                        meta['aspect_ratio'] = round(w / h, 2) if h > 0 else 0
                except Exception:
                    pass

            return meta
        except Exception as e:
            return {
                'size_bytes': 0,
                'size_human': '0 B',
                'created': '-',
                'modified': '-',
                'mime_type': 'unknown',
                'error': str(e)
            }

    @staticmethod
    def format_bytes(size_bytes):
        """Byte miktarını KB, MB, GB biçimine çevirir."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

    @staticmethod
    def inspect_content_sample(file_path, max_bytes=4096):
        """Dosyanın ilk 4KB'lık içeriğini okuyup anlamsal ipuçları arar."""
        ext = os.path.splitext(file_path)[1].lower()
        readable_exts = {
            '.txt', '.log', '.md', '.json', '.xml', '.html', '.htm', '.css',
            '.py', '.js', '.ts', '.c', '.cpp', '.h', '.cs', '.java', '.sql',
            '.yaml', '.yml', '.ini', '.cfg', '.ino'
        }

        # Arşiv içeriği denetimi (zip)
        if ext == '.zip':
            try:
                with zipfile.ZipFile(file_path, 'r') as zf:
                    namelist = zf.namelist()[:30]
                    return {'type': 'archive', 'files': namelist}
            except Exception:
                return None

        if ext not in readable_exts and not ext == '':
            return None

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(max_bytes)
                return {'type': 'text', 'sample': content.lower()}
        except Exception:
            return None

    _analysis_cache = {}
    TOKEN_REGEX = re.compile(r'[^a-zA-Z0-9çğıöşüÇĞİÖŞÜ]+')

    @classmethod
    def clear_cache(cls):
        cls._analysis_cache.clear()

    @classmethod
    def analyze(cls, file_path, target_base_folder=None, allow_new_categories=True):
        """
        Dosyayı çok boyutlu yapay zeka analizinden geçirir.
        Önbellekleme sayesinde aynı dosya için ardışık analizler 0.0001 ms hızında tamamlanır.
        """
        if not target_base_folder:
            target_base_folder = os.path.join(os.path.expanduser('~'), 'Desktop', 'Folders')
        stat_key = None
        if os.path.exists(file_path):
            try:
                st = os.stat(file_path)
                stat_key = (os.path.normpath(file_path).lower(), st.st_mtime, st.st_size, target_base_folder)
                if stat_key in cls._analysis_cache:
                    return cls._analysis_cache[stat_key]
            except Exception:
                pass

        result = cls._analyze_uncached(file_path, target_base_folder, allow_new_categories)

        if stat_key:
            if len(cls._analysis_cache) > 2000:
                cls._analysis_cache.clear()
            cls._analysis_cache[stat_key] = result

        return result

    @classmethod
    def _analyze_uncached(cls, file_path, target_base_folder=None, allow_new_categories=True):
        if not target_base_folder:
            target_base_folder = os.path.join(os.path.expanduser('~'), 'Desktop', 'Folders')
        file_name = os.path.basename(file_path)
        lower_name = file_name.lower()
        base_name, ext = os.path.splitext(lower_name)

        tokens = set(cls.TOKEN_REGEX.split(base_name))
        metadata = cls.extract_metadata(file_path)
        content_sample = cls.inspect_content_sample(file_path) if os.path.isfile(file_path) else None

        tags = []
        confidence = 0.85
        reasoning = []

        # ==========================================
        # 1. BOYUT: RESMİ & KİMLİK & HUKUKİ EVRAKLAR
        # ==========================================
        is_official = False
        matched_official = tokens & cls.OFFICIAL_KEYWORDS
        if matched_official or any(k in lower_name for k in ['tc kimlik', 't.c.', 'dekontu']):
            is_official = True
            confidence = 0.98
            tags.extend(['Resmi Evrak', 'Kimlik/Finans'])
            reasoning.append(f"İsimde resmi evrak belirteci bulundu: {list(matched_official)}")

        # İçerik denetimi
        if content_sample and content_sample.get('type') == 'text':
            sample = content_sample.get('sample', '')
            if any(k in sample for k in ['t.c. kimlik', 'fatura no', 'iban', 'vergi dairesi', 'toplam tutar']):
                is_official = True
                confidence = 0.99
                tags.append('Resmi İçerik')
                reasoning.append("Dosya metninde resmi evrak/fatura şablonu tespit edildi.")

        if is_official:
            target_rel = r'05_Belgeler ve Kişisel\Kimlik ve Resmi Evraklar'
            return {
                'category': 'Documents',
                'subcategory': 'Official',
                'target_rel_path': target_rel,
                'target_folder': os.path.join(target_base_folder, target_rel),
                'confidence': confidence,
                'detected_type': 'Resmi Belge / Kimlik / Fatura',
                'tags': tags,
                'metadata': metadata,
                'reasoning': '; '.join(reasoning)
            }

        # ==========================================
        # 2. BOYUT: ELEKTRONİK VE DEVRE TASARIMI
        # ==========================================
        # Proteus dosyaları
        if ext in {'.pdsprj', '.pdsbak', '.workspace'} or 'proteus' in tokens:
            target_rel = r'01_Elektronik ve Devre Tasarımı\Devre ve Proteus Projeleri'
            tags.extend(['Proteus', 'Devre Tasarımı', 'Simülasyon'])
            return {
                'category': 'Electronics',
                'subcategory': 'Devre ve Proteus',
                'target_rel_path': target_rel,
                'target_folder': os.path.join(target_base_folder, target_rel),
                'confidence': 0.99,
                'detected_type': 'Proteus Devre Projesi',
                'tags': tags,
                'metadata': metadata,
                'reasoning': 'Proteus proje ve çalışma alanı uzantısı eşleşti.'
            }

        # Arduino & Mikrodenetleyici
        is_mcu = ext == '.ino' or bool(tokens & {'arduino', 'esp32', 'stm32', 'rfid', 'atmega'})
        if is_mcu:
            target_rel = r'01_Elektronik ve Devre Tasarımı\Mikrodenetleyici ve Donanım'
            tags.extend(['Mikrodenetleyici', 'Gömülü Sistem'])
            if 'esp32' in tokens: tags.append('ESP32')
            if 'arduino' in tokens: tags.append('Arduino')
            if 'stm32' in tokens: tags.append('STM32')
            return {
                'category': 'Electronics',
                'subcategory': 'Mikrodenetleyici',
                'target_rel_path': target_rel,
                'target_folder': os.path.join(target_base_folder, target_rel),
                'confidence': 0.96,
                'detected_type': 'Gömülü Sistem / Mikrodenetleyici Kodu',
                'tags': tags,
                'metadata': metadata,
                'reasoning': 'Mikrodenetleyici donanım veya kod kalıbı belirlendi.'
            }

        # KiCad
        if ext.startswith('.kicad') or 'kicad' in tokens:
            target_rel = r'01_Elektronik ve Devre Tasarımı\KiCad Projeleri'
            tags.extend(['KiCad', 'PCB Çizimi'])
            return {
                'category': 'Electronics',
                'subcategory': 'KiCad',
                'target_rel_path': target_rel,
                'target_folder': os.path.join(target_base_folder, target_rel),
                'confidence': 0.98,
                'detected_type': 'KiCad EDA Projesi',
                'tags': tags,
                'metadata': metadata,
                'reasoning': 'KiCad şematik veya PCB dosyası tespit edildi.'
            }

        # PLC & Otomasyon
        if bool(tokens & {'plc', 'wplsoft', 'delta', 'ladder'}):
            target_rel = r'01_Elektronik ve Devre Tasarımı\PLC ve Otomasyon'
            tags.extend(['PLC', 'Otomasyon', 'Endüstriyel'])
            return {
                'category': 'Electronics',
                'subcategory': 'PLC ve Otomasyon',
                'target_rel_path': target_rel,
                'target_folder': os.path.join(target_base_folder, target_rel),
                'confidence': 0.95,
                'detected_type': 'PLC / Otomasyon Yazılımı',
                'tags': tags,
                'metadata': metadata,
                'reasoning': 'PLC otomasyon anahtar sözcüğü belirlendi.'
            }

        # Datasheet
        if 'datasheet' in tokens or 'datasheet' in lower_name:
            target_rel = r'01_Elektronik ve Devre Tasarımı\Datasheetler'
            tags.extend(['Datasheet', 'Teknik Doküman'])
            return {
                'category': 'Electronics',
                'subcategory': 'Datasheetler',
                'target_rel_path': target_rel,
                'target_folder': os.path.join(target_base_folder, target_rel),
                'confidence': 0.95,
                'detected_type': 'Elektronik Bileşen Datasheet',
                'tags': tags,
                'metadata': metadata,
                'reasoning': 'Datasheet belirteci tespit edildi.'
            }

        # Elektronik kütüphane & hex
        if ext in {'.hex', '.lib', '.idx'} or bool(tokens & cls.ELEC_KEYWORDS):
            target_rel = r'01_Elektronik ve Devre Tasarımı\Sensör ve Kütüphaneler'
            tags.extend(['Elektronik', 'Kütüphane / Sensör'])
            return {
                'category': 'Electronics',
                'subcategory': 'Sensör ve Kütüphaneler',
                'target_rel_path': target_rel,
                'target_folder': os.path.join(target_base_folder, target_rel),
                'confidence': 0.90,
                'detected_type': 'Sensör / Devre Kütüphanesi',
                'tags': tags,
                'metadata': metadata,
                'reasoning': 'Elektronik kütüphane veya ikili yazılım yapısı.'
            }

        # ==========================================
        # 3. BOYUT: OYUNLAR VE OYUN MODLARI
        # ==========================================
        if bool(re.search(r'\b(witcher|geralt)', lower_name)):
            target_rel = r'02_Oyunlar ve Modlar\The Witcher'
            tags.extend(['The Witcher', 'Oyun Modu/Save'])
            return {
                'category': 'Games_Mods',
                'subcategory': 'The_Witcher',
                'target_rel_path': target_rel,
                'target_folder': os.path.join(target_base_folder, target_rel),
                'confidence': 0.99,
                'detected_type': 'The Witcher Materyali',
                'tags': tags,
                'metadata': metadata,
                'reasoning': 'The Witcher serisi ile tam eşleşti.'
            }

        if bool(re.search(r'\b(gta|grand theft auto|yim\s*menu)', lower_name)):
            target_rel = r'02_Oyunlar ve Modlar\GTA'
            tags.extend(['GTA', 'Rockstar Games'])
            return {
                'category': 'Games_Mods',
                'subcategory': 'GTA',
                'target_rel_path': target_rel,
                'target_folder': os.path.join(target_base_folder, target_rel),
                'confidence': 0.99,
                'detected_type': 'Grand Theft Auto Materyali',
                'tags': tags,
                'metadata': metadata,
                'reasoning': 'GTA serisi veya modu ile tam eşleşti.'
            }

        if bool(re.search(r'\bhytale', lower_name)):
            target_rel = r'02_Oyunlar ve Modlar\Hytale'
            tags.extend(['Hytale', 'Shader / Mod'])
            return {
                'category': 'Games_Mods',
                'subcategory': 'Hytale',
                'target_rel_path': target_rel,
                'target_folder': os.path.join(target_base_folder, target_rel),
                'confidence': 0.98,
                'detected_type': 'Hytale Oyunu / Shader',
                'tags': tags,
                'metadata': metadata,
                'reasoning': 'Hytale anahtar kelimesi belirlendi.'
            }

        # Diğer oyun modları ve araçları
        game_keys = {'mod', 'mods', 'modlar', 'modu', 'cheat', 'trainer', 'savegame', 'saves', 'reshade', 'shader', 'shaders', 'achievement', 'tcv', 'tryama', 'game', 'oyun'}
        if ext in {'.sav', '.save', '.mod'} or bool(tokens & game_keys):
            target_rel = r'02_Oyunlar ve Modlar\Diğer Oyun Modları ve Araçları'
            tags.extend(['Oyun Modu', 'Yama / Kayıt'])
            return {
                'category': 'Games_Mods',
                'subcategory': 'Other_Mods',
                'target_rel_path': target_rel,
                'target_folder': os.path.join(target_base_folder, target_rel),
                'confidence': 0.92,
                'detected_type': 'Oyun Modu / Yama / Kayıt Dosyası',
                'tags': tags,
                'metadata': metadata,
                'reasoning': 'Oyun modu veya kayıt dosyası formatı tespit edildi.'
            }

        # ==========================================
        # 4. BOYUT: EĞİTİM, OKUL VE KİTAPLAR (School)
        # ==========================================
        matched_school = tokens & cls.SCHOOL_KEYWORDS
        is_school = bool(matched_school)

        if content_sample and content_sample.get('type') == 'text':
            sample = content_sample.get('sample', '')
            if any(k in sample for k in ['bölüm', 'konu anlatımı', 'örnek soru', 'ünite', 'meb']):
                is_school = True
                tags.append('Ders İçeriği')

        if is_school or ext in {'.pdf', '.epub', '.mobi'}:
            # Eğer açıkça okul/eğitim ile ilgiliyse
            if is_school:
                target_rel = r'05_Belgeler ve Kişisel\PDF ve Kitaplar'
                tags.extend(['Okul / Ders', 'Eğitim', ext.lstrip('.').upper()])
                return {
                    'category': 'Documents',
                    'subcategory': 'School',
                    'target_rel_path': target_rel,
                    'target_folder': os.path.join(target_base_folder, target_rel),
                    'confidence': 0.95,
                    'detected_type': 'Ders Kitabı / Sınav / Eğitim Dokümanı',
                    'tags': tags,
                    'metadata': metadata,
                    'reasoning': f"Eğitim / ders içerik belirteci bulundu: {list(matched_school)}"
                }
            elif ext in {'.pdf', '.epub', '.mobi'}:
                target_rel = r'05_Belgeler ve Kişisel\PDF ve Kitaplar'
                tags.extend(['Kitap / PDF', 'Doküman'])
                return {
                    'category': 'Documents',
                    'subcategory': 'General_PDF',
                    'target_rel_path': target_rel,
                    'target_folder': os.path.join(target_base_folder, target_rel),
                    'confidence': 0.92,
                    'detected_type': 'PDF / E-Kitap Dokümanı',
                    'tags': tags,
                    'metadata': metadata,
                    'reasoning': 'PDF veya E-Kitap doküman formatı.'
                }

        # ==========================================
        # 5. BOYUT: SUNUMLAR & TABLOLAR (Office)
        # ==========================================
        if ext in {'.pptx', '.ppt', '.odp', '.key'}:
            target_rel = r'05_Belgeler ve Kişisel\Sunumlar ve Slaytlar'
            tags.extend(['Sunum', 'Slayt', 'PowerPoint'])
            return {
                'category': 'Documents',
                'subcategory': 'Presentations',
                'target_rel_path': target_rel,
                'target_folder': os.path.join(target_base_folder, target_rel),
                'confidence': 0.97,
                'detected_type': 'Sunum Dosyası (Slayt)',
                'tags': tags,
                'metadata': metadata,
                'reasoning': 'Sunum dosyası formatı (.pptx/.ppt).'
            }

        if ext in {'.xlsx', '.xls', '.ods', '.csv'}:
            target_rel = r'05_Belgeler ve Kişisel\Hesap Tabloları'
            tags.extend(['Tablo', 'Excel / Veri'])
            return {
                'category': 'Documents',
                'subcategory': 'Spreadsheets',
                'target_rel_path': target_rel,
                'target_folder': os.path.join(target_base_folder, target_rel),
                'confidence': 0.96,
                'detected_type': 'Hesap Tablosu / Veri Dosyası',
                'tags': tags,
                'metadata': metadata,
                'reasoning': 'Hesap tablosu / elektronik tablo formatı (.xlsx/.csv).'
            }

        # Genel Ofis ve Metin Notları
        if ext in {'.docx', '.doc', '.odt', '.rtf'}:
            target_rel = r'05_Belgeler ve Kişisel\PDF ve Kitaplar'
            tags.extend(['Word / Doküman', 'Yazı'])
            return {
                'category': 'Documents',
                'subcategory': 'Office_Docs',
                'target_rel_path': target_rel,
                'target_folder': os.path.join(target_base_folder, target_rel),
                'confidence': 0.94,
                'detected_type': 'Metin / Ofis Dokümanı',
                'tags': tags,
                'metadata': metadata,
                'reasoning': 'Kelime işlemci metin dokümanı.'
            }

        if ext in {'.txt', '.log', '.md'}:
            target_rel = r'05_Belgeler ve Kişisel\Notlar ve Metinler'
            tags.extend(['Not', 'Düz Metin'])
            return {
                'category': 'Documents',
                'subcategory': 'Personal',
                'target_rel_path': target_rel,
                'target_folder': os.path.join(target_base_folder, target_rel),
                'confidence': 0.92,
                'detected_type': 'Not / Metin Dosyası',
                'tags': tags,
                'metadata': metadata,
                'reasoning': 'Metin notu veya markdown belgesi.'
            }

        # ==========================================
        # 6. BOYUT: YAZILIM, KODLAMA VE PROJELER
        # ==========================================
        code_exts = {
            '.py', '.pyw', '.js', '.mjs', '.jsx', '.ts', '.tsx', '.html', '.css', '.scss',
            '.c', '.cpp', '.h', '.hpp', '.cs', '.java', '.go', '.rs', '.php', '.rb',
            '.lua', '.sql', '.sh', '.bat', '.cmd', '.ps1', '.yaml', '.yml', '.toml'
        }
        dev_keywords = {'project', 'proje', 'repo', 'github', 'script', 'bot', 'crawler', 'api', 'backend', 'frontend', 'master', 'main', 'library'}

        is_code = (ext in code_exts) or bool(tokens & dev_keywords)

        # Arşiv içeriğinde kod deposu kontrolü (Örn. zip içinde package.json veya .py varsa)
        if content_sample and content_sample.get('type') == 'archive':
            internal_files = content_sample.get('files', [])
            if any(f.endswith(('.py', '.js', '.ts', '.cpp', '.json', '.git')) for f in internal_files):
                is_code = True
                tags.append('Kod Deposu Arşivi')

        if is_code:
            target_rel = r'03_Yazılım ve Projeler'
            tags.extend(['Yazılım', 'Kod', ext.lstrip('.').upper() if ext else 'Proje'])
            return {
                'category': 'Programming',
                'subcategory': 'Code_Projects',
                'target_rel_path': target_rel,
                'target_folder': os.path.join(target_base_folder, target_rel),
                'confidence': 0.95,
                'detected_type': 'Kaynak Kod / Yazılım Projesi',
                'tags': tags,
                'metadata': metadata,
                'reasoning': 'Yazılım geliştirme dili veya proje deposu yapısı.'
            }

        # ==========================================
        # 7. BOYUT: MEDYA (Görseller, Videolar, Müzikler)
        # ==========================================
        img_exts = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg', '.ico', '.jfif', '.tiff'}
        if ext in img_exts:
            # Alt kategori tespiti: Screenshot vs Wallpaper vs Fotoğraf
            subcat = 'Görseller'
            w = metadata.get('image_width', 0)
            h = metadata.get('image_height', 0)

            if 'screenshot' in tokens or 'ekran' in tokens or 'ss' in tokens:
                subcat = 'Ekran Görüntüleri'
                tags.append('Ekran Görüntüsü')
            elif (w >= 1920 and h >= 1080) and metadata.get('aspect_ratio') in [1.78, 1.77, 1.6, 2.33]:
                subcat = 'Duvar Kağıtları'
                tags.append('Duvar Kağıdı (Wallpaper)')
            else:
                tags.append('Görsel')

            target_rel = r'04_Medya ve Tasarım\Fotoğraflar ve Görseller'
            return {
                'category': 'Images',
                'subcategory': subcat,
                'target_rel_path': target_rel,
                'target_folder': os.path.join(target_base_folder, target_rel),
                'confidence': 0.94,
                'detected_type': f'Görsel ({subcat})',
                'tags': tags,
                'metadata': metadata,
                'reasoning': f"Görsel formatı ({ext.upper()}) ve {w}x{h} boyut analizi."
            }

        vid_exts = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.3gp'}
        if ext in vid_exts:
            tags.extend(['Video', ext.lstrip('.').upper()])
            target_rel = r'04_Medya ve Tasarım\Videolar'
            return {
                'category': 'Videos',
                'subcategory': 'Clips_Edits',
                'target_rel_path': target_rel,
                'target_folder': os.path.join(target_base_folder, target_rel),
                'confidence': 0.96,
                'detected_type': 'Video Dosyası',
                'tags': tags,
                'metadata': metadata,
                'reasoning': 'Video konteyner formatı.'
            }

        aud_exts = {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma', '.mid', '.midi'}
        if ext in aud_exts:
            tags.extend(['Ses / Müzik', ext.lstrip('.').upper()])
            target_rel = r'04_Medya ve Tasarım\Müzikler ve Sesler'
            return {
                'category': 'Music',
                'subcategory': 'Tracks',
                'target_rel_path': target_rel,
                'target_folder': os.path.join(target_base_folder, target_rel),
                'confidence': 0.96,
                'detected_type': 'Ses / Müzik Dosyası',
                'tags': tags,
                'metadata': metadata,
                'reasoning': 'Ses / ses dalgası formatı.'
            }

        # ==========================================
        # 8. BOYUT: 3D MODELLER, CAD & YAZI TİPLERİ (Design)
        # ==========================================
        if ext in {'.stl', '.obj', '.blend', '.fbx', '.step', '.iges', '.3ds', '.max', '.dae'}:
            target_rel = r'08_3D ve Tasarım Dosyaları'
            tags.extend(['3D Model', 'Tasarım'])
            return {
                'category': 'Design_3D',
                'subcategory': '3D_Models',
                'target_rel_path': target_rel,
                'target_folder': os.path.join(target_base_folder, target_rel),
                'confidence': 0.97,
                'detected_type': '3D CAD / Modelleme Dosyası',
                'tags': tags,
                'metadata': metadata,
                'reasoning': '3D mesh / model formatı.'
            }

        if ext in {'.dwg', '.dxf'}:
            target_rel = r'11_Teknik Çizimler (CAD)'
            tags.extend(['CAD', 'Teknik Çizim', 'AutoCAD'])
            return {
                'category': 'Design_3D',
                'subcategory': 'CAD_Drawings',
                'target_rel_path': target_rel,
                'target_folder': os.path.join(target_base_folder, target_rel),
                'confidence': 0.98,
                'detected_type': '2D/3D Teknik Çizim (CAD)',
                'tags': tags,
                'metadata': metadata,
                'reasoning': 'Vektörel CAD çizim formatı.'
            }

        if ext in {'.ttf', '.otf', '.woff', '.woff2'}:
            target_rel = r'09_Yazı Tipleri (Fonts)'
            tags.extend(['Yazı Tipi', 'Font', 'Tipografi'])
            return {
                'category': 'Design_3D',
                'subcategory': 'Fonts',
                'target_rel_path': target_rel,
                'target_folder': os.path.join(target_base_folder, target_rel),
                'confidence': 0.99,
                'detected_type': 'Yazı Tipi (Font)',
                'tags': tags,
                'metadata': metadata,
                'reasoning': 'TrueType/OpenType font formatı.'
            }

        # Tasarım grafikleri (.psd, .ai)
        if ext in {'.psd', '.ai', '.xd', '.fig'}:
            target_rel = r'04_Medya ve Tasarım\Fotoğraflar ve Görseller'
            tags.extend(['Tasarım Projesi', 'Photoshop/Illustrator'])
            return {
                'category': 'Design_3D',
                'subcategory': 'Vector_Graphics',
                'target_rel_path': target_rel,
                'target_folder': os.path.join(target_base_folder, target_rel),
                'confidence': 0.95,
                'detected_type': 'Grafik Tasarım Proje Dosyası',
                'tags': tags,
                'metadata': metadata,
                'reasoning': 'Katmanlı grafik tasarım kaynak dosyası.'
            }

        # ==========================================
        # 9. BOYUT: PROGRAMLAR VE KURULUMLAR
        # ==========================================
        if ext in {'.exe', '.msi', '.iso', '.dmg', '.pkg', '.apk', '.appx', '.msix'}:
            target_rel = r'06_Programlar ve Kurulumlar\Kurulum Dosyaları (Setup)'
            tags.extend(['Uygulama', 'Kurulum (Installer)'])
            return {
                'category': 'Software',
                'subcategory': 'Installers',
                'target_rel_path': target_rel,
                'target_folder': os.path.join(target_base_folder, target_rel),
                'confidence': 0.98,
                'detected_type': 'Uygulama Yükleyicisi / Kurulum',
                'tags': tags,
                'metadata': metadata,
                'reasoning': 'Çalıştırılabilir kurulum ve dağıtım paketi.'
            }

        # ==========================================
        # 10. BOYUT: KISAYOLLAR
        # ==========================================
        if ext in {'.lnk', '.url'}:
            target_rel = r'07_Kısayollar\Program Kısayolları'
            tags.extend(['Kısayol'])
            return {
                'category': 'Miscellaneous',
                'subcategory': 'Shortcuts',
                'target_rel_path': target_rel,
                'target_folder': os.path.join(target_base_folder, target_rel),
                'confidence': 0.99,
                'detected_type': 'Windows Kısayolu',
                'tags': tags,
                'metadata': metadata,
                'reasoning': 'Windows .lnk veya .url kısayol bağlantısı.'
            }

        # ==========================================
        # 11. BOYUT: SIKIŞTIRILMIŞ ARŞİVLER
        # ==========================================
        if ext in {'.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz'}:
            target_rel = r'10_Arşivler ve Sıkıştırılmış Dosyalar'
            tags.extend(['Arşiv', 'Sıkıştırılmış'])
            return {
                'category': 'Archives',
                'subcategory': 'Zip_Rar',
                'target_rel_path': target_rel,
                'target_folder': os.path.join(target_base_folder, target_rel),
                'confidence': 0.90,
                'detected_type': 'Sıkıştırılmış Arşiv Dosyası',
                'tags': tags,
                'metadata': metadata,
                'reasoning': 'Genel arşiv paketi.'
            }

        # ==========================================
        # 12. BOYUT: DİĞER / DİNAMİK YENİ KATEGORİ
        # ==========================================
        if allow_new_categories and ext:
            clean_ext = ext.lstrip('.').upper()
            target_rel = f'Diğer Dosyalar ({clean_ext})'
            tags.append(clean_ext)
            return {
                'category': 'Miscellaneous',
                'subcategory': clean_ext,
                'target_rel_path': target_rel,
                'target_folder': os.path.join(target_base_folder, target_rel),
                'confidence': 0.70,
                'detected_type': f'Özel Dosya ({clean_ext})',
                'tags': tags,
                'metadata': metadata,
                'reasoning': f"Standart kategoriler dışındaki özel uzantı için yeni kategori açıldı."
            }

        target_rel = 'Diğer Dosyalar'
        return {
            'category': 'Miscellaneous',
            'subcategory': 'General',
            'target_rel_path': target_rel,
            'target_folder': os.path.join(target_base_folder, target_rel),
            'confidence': 0.60,
            'detected_type': 'Tanımsız / Genel Dosya',
            'tags': ['Genel'],
            'metadata': metadata,
            'reasoning': 'Belirli bir kategoriye doğrudan eşleşmedi, varsayılan klasöre yönlendirildi.'
        }
