"""
Windows 11 Fluent Command Palette (Ctrl + K) (V2.1)
Provides instant keyboard-first navigation to all pages, pinned folders,
and real application actions with smooth entrance transitions and live search.
"""

import customtkinter as ctk
from theme import FluentTheme
from animation import FluidAnimator
from security_backup import SecurityBackupEngine
from config import save_config, refresh_desktop_baseline


class CommandPalette:
    _active_overlay = None
    _selected_index = 0
    _filtered_commands = []
    _row_widgets = []

    @classmethod
    def get_all_commands(cls, app_controller):
        """Uygulamadaki tüm gerçek sayfa ve aksiyon komutlarını döndürür."""
        return [
            # Hızlı Aksiyonlar
            {
                'id': 'act_scan_now',
                'title': '⚡ Şimdi Tara ve Organize Et',
                'subtitle': 'İzlenen tüm klasörleri anında tarar ve yeni dosyaları düzenler',
                'category': 'Aksiyon',
                'keywords': 'tara scan organize düzenle şimdi çalıştır',
                'action': lambda: app_controller.trigger_manual_scan()
            },
            {
                'id': 'act_undo_last',
                'title': '↩️ Son Dosya İşlemini Geri Al (Undo)',
                'subtitle': 'Taşınan en son dosyayı eski konumuna geri döndürür',
                'category': 'Aksiyon',
                'keywords': 'geri al undo iptal kurtar',
                'action': lambda: cls._exec_undo(app_controller)
            },
            {
                'id': 'act_open_folders',
                'title': '📂 Hedef Folders Klasörünü Aç',
                'subtitle': 'Masaüstündeki ana Folders dizinini Windows Gezgininde açar',
                'category': 'Aksiyon',
                'keywords': 'klasör aç explorer folders hedef',
                'action': lambda: app_controller.open_target_folder()
            },
            {
                'id': 'act_toggle_theme',
                'title': '🌓 Görünüm Temasını Değiştir (Gece Camı / Kristal Açık)',
                'subtitle': 'Midnight Glass ve Crystal Light tema modları arasında geçiş yapar',
                'category': 'Aksiyon',
                'keywords': 'tema renk karanlık aydınlık dark light mode glass',
                'action': lambda: app_controller.toggle_theme_quick()
            },
            {
                'id': 'act_cycle_glass',
                'title': '💎 Pencere Cam Şeffaflığını Değiştir (%95 / %88 / %100)',
                'subtitle': 'Windows 11 DWM Acrylic pencere geçirgenlik oranını değiştirir',
                'category': 'Aksiyon',
                'keywords': 'cam glass şeffaflık acrylic mica saydamlık opacity',
                'action': lambda: app_controller.cycle_glass_opacity() if hasattr(app_controller, 'cycle_glass_opacity') else None
            },
            {
                'id': 'act_toggle_watch',
                'title': '⏯️ Otomatik Arka Plan İzlemeyi Aç / Kapat',
                'subtitle': 'Gerçek zamanlı klasör izleme motorunu başlatır veya duraklatır',
                'category': 'Aksiyon',
                'keywords': 'izleme otomatik duraklat başlat watcher',
                'action': lambda: cls._exec_toggle_watch(app_controller)
            },
            {
                'id': 'act_refresh_baseline',
                'title': '🛡️ Masaüstü Koruma Listesini Güncelle',
                'subtitle': 'Mevcut masaüstü öğelerini güvenli koruma listesine kaydeder',
                'category': 'Aksiyon',
                'keywords': 'masaüstü koruma kilit baseline güvenlik',
                'action': lambda: cls._exec_refresh_baseline(app_controller)
            },
            # Sayfalar
            {
                'id': 'nav_home',
                'title': '🏠 Genel Bakış (Dashboard)',
                'subtitle': 'Canlı istatistikler, hızlı sürükle-bırak alanı ve son hareketler',
                'category': 'Sayfa',
                'keywords': 'home ana sayfa genel bakış dashboard özet',
                'action': lambda: app_controller.navigate_to('home')
            },
            {
                'id': 'nav_files',
                'title': '📁 Folders Gezgini (Dosyalarım)',
                'subtitle': 'Kategorize edilmiş klasör yapısını ve dosya dağılımını inceleyin',
                'category': 'Sayfa',
                'keywords': 'dosyalarım folders gezgin kategoriler',
                'action': lambda: app_controller.navigate_to('files')
            },
            {
                'id': 'nav_media',
                'title': '🎬 Medya & Video Galerisi',
                'subtitle': 'Görsel ve videoları küçük resim (thumbnail) önizlemeleriyle görüntüleyin',
                'category': 'Sayfa',
                'keywords': 'medya video resim fotoğraf galeri önizleme',
                'action': lambda: app_controller.navigate_to('media')
            },
            {
                'id': 'nav_ai',
                'title': '🧠 AI Dosya Zekâsı (Intelligence Center)',
                'subtitle': 'Dosya içeriği, metadata ve anlamsal etiket analizi yapın',
                'category': 'Sayfa',
                'keywords': 'ai yapay zeka analiz içerik metadata etiket',
                'action': lambda: app_controller.navigate_to('ai')
            },
            {
                'id': 'nav_search',
                'title': '🔍 Akıllı Anlamsal Arama (Semantic Search)',
                'subtitle': 'Dosya adı, etiket, kategori ve içerik bazlı gelişmiş arama',
                'category': 'Sayfa',
                'keywords': 'ara search bul filtrele semantik',
                'action': lambda: app_controller.navigate_to('search')
            },
            {
                'id': 'nav_smart_org',
                'title': '✨ Hızlı Düzenle (Smart Organization)',
                'subtitle': 'Herhangi bir klasörü tek tıkla analiz edin ve düzenleyin',
                'category': 'Sayfa',
                'keywords': 'hızlı düzenle smart organization klasör topla',
                'action': lambda: app_controller.navigate_to('smart_org')
            },
            {
                'id': 'nav_duplicates',
                'title': '📑 Kopya Dosya Yöneticisi (Duplicate Manager)',
                'subtitle': 'SHA-256 doğrulukla mükerrer kopyaları bulun ve yer açın',
                'category': 'Sayfa',
                'keywords': 'kopya mükerrer duplicate aynı dosya sil',
                'action': lambda: app_controller.navigate_to('duplicates')
            },
            {
                'id': 'nav_storage',
                'title': '📊 Depolama Analizi (Storage Analyzer)',
                'subtitle': 'Kategori boyutlarını ve en büyük dosyaları inceleyin',
                'category': 'Sayfa',
                'keywords': 'depolama disk boyut alan analiz büyük dosya',
                'action': lambda: app_controller.navigate_to('storage')
            },
            {
                'id': 'nav_automation',
                'title': '⚡ Otomasyon ve İzleme Ayarları',
                'subtitle': 'İzlenen klasörleri ve tarama sıklığını yapılandırın',
                'category': 'Sayfa',
                'keywords': 'otomasyon izlenen klasörler sıklık',
                'action': lambda: app_controller.navigate_to('automation')
            },
            {
                'id': 'nav_activity',
                'title': '🕒 Aktivite Merkezi (Activity Center)',
                'subtitle': 'Gerçekleşen tüm dosya organizasyon işlemlerinin geçmişi',
                'category': 'Sayfa',
                'keywords': 'aktivite geçmiş log kayıtlar hareketler',
                'action': lambda: app_controller.navigate_to('activity')
            },
            {
                'id': 'nav_security',
                'title': '🛡️ Güvenlik ve Yedekleme (Undo Defteri)',
                'subtitle': 'Dosya işlemlerini tek tek geri alın ve güvenlik durumunu görün',
                'category': 'Sayfa',
                'keywords': 'güvenlik yedekleme geri al undo koruma',
                'action': lambda: app_controller.navigate_to('security')
            },
            {
                'id': 'nav_settings',
                'title': '⚙️ Uygulama Ayarları & Erişilebilirlik',
                'subtitle': 'Tema, animasyon düzeyi, başlangıç ve sistem tercihleri',
                'category': 'Sayfa',
                'keywords': 'ayarlar settings animasyon erişilebilirlik tema',
                'action': lambda: app_controller.navigate_to('settings')
            },
            # Sabitlenen Klasörler
            {
                'id': 'pin_desktop',
                'title': '📌 Masaüstü Klasörü Görünümü',
                'subtitle': 'Masaüstündeki yeni ve korunan öğeleri inceleyin',
                'category': 'Sabitlenen Klasör',
                'keywords': 'masaüstü desktop sabitlenen',
                'action': lambda: app_controller.navigate_to('qf_desktop')
            },
            {
                'id': 'pin_downloads',
                'title': '📌 İndirilenler Klasörü Görünümü',
                'subtitle': 'İndirilenler klasörünü inceleyin ve organize edin',
                'category': 'Sabitlenen Klasör',
                'keywords': 'indirilenler downloads sabitlenen',
                'action': lambda: app_controller.navigate_to('qf_downloads')
            },
            {
                'id': 'pin_documents',
                'title': '📌 Belgeler Klasörü Görünümü',
                'subtitle': 'Belgeler klasörünü inceleyin ve organize edin',
                'category': 'Sabitlenen Klasör',
                'keywords': 'belgeler documents sabitlenen',
                'action': lambda: app_controller.navigate_to('qf_documents')
            },
            {
                'id': 'pin_pictures',
                'title': '📌 Resimler Klasörü Görünümü',
                'subtitle': 'Resimler klasörünü inceleyin ve organize edin',
                'category': 'Sabitlenen Klasör',
                'keywords': 'resimler pictures fotoğraflar sabitlenen',
                'action': lambda: app_controller.navigate_to('qf_pictures')
            },
            {
                'id': 'pin_music',
                'title': '📌 Müzikler Klasörü Görünümü',
                'subtitle': 'Müzikler klasörünü inceleyin ve organize edin',
                'category': 'Sabitlenen Klasör',
                'keywords': 'müzikler music ses sabitlenen',
                'action': lambda: app_controller.navigate_to('qf_music')
            },
            {
                'id': 'pin_videos',
                'title': '📌 Videolar Klasörü Görünümü',
                'subtitle': 'Videolar klasörünü inceleyin ve organize edin',
                'category': 'Sabitlenen Klasör',
                'keywords': 'videolar videos film sabitlenen',
                'action': lambda: app_controller.navigate_to('qf_videos')
            },
        ]

    @classmethod
    def filter_commands(cls, app_controller, query: str):
        all_cmds = cls.get_all_commands(app_controller)
        q = (query or "").strip().lower()
        if not q:
            return all_cmds
        scored = []
        for cmd in all_cmds:
            haystack = f"{cmd['title']} {cmd['subtitle']} {cmd['category']} {cmd['keywords']}".lower()
            if q in cmd['title'].lower():
                scored.append((2, cmd))
            elif q in haystack:
                scored.append((1, cmd))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored]

    @classmethod
    def is_open(cls) -> bool:
        if cls._active_overlay is not None:
            try:
                return bool(cls._active_overlay.winfo_exists())
            except Exception:
                return False
        return False

    @classmethod
    def close(cls):
        if cls._active_overlay is not None:
            try:
                if cls._active_overlay.winfo_exists():
                    cls._active_overlay.destroy()
            except Exception:
                pass
            cls._active_overlay = None
        cls._row_widgets.clear()

    @classmethod
    def toggle(cls, app_controller):
        if cls.is_open():
            cls.close()
        else:
            cls.open(app_controller)

    @classmethod
    def open(cls, app_controller, initial_query: str = ""):
        cls.close()
        theme_mode = getattr(app_controller, 'theme_mode', 'dark')
        c = lambda token: FluentTheme.c(token, theme_mode)

        card = ctk.CTkFrame(
            app_controller,
            fg_color=c('bg_elevated'),
            corner_radius=12,
            border_width=1,
            border_color=c('border_focus'),
            width=600,
            height=430
        )
        card.pack_propagate(False)
        cls._active_overlay = card
        cls._selected_index = 0

        # Üst Arama Satırı
        top_bar = ctk.CTkFrame(card, fg_color="transparent")
        top_bar.pack(fill="x", padx=14, pady=(12, 8))

        ctk.CTkLabel(
            top_bar,
            text="🔎",
            font=ctk.CTkFont(size=16),
            text_color=c('accent_light')
        ).pack(side="left", padx=(4, 8))

        search_entry = ctk.CTkEntry(
            top_bar,
            placeholder_text="Komut çalıştır veya sayfaya git... (Örn: Şimdi Tara, Kopya, Masaüstü, Geri Al)",
            font=ctk.CTkFont(size=13),
            fg_color=c('bg_input'),
            border_color=c('border'),
            text_color=c('text_primary'),
            height=36,
            corner_radius=8
        )
        search_entry.pack(side="left", fill="x", expand=True)
        FluidAnimator.bind_input_focus(search_entry, theme_mode)

        esc_badge = ctk.CTkButton(
            top_bar,
            text="ESC",
            width=42,
            height=26,
            corner_radius=6,
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color=c('bg_card'),
            hover_color=c('bg_card_hover'),
            text_color=c('text_muted'),
            command=cls.close
        )
        esc_badge.pack(side="right", padx=(8, 0))

        ctk.CTkFrame(card, fg_color=c('border_subtle'), height=1).pack(fill="x", padx=12)

        # Sonuç Listesi
        scroll = ctk.CTkScrollableFrame(card, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=6)

        # Alt Bilgi Çubuğu
        footer = ctk.CTkFrame(card, fg_color=c('bg_secondary'), height=28, corner_radius=0)
        footer.pack(fill="x", side="bottom")
        ctk.CTkLabel(
            footer,
            text="↑↓ Gezin   •   Enter Çalıştır   •   Esc Kapat   •   Ctrl+K Hızlı Komut Paleti",
            font=ctk.CTkFont(size=11),
            text_color=c('text_muted')
        ).pack(pady=4)

        def _render_list(query_text=""):
            for w in scroll.winfo_children():
                w.destroy()
            cls._row_widgets.clear()

            cls._filtered_commands = cls.filter_commands(app_controller, query_text)
            cls._selected_index = 0

            if not cls._filtered_commands:
                ctk.CTkLabel(
                    scroll,
                    text="Eşleşen bir sayfa veya komut bulunamadı.",
                    font=ctk.CTkFont(size=12),
                    text_color=c('text_muted')
                ).pack(pady=40)
                return

            for idx, cmd in enumerate(cls._filtered_commands):
                is_sel = (idx == cls._selected_index)
                row = ctk.CTkFrame(
                    scroll,
                    fg_color=c('accent_subtle') if is_sel else c('bg_card'),
                    corner_radius=8,
                    border_width=1,
                    border_color=c('border_focus') if is_sel else c('border_subtle')
                )
                row.pack(fill="x", pady=2)
                cls._row_widgets.append(row)

                inner = ctk.CTkFrame(row, fg_color="transparent")
                inner.pack(fill="x", padx=12, pady=7)

                left = ctk.CTkFrame(inner, fg_color="transparent")
                left.pack(side="left", fill="x", expand=True)

                lbl_t = ctk.CTkLabel(
                    left,
                    text=cmd['title'],
                    font=ctk.CTkFont(size=12, weight="bold"),
                    text_color=c('text_primary'),
                    anchor="w"
                )
                lbl_t.pack(anchor="w")

                lbl_sub = ctk.CTkLabel(
                    left,
                    text=cmd['subtitle'],
                    font=ctk.CTkFont(size=10),
                    text_color=c('text_secondary'),
                    anchor="w"
                )
                lbl_sub.pack(anchor="w")

                badge = ctk.CTkLabel(
                    inner,
                    text=cmd['category'],
                    font=ctk.CTkFont(size=10, weight="bold"),
                    text_color=c('accent_light'),
                    fg_color=c('bg_secondary'),
                    corner_radius=6,
                    padx=8,
                    pady=2
                )
                badge.pack(side="right")

                def _make_click(command_obj):
                    return lambda _e=None: cls._execute_command(command_obj)

                for w_target in (row, inner, left, lbl_t, lbl_sub, badge):
                    w_target.bind("<Button-1>", _make_click(cmd))

        def _update_selection_visuals():
            for idx, row in enumerate(cls._row_widgets):
                if not row.winfo_exists():
                    continue
                is_sel = (idx == cls._selected_index)
                row.configure(
                    fg_color=c('accent_subtle') if is_sel else c('bg_card'),
                    border_color=c('border_focus') if is_sel else c('border_subtle')
                )

        def _on_key_down(_e=None):
            if not cls._filtered_commands:
                return "break"
            cls._selected_index = (cls._selected_index + 1) % len(cls._filtered_commands)
            _update_selection_visuals()
            return "break"

        def _on_key_up(_e=None):
            if not cls._filtered_commands:
                return "break"
            cls._selected_index = (cls._selected_index - 1) % len(cls._filtered_commands)
            _update_selection_visuals()
            return "break"

        def _on_enter(_e=None):
            if cls._filtered_commands and 0 <= cls._selected_index < len(cls._filtered_commands):
                cls._execute_command(cls._filtered_commands[cls._selected_index])
            return "break"

        search_entry.bind("<KeyRelease>", lambda e: _render_list(search_entry.get()) if e.keysym not in ('Up', 'Down', 'Return', 'Escape') else None)
        search_entry.bind("<Down>", _on_key_down)
        search_entry.bind("<Up>", _on_key_up)
        search_entry.bind("<Return>", _on_enter)
        search_entry.bind("<Escape>", lambda _e: cls.close())

        if initial_query:
            search_entry.insert(0, initial_query)
        _render_list(initial_query)

        card.place(relx=0.5, rely=0.09, anchor="n")
        card.lift()
        FluidAnimator.fade_in_surface(
            card,
            c('bg_secondary'),
            c('bg_elevated'),
            duration_ms=FluidAnimator.TIMING_MODAL
        )
        try:
            search_entry.focus_set()
        except Exception:
            pass

    @classmethod
    def _execute_command(cls, cmd_obj):
        cls.close()
        action = cmd_obj.get('action')
        if callable(action):
            action()

    @staticmethod
    def _exec_undo(app_controller):
        res = SecurityBackupEngine.undo_last()
        lvl = 'success' if res.get('success') else 'warning'
        FluidAnimator.show_toast(
            app_controller,
            "Geri Alma (Undo)",
            res.get('message', ''),
            theme_mode=getattr(app_controller, 'theme_mode', 'dark'),
            level=lvl
        )

    @staticmethod
    def _exec_toggle_watch(app_controller):
        cur = app_controller.cfg.get('auto_watch', True)
        app_controller.cfg['auto_watch'] = not cur
        save_config(app_controller.cfg)
        app_controller.update_status_footer()
        state_str = "Aktif" if app_controller.cfg['auto_watch'] else "Duraklatıldı"
        FluidAnimator.show_toast(
            app_controller,
            f"Otomatik İzleme: {state_str}",
            "Arka plan dosya izleme durumu güncellendi.",
            theme_mode=getattr(app_controller, 'theme_mode', 'dark'),
            level='info'
        )

    @staticmethod
    def _exec_refresh_baseline(app_controller):
        cnt = refresh_desktop_baseline(app_controller.cfg)
        FluidAnimator.show_toast(
            app_controller,
            "Masaüstü Koruması Yenilendi",
            f"Mevcut {cnt} masaüstü öğesi güvenli koruma listesine alındı.",
            theme_mode=getattr(app_controller, 'theme_mode', 'dark'),
            level='success'
        )
