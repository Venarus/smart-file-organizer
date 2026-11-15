"""
Premium Glass Dashboard (V2.1 — Premium Glass Edition)
Features:
- Frosted Aurora Glass Hero Header with live Organization Status badge
- 4 Layered Glass Telemetry Cards with glowing Glass Orbs & Animated Counters:
  1. Toplam Dosya (Total Files)
  2. Düzenlenen Dosya (Organized Files)
  3. Bekleyen Organizasyon (Pending Organization — live scan of monitored folders)
  4. Depolama Kullanımı (Storage Usage with animated progress bar)
- Bento Grid: Translucent Drag & Drop Portal + Top File Categories Progress Matrix
- Live Recent Activity Stream with File-Type Badges + Quick AI Actions Pod
"""

import os
import time
import threading
from datetime import datetime
import customtkinter as ctk
from theme import FluentTheme
from glass_engine import GlassArtEngine
from storage_analyzer import StorageAnalyzer
from security_backup import SecurityBackupEngine
from animation import FluidAnimator, UIBridge
from notification_center import FluentContextMenu
from command_palette import CommandPalette
from config import DEFAULT_DESKTOP


class HomeView(ctk.CTkFrame):
    def __init__(self, master, app_controller):
        super().__init__(master, fg_color="transparent")
        self.app = app_controller
        self.theme_mode = self.app.theme_mode
        self._is_loading_stats = False
        self._is_updating_pending = False
        self._last_pending_ts = 0.0
        self._rendered_ledger_rev = -1
        self._rendered_storage_id = None
        self._prev_files = 0
        self._prev_organized = 0
        self._prev_pending = 0

        self._build_ui()

    def update_theme(self, theme_mode):
        self.theme_mode = theme_mode
        self._rendered_ledger_rev = -1
        self._rendered_storage_id = None
        for widget in self.winfo_children():
            widget.destroy()
        self._build_ui()

    @staticmethod
    def _get_activity_summary():
        history = SecurityBackupEngine.get_history(limit=1000, active_only=True)
        today_prefix = datetime.now().strftime('%Y-%m-%d')
        today_cnt = sum(1 for tx in history if str(tx.get('timestamp', '')).startswith(today_prefix))
        return {'today': today_cnt, 'total': len(history)}

    def _count_pending_files(self) -> int:
        """İzlenen kaynak klasörlerde (Masaüstü koruma listesi hariç) bekleyen dosya sayısını hesaplar."""
        sources = self.app.cfg.get('sources', [])
        target = os.path.normpath(self.app.cfg.get('target', '')).lower()
        norm_dt = os.path.normpath(DEFAULT_DESKTOP).lower()
        baseline = set(self.app.cfg.get('desktop_baseline', []))
        ignored = {'desktop.ini', 'thumbs.db', '.ds_store'}
        pending = 0

        for folder in sources:
            if not os.path.exists(folder):
                continue
            nf = os.path.normpath(folder).lower()
            if nf == target or nf.startswith(target + os.sep):
                continue
            is_dt = (nf == norm_dt)
            try:
                for item in os.listdir(folder):
                    if item.lower() in ignored or item.startswith('.'):
                        continue
                    if is_dt and item in baseline:
                        continue
                    ip = os.path.join(folder, item)
                    if os.path.isfile(ip):
                        pending += 1
            except Exception:
                pass
        return pending

    def on_page_show(self):
        """
        Sayfa tekrar görünür olduğunda yalnızca veri revizyonu değişmişse
        bileşenleri günceller; veri değişmediyse 0.1 ms içinde anında döner.
        """
        c = lambda token: FluentTheme.c(token, self.theme_mode)
        cur_rev = SecurityBackupEngine.get_revision()

        if cur_rev != self._rendered_ledger_rev:
            summary = self._get_activity_summary()
            new_organized = summary.get('total', 0)

            if hasattr(self, 'lbl_organized_files') and self.lbl_organized_files.winfo_exists():
                FluidAnimator.animate_counter(
                    self.lbl_organized_files,
                    self._prev_organized,
                    new_organized,
                    duration_ms=FluidAnimator.TIMING_COMPLEX
                )
                self._prev_organized = new_organized

            if hasattr(self, 'lbl_organized_sub') and self.lbl_organized_sub.winfo_exists():
                self.lbl_organized_sub.configure(text=f"Bugün: {summary.get('today', 0)} dosya düzenlendi")

            if hasattr(self, 'recent_container') and self.recent_container.winfo_exists():
                self._populate_recent_list(c)
            self._rendered_ledger_rev = cur_rev

        target_base = self.app.cfg.get('target', '')
        cached_storage = StorageAnalyzer._cache.get(target_base)
        if cached_storage is not None:
            if id(cached_storage) != self._rendered_storage_id:
                self._apply_storage_stats(cached_storage)
        elif not self._is_loading_stats:
            self._is_loading_stats = True
            threading.Thread(target=self._async_load_stats, args=(target_base,), daemon=True).start()

        # Bekleyen dosyaları en fazla 4 saniyede bir arka planda kontrol et
        now = time.perf_counter()
        if not self._is_updating_pending and (now - self._last_pending_ts) > 4.0:
            self._is_updating_pending = True
            self._last_pending_ts = now
            threading.Thread(target=self._async_update_pending, daemon=True).start()

    def _async_update_pending(self):
        try:
            cnt = self._count_pending_files()

            def _apply():
                if hasattr(self, 'lbl_pending_files') and self.lbl_pending_files.winfo_exists():
                    if cnt != self._prev_pending:
                        FluidAnimator.animate_counter(
                            self.lbl_pending_files,
                            self._prev_pending,
                            cnt,
                            duration_ms=FluidAnimator.TIMING_COMPLEX
                        )
                        self._prev_pending = cnt
                    else:
                        self.lbl_pending_files.configure(text=str(cnt))
                if hasattr(self, 'lbl_pending_sub') and self.lbl_pending_sub.winfo_exists():
                    status_txt = "Tüm klasörler tertemiz ✨" if cnt == 0 else f"{cnt} yeni dosya organize edilmeye hazır"
                    self.lbl_pending_sub.configure(text=status_txt)

            UIBridge.post(_apply)
        finally:
            self._is_updating_pending = False

    def _build_ui(self):
        c = lambda token: FluentTheme.c(token, self.theme_mode)

        self.scroll = ctk.CTkScrollableFrame(
            self,
            fg_color=c('bg_mica'),
            scrollbar_button_color=c('border'),
            scrollbar_button_hover_color=c('accent')
        )
        self.scroll.pack(fill="both", expand=True, padx=10, pady=(4, 6))
        try:
            self.scroll._parent_canvas.configure(yscrollincrement=4)
        except Exception:
            pass

        # =========================================================================
        # 1. AURORA FROSTED GLASS HERO BANNER (Üst Karşılama & Durum Paneli)
        # =========================================================================
        hero_card = ctk.CTkFrame(
            self.scroll,
            fg_color=c('bg_card'),
            corner_radius=16,
            border_width=1,
            border_color=c('border_hover')
        )
        hero_card.pack(fill="x", pady=(4, 14))
        FluidAnimator.bind_card_hover(
            hero_card,
            self.theme_mode,
            normal_border_token='border',
            hover_border_token='border_hover'
        )

        hero_inner = ctk.CTkFrame(hero_card, fg_color="transparent")
        hero_inner.pack(fill="x", padx=22, pady=18)

        hero_left = ctk.CTkFrame(hero_inner, fg_color="transparent")
        hero_left.pack(side="left", fill="x", expand=True)

        status_pill_row = ctk.CTkFrame(hero_left, fg_color="transparent")
        status_pill_row.pack(anchor="w", pady=(0, 6))

        is_watching = self.app.cfg.get('auto_watch', True)
        pill_text = "🟢 AI FILE INTELLIGENCE ONLINE  •  OTOMATİK İZLEME AKTİF" if is_watching else "⏸️ OTOMATİK İZLEME DURAKLATILDI"
        pill_col = c('success') if is_watching else c('warning')
        pill_bg = c('success_bg') if is_watching else c('warning_bg')

        ctk.CTkLabel(
            status_pill_row,
            text=pill_text,
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=pill_col,
            fg_color=pill_bg,
            corner_radius=6,
            padx=10,
            pady=3
        ).pack(side="left")

        ctk.CTkLabel(
            status_pill_row,
            text=f"🛡️ Masaüstü Koruması: {len(self.app.cfg.get('desktop_baseline', []))} öğe kilitli",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=c('accent_violet_light'),
            fg_color=c('bg_card_secondary'),
            corner_radius=6,
            padx=10,
            pady=3
        ).pack(side="left", padx=8)

        ctk.CTkLabel(
            hero_left,
            text="Premium Glass Komuta Merkezi",
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=25, weight="bold"),
            text_color=c('text_primary')
        ).pack(anchor="w")

        ctk.CTkLabel(
            hero_left,
            text="Dosyalarınız gerçek zamanlı yapay zekâ içerik analizi ile Desktop/Folders mimarisinde güvenle korunuyor.",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=c('text_secondary')
        ).pack(anchor="w", pady=(2, 0))

        hero_right = ctk.CTkFrame(hero_inner, fg_color="transparent")
        hero_right.pack(side="right")

        ctk.CTkButton(
            hero_right,
            text="⚡ Şimdi Tara",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=c('accent'),
            hover_color=c('accent_hover'),
            text_color="#FFFFFF",
            corner_radius=9,
            height=36,
            width=120,
            command=self.app.trigger_manual_scan
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            hero_right,
            text="📂 Folders'ı Aç",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=c('bg_card_secondary'),
            hover_color=c('bg_card_hover'),
            text_color=c('text_primary'),
            border_width=1,
            border_color=c('border'),
            corner_radius=9,
            height=36,
            width=120,
            command=self.app.open_target_folder
        ).pack(side="left", padx=5)

        # =========================================================================
        # 2. 4'LÜ KATMANLI CAM TELEMETRİ KARTLARI (4-Column Glass Metric Grid)
        # =========================================================================
        stats_grid = ctk.CTkFrame(self.scroll, fg_color="transparent")
        stats_grid.pack(fill="x", pady=(0, 14))
        for i in range(4):
            stats_grid.grid_columnconfigure(i, weight=1, uniform="glass_stat")

        target_base = self.app.cfg.get('target', '')
        summary = self._get_activity_summary()
        cached_storage = StorageAnalyzer._cache.get(target_base)

        init_files = cached_storage.get('total_files', 0) if cached_storage else 0
        init_size = cached_storage.get('total_size_human', 'Hesaplanıyor...') if cached_storage else "Hesaplanıyor..."
        init_cats = len(cached_storage.get('categories', [])) if cached_storage else 0
        init_organized = summary.get('total', 0)

        self.lbl_total_files, self.lbl_total_files_sub = self._create_glass_stat_card(
            stats_grid, 0, "📂", c('accent'), "TOPLAM DOSYA", "0", f"{init_cats} aktif kategori içinde", c
        )
        self.lbl_organized_files, self.lbl_organized_sub = self._create_glass_stat_card(
            stats_grid, 1, "✨", c('accent_violet'), "DÜZENLENEN İŞLEM", "0", f"Bugün: {summary.get('today', 0)} dosya düzenlendi", c
        )
        self.lbl_pending_files, self.lbl_pending_sub = self._create_glass_stat_card(
            stats_grid, 2, "⏳", c('warning'), "BEKLİYOR (KAYNAKLAR)", "0", "İzlenen klasörler kontrol ediliyor...", c
        )
        self.lbl_total_size, self.lbl_storage_sub = self._create_glass_stat_card(
            stats_grid, 3, "💎", c('success'), "DEPOLAMA HACMİ", init_size, "Folders toplam disk kullanımı", c
        )

        FluidAnimator.animate_counter(self.lbl_total_files, 0, init_files, duration_ms=FluidAnimator.TIMING_COMPLEX)
        FluidAnimator.animate_counter(self.lbl_organized_files, 0, init_organized, duration_ms=FluidAnimator.TIMING_COMPLEX)
        self._prev_files = init_files
        self._prev_organized = init_organized
        threading.Thread(target=self._async_update_pending, daemon=True).start()

        # =========================================================================
        # 3. ORTA BENTO SATIRI: SÜRÜKLE-BIRAK PORTALI & KATEGORİ DAĞILIM MATRİSİ
        # =========================================================================
        mid_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        mid_frame.pack(fill="x", pady=(0, 14))
        mid_frame.grid_columnconfigure(0, weight=11)
        mid_frame.grid_columnconfigure(1, weight=9)

        # Sol: Yarı-Saydam Sürükle & Bırak ve Sabitlenen Klasörler Portalı
        self.drop_card = ctk.CTkFrame(
            mid_frame,
            fg_color=c('bg_card'),
            corner_radius=14,
            border_width=1,
            border_color=c('accent')
        )
        self.drop_card.grid(row=0, column=0, sticky="nsew", padx=(0, 7))
        FluidAnimator.bind_card_hover(
            self.drop_card,
            self.theme_mode,
            normal_border_token='accent',
            hover_border_token='border_hover'
        )

        drop_inner = ctk.CTkFrame(self.drop_card, fg_color="transparent")
        drop_inner.pack(fill="both", expand=True, padx=20, pady=18)

        drop_top = ctk.CTkFrame(drop_inner, fg_color="transparent")
        drop_top.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(
            drop_top,
            text="📥 Akıllı Cam Sürükle & Bırak Portalı",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=c('accent_light')
        ).pack(side="left")

        ctk.CTkLabel(
            drop_top,
            text="ANINDA ANALİZ",
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color=c('accent_violet_light'),
            fg_color=c('bg_card_secondary'),
            corner_radius=5,
            padx=8,
            pady=2
        ).pack(side="right")

        drop_well = ctk.CTkFrame(
            drop_inner,
            fg_color=c('bg_card_secondary'),
            corner_radius=12,
            border_width=1,
            border_color=c('border')
        )
        drop_well.pack(fill="x", pady=(2, 12))

        ctk.CTkLabel(
            drop_well,
            text="✨ Dosya veya Klasörleri Pencerenin Herhangi Bir Yerine Bırakın\nAI Motoru içerik, uzantı ve metadata analiziyle doğru kategoriye otomatik taşır.",
            font=ctk.CTkFont(size=12),
            text_color=c('text_secondary'),
            justify="center"
        ).pack(padx=16, pady=18)

        ctk.CTkLabel(
            drop_inner,
            text="📌 Windows 11 Sabitlenen Klasörler (Hızlı Erişim):",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=c('text_muted')
        ).pack(anchor="w", pady=(0, 6))

        chips_row = ctk.CTkFrame(drop_inner, fg_color="transparent")
        chips_row.pack(fill="x")

        pinned_nav = [
            ("🖥️ Masaüstü", 'qf_desktop'),
            ("📥 İndirilenler", 'qf_downloads'),
            ("📑 Belgeler", 'qf_documents'),
            ("🖼️ Resimler", 'qf_pictures'),
            ("🎵 Müzikler", 'qf_music'),
            ("🎬 Videolar", 'qf_videos'),
        ]
        for label_txt, nav_id in pinned_nav:
            ctk.CTkButton(
                chips_row,
                text=label_txt,
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color=c('quick_access_bg'),
                hover_color=c('quick_access_hover'),
                text_color=c('text_primary'),
                border_width=1,
                border_color=c('border'),
                height=30,
                width=92,
                corner_radius=8,
                command=lambda nid=nav_id: self.app.navigate_to(nid)
            ).pack(side="left", padx=(0, 5), pady=2)

        # Sağ: Canlı Dosya Kategorileri Dağılım Matrisi (File Categories)
        cat_card = ctk.CTkFrame(
            mid_frame,
            fg_color=c('bg_card'),
            corner_radius=14,
            border_width=1,
            border_color=c('border')
        )
        cat_card.grid(row=0, column=1, sticky="nsew", padx=(7, 0))
        FluidAnimator.bind_card_hover(cat_card, self.theme_mode)

        cat_inner = ctk.CTkFrame(cat_card, fg_color="transparent")
        cat_inner.pack(fill="both", expand=True, padx=18, pady=16)

        cat_hdr = ctk.CTkFrame(cat_inner, fg_color="transparent")
        cat_hdr.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(
            cat_hdr,
            text="🏷️ Kategori Dağılımı (Folders)",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=c('text_primary')
        ).pack(side="left")

        ctk.CTkButton(
            cat_hdr,
            text="Tümünü Aç →",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="transparent",
            hover_color=c('bg_card_hover'),
            text_color=c('accent_light'),
            width=85,
            height=26,
            corner_radius=6,
            command=lambda: self.app.navigate_to('files')
        ).pack(side="right")

        self.categories_box = ctk.CTkFrame(cat_inner, fg_color="transparent")
        self.categories_box.pack(fill="both", expand=True)

        if cached_storage:
            self._rendered_storage_id = id(cached_storage)
            self._populate_categories_matrix(cached_storage.get('categories', []))
        else:
            FluidAnimator.create_skeleton(self.categories_box, rows=3, row_height=42, theme_mode=self.theme_mode)

        # =========================================================================
        # 4. ALT SATIR: SON AKTİVİTE AKIŞI & HIZLI ZEKÂ ARAÇLARI
        # =========================================================================
        bot_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        bot_frame.pack(fill="x", pady=(0, 8))
        bot_frame.grid_columnconfigure(0, weight=12)
        bot_frame.grid_columnconfigure(1, weight=8)

        # Sol: Son Düzenlenen Dosyalar Akışı
        recent_card = ctk.CTkFrame(
            bot_frame,
            fg_color=c('bg_card'),
            corner_radius=14,
            border_width=1,
            border_color=c('border')
        )
        recent_card.grid(row=0, column=0, sticky="nsew", padx=(0, 7))
        FluidAnimator.bind_card_hover(recent_card, self.theme_mode)

        r_header = ctk.CTkFrame(recent_card, fg_color="transparent")
        r_header.pack(fill="x", padx=18, pady=(14, 8))

        ctk.CTkLabel(
            r_header,
            text="🕒 Son Organizasyon Hareketleri (Canlı Akış)",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=c('text_primary')
        ).pack(side="left")

        ctk.CTkButton(
            r_header,
            text="Geçmiş →",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="transparent",
            hover_color=c('bg_card_hover'),
            text_color=c('accent_light'),
            width=75,
            height=26,
            command=lambda: self.app.navigate_to('activity')
        ).pack(side="right")

        self.recent_container = ctk.CTkFrame(recent_card, fg_color="transparent")
        self.recent_container.pack(fill="x", padx=16, pady=(0, 14))
        self._populate_recent_list(c)
        self._rendered_ledger_rev = SecurityBackupEngine.get_revision()

        # Sağ: Hızlı Zekâ ve Yönetim Aksiyonları
        quick_card = ctk.CTkFrame(
            bot_frame,
            fg_color=c('bg_card'),
            corner_radius=14,
            border_width=1,
            border_color=c('border')
        )
        quick_card.grid(row=0, column=1, sticky="nsew", padx=(7, 0))
        FluidAnimator.bind_card_hover(quick_card, self.theme_mode)

        q_inner = ctk.CTkFrame(quick_card, fg_color="transparent")
        q_inner.pack(fill="both", expand=True, padx=18, pady=14)

        ctk.CTkLabel(
            q_inner,
            text="🚀 Hızlı Zekâ Stüdyosu",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=c('text_primary')
        ).pack(anchor="w", pady=(0, 10))

        self._create_quick_btn(q_inner, "🧠  AI Dosya İçerik Analizörü", "Derin metadata & etiket incelemesi", lambda: self.app.navigate_to('ai'), c)
        self._create_quick_btn(q_inner, "🔍  Akıllı Anlamsal Arama", "İçerik, kategori ve boyut filtreleri", lambda: self.app.navigate_to('search'), c)
        self._create_quick_btn(q_inner, "📑  SHA-256 Kopya Temizleyici", "Mükerrer dosyaları tespit edin", lambda: self.app.navigate_to('duplicates'), c)
        self._create_quick_btn(q_inner, "↩️  1-Tıkla Geri Alma (Undo)", "Son dosya hareketlerini geri döndürün", lambda: self.app.navigate_to('security'), c)
        self._create_quick_btn(q_inner, "⌘  Komut Paleti (Ctrl+K)", "Tüm komutlara klavyeden erişin", lambda: CommandPalette.toggle(self.app), c)

        if not cached_storage and not self._is_loading_stats:
            self._is_loading_stats = True
            threading.Thread(target=self._async_load_stats, args=(target_base,), daemon=True).start()

    def _async_load_stats(self, target_base):
        try:
            data = StorageAnalyzer.analyze_folder(target_base)
            UIBridge.post(lambda: self._apply_storage_stats(data))
        except Exception:
            pass
        finally:
            self._is_loading_stats = False

    def _apply_storage_stats(self, data):
        try:
            if id(data) == self._rendered_storage_id:
                return
            self._rendered_storage_id = id(data)
            new_files = data.get('total_files', 0)
            new_cats = len(data.get('categories', []))
            if hasattr(self, 'lbl_total_files') and self.lbl_total_files.winfo_exists():
                FluidAnimator.animate_counter(
                    self.lbl_total_files,
                    self._prev_files,
                    new_files,
                    duration_ms=FluidAnimator.TIMING_COMPLEX
                )
                self._prev_files = new_files
            if hasattr(self, 'lbl_total_files_sub') and self.lbl_total_files_sub.winfo_exists():
                self.lbl_total_files_sub.configure(text=f"{new_cats} aktif kategori içinde")
            if hasattr(self, 'lbl_total_size') and self.lbl_total_size.winfo_exists():
                self.lbl_total_size.configure(text=data.get('total_size_human', '0 B'))
            if hasattr(self, 'categories_box') and self.categories_box.winfo_exists():
                self._populate_categories_matrix(data.get('categories', []))
        except Exception:
            pass

    def _populate_categories_matrix(self, categories):
        c = lambda token: FluentTheme.c(token, self.theme_mode)
        for w in self.categories_box.winfo_children():
            w.destroy()

        if not categories:
            ctk.CTkLabel(
                self.categories_box,
                text="Henüz kategori verisi bulunmuyor.",
                font=ctk.CTkFont(size=12),
                text_color=c('text_muted')
            ).pack(pady=24)
            return

        palette_accents = [c('accent'), c('accent_violet'), c('success'), c('warning'), c('accent_light')]
        for idx, cat in enumerate(categories[:5]):
            row = ctk.CTkFrame(self.categories_box, fg_color="transparent")
            row.pack(fill="x", pady=4)

            top_r = ctk.CTkFrame(row, fg_color="transparent")
            top_r.pack(fill="x")

            ctk.CTkLabel(
                top_r,
                text=f"📁 {cat['name']}",
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=c('text_primary')
            ).pack(side="left")

            ctk.CTkLabel(
                top_r,
                text=f"{cat['count']:,} dosya  •  {cat['size_human']} (%{cat['percentage']})".replace(',', '.'),
                font=ctk.CTkFont(size=10),
                text_color=c('text_secondary')
            ).pack(side="right")

            pbar = ctk.CTkProgressBar(row, height=6, corner_radius=3, fg_color=c('bg_card_secondary'))
            pbar.pack(fill="x", pady=(3, 0))
            pbar.set(0.0)
            pbar.configure(progress_color=palette_accents[idx % len(palette_accents)])
            ratio = max(0.03, min(1.0, float(cat.get('percentage', 0)) / 100.0))
            FluidAnimator.animate_progress(pbar, ratio, duration_ms=FluidAnimator.TIMING_COMPLEX, start_val=0.0)

    def _create_glass_stat_card(self, parent, col, icon, orb_color, title, value, subtitle, c):
        card = ctk.CTkFrame(
            parent,
            fg_color=c('bg_card'),
            corner_radius=14,
            border_width=1,
            border_color=c('border')
        )
        card.grid(row=0, column=col, sticky="nsew", padx=5)
        FluidAnimator.bind_card_hover(card, self.theme_mode)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=16, pady=14)

        top = ctk.CTkFrame(inner, fg_color="transparent")
        top.pack(fill="x")

        orb = GlassArtEngine.get_glass_orb(36, orb_color, self.theme_mode)
        ctk.CTkLabel(
            top,
            text=icon,
            image=orb,
            compound="center",
            font=ctk.CTkFont(size=16),
            width=36,
            height=36
        ).pack(side="left")

        ctk.CTkLabel(
            top,
            text=title,
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=c('text_secondary')
        ).pack(side="left", padx=10)

        val_lbl = ctk.CTkLabel(
            inner,
            text=value,
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=24, weight="bold"),
            text_color=c('text_primary')
        )
        val_lbl.pack(anchor="w", pady=(8, 2))

        sub_lbl = ctk.CTkLabel(
            inner,
            text=subtitle,
            font=ctk.CTkFont(size=11),
            text_color=c('text_muted')
        )
        sub_lbl.pack(anchor="w")
        return val_lbl, sub_lbl

    def _create_quick_btn(self, parent, title, subtitle, cmd, c):
        card = ctk.CTkFrame(
            parent,
            fg_color=c('bg_card_secondary'),
            corner_radius=10,
            border_width=1,
            border_color=c('border_subtle')
        )
        card.pack(fill="x", pady=3)
        FluidAnimator.bind_card_hover(
            card,
            self.theme_mode,
            normal_bg_token='bg_card_secondary',
            hover_bg_token='bg_card_hover',
            normal_border_token='border_subtle',
            hover_border_token='border_hover'
        )

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=12, pady=7)

        left = ctk.CTkFrame(inner, fg_color="transparent")
        left.pack(side="left", fill="x", expand=True)

        lbl1 = ctk.CTkLabel(left, text=title, font=ctk.CTkFont(size=12, weight="bold"), text_color=c('text_primary'), anchor="w")
        lbl1.pack(anchor="w")

        lbl2 = ctk.CTkLabel(left, text=subtitle, font=ctk.CTkFont(size=10), text_color=c('text_muted'), anchor="w")
        lbl2.pack(anchor="w")

        arrow = ctk.CTkLabel(inner, text="›", font=ctk.CTkFont(size=18, weight="bold"), text_color=c('accent_light'))
        arrow.pack(side="right", padx=4)

        for w in (card, inner, left, lbl1, lbl2, arrow):
            w.bind("<Button-1>", lambda _e, fn=cmd: fn())

    def _populate_recent_list(self, c):
        for w in self.recent_container.winfo_children():
            w.destroy()

        logs = SecurityBackupEngine.get_history(limit=6, active_only=True)
        if not logs:
            ctk.CTkLabel(
                self.recent_container,
                text="✨ Henüz kaydedilmiş bir dosya organizasyon işlemi bulunmuyor.\nYeni dosyalar geldiğinde canlı olarak burada listelenir.",
                font=ctk.CTkFont(size=12),
                text_color=c('text_muted'),
                justify="center"
            ).pack(pady=24)
            return

        for entry in logs:
            fname = entry.get('file_name', 'Bilinmeyen')
            badge_txt, _, badge_fg, badge_bg = FluentTheme.file_badge_style(fname, self.theme_mode)

            row = ctk.CTkFrame(
                self.recent_container,
                fg_color=c('bg_card_secondary'),
                corner_radius=9,
                border_width=1,
                border_color=c('border_subtle'),
                height=38
            )
            row.pack(fill="x", pady=3)
            row.pack_propagate(False)
            FluidAnimator.bind_card_hover(
                row,
                self.theme_mode,
                normal_bg_token='bg_card_secondary',
                hover_bg_token='bg_card_hover',
                normal_border_token='border_subtle',
                hover_border_token='border_hover'
            )

            ctk.CTkLabel(
                row,
                text=badge_txt,
                font=ctk.CTkFont(size=9, weight="bold"),
                text_color=badge_fg,
                fg_color=badge_bg,
                corner_radius=5,
                width=40,
                padx=4,
                pady=2
            ).pack(side="left", padx=(10, 8), pady=7)

            ctk.CTkLabel(
                row,
                text=fname[:32] + ("..." if len(fname) > 32 else ""),
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=c('text_primary')
            ).pack(side="left", pady=7)

            ctk.CTkLabel(
                row,
                text=f"➔  {entry.get('category', '')}",
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=c('accent_light')
            ).pack(side="left", padx=10)

            ctk.CTkLabel(
                row,
                text=str(entry.get('timestamp', ''))[-8:],
                font=ctk.CTkFont(size=10),
                text_color=c('text_muted')
            ).pack(side="right", padx=12)

            if entry.get('target_path'):
                FluentContextMenu.bind_to_widget(
                    row,
                    entry['target_path'],
                    self.app,
                    on_refresh=lambda: self._populate_recent_list(c),
                    normal_bg_token='bg_card_secondary',
                    normal_border_token='border_subtle'
                )
