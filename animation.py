"""
Windows 11 Fluent Motion & Centralized Animation Engine (V2.1)
Provides:
- Standardized timing constants (Micro, Hover, Page, Modal, Complex)
- Mathematical easing functions (Ease-Out, Ease-In, Ease-In-Out)
- Accessibility & Reduced Motion support (Full, Reduced, Disabled + Windows SPI_GETCLIENTAREAANIMATION)
- Thread-safe UIBridge queue for Python 3.15 background thread callbacks
- Reusable animations: Color/Surface Fade, Counter Tween, Progress Tween,
  Card Hover Elevation, Input Focus Ring, Skeleton Shimmer, and Smart Toasts.
- Zero geometry jitter: Never shifts button hitboxes during mouse clicks.
"""

import queue
import time
import customtkinter as ctk
from theme import FluentTheme
from config import get_effective_animation_mode


class Easing:
    """Standart Windows 11 Fluent hareket eğrileri (Easing Curves)."""

    @staticmethod
    def linear(t: float) -> float:
        return max(0.0, min(1.0, float(t)))

    @staticmethod
    def ease_out(t: float) -> float:
        """Giriş (Entrance) animasyonları için yumuşak yavaşlayan eğri (Cubic Ease-Out)."""
        t = max(0.0, min(1.0, float(t)))
        return 1.0 - pow(1.0 - t, 3)

    @staticmethod
    def ease_in(t: float) -> float:
        """Çıkış (Exit) animasyonları için hızlanan eğri (Cubic Ease-In)."""
        t = max(0.0, min(1.0, float(t)))
        return t * t * t

    @staticmethod
    def ease_in_out(t: float) -> float:
        """Durum geçişleri (Transition) için simetrik eğri (Cubic Ease-In-Out)."""
        t = max(0.0, min(1.0, float(t)))
        if t < 0.5:
            return 4.0 * t * t * t
        return 1.0 - pow(-2.0 * t + 2.0, 3) / 2.0


class UIBridge:
    """
    Python 3.15+ Tkinter Thread-Safety Köprüsü.
    Arka plan iş parçacıklarından (worker threads) ana UI iş parçacığına güvenli
    geri çağırım (callback) iletimi sağlar.
    """
    _queue = queue.Queue()
    _root = None
    _running = False
    _after_id = None

    @classmethod
    def start(cls, root_widget):
        cls._root = root_widget
        cls._running = True
        cls._poll()

    @classmethod
    def stop(cls):
        cls._running = False
        if cls._root and cls._after_id:
            try:
                cls._root.after_cancel(cls._after_id)
            except Exception:
                pass
        cls._after_id = None

    @classmethod
    def post(cls, callback):
        """Arka plan thread'inden ana UI thread'ine görev gönderir."""
        if callable(callback):
            cls._queue.put(callback)

    @classmethod
    def drain_now(cls):
        """Kuyruktaki tüm bekleyen UI görevlerini anında çalıştırır (Test ve senkron kullanım için)."""
        processed = 0
        while not cls._queue.empty():
            try:
                cb = cls._queue.get_nowait()
                cb()
                processed += 1
            except queue.Empty:
                break
            except Exception:
                pass
        return processed

    @classmethod
    def _poll(cls):
        if not cls._running or not cls._root:
            return
        try:
            if not cls._root.winfo_exists():
                cls._running = False
                return
        except Exception:
            cls._running = False
            return

        cls.drain_now()

        try:
            cls._after_id = cls._root.after(25, cls._poll)
        except Exception:
            pass


class FluidAnimator:
    """
    Merkezi Animasyon Motoru (Centralized Animation Engine).
    Bileşenlerin yaşam döngüsünü takip eder, çakışan animasyonları iptal eder
    ve erişilebilirlik tercihlerine ('full', 'reduced', 'disabled') uyum sağlar.
    """

    # Standart Zamanlama Sabitleri (ms)
    TIMING_MICRO = 150     # 120-180 ms (Mikro etkileşimler)
    TIMING_HOVER = 140     # 120-180 ms (Hover geçişleri)
    TIMING_PAGE = 200      # 180-250 ms (Sayfa geçişleri)
    TIMING_MODAL = 200     # 180-240 ms (Modal / Komut Paleti geçişleri)
    TIMING_COMPLEX = 300   # 250-350 ms (Sayaç ve ilerleme çubuğu geçişleri)

    _mode_override = None  # None ise config'den okur
    _active_jobs = {}      # {(widget_id, prop_key): (widget, after_id)}
    _chunk_jobs = {}       # {container_id: (container, after_id)}
    _active_hover_reset = None
    _active_toasts = []    # Aktif toast bildirim pencereleri
    _last_toast_key = None
    _last_toast_time = 0.0

    @classmethod
    def set_animation_mode(cls, mode: str = None):
        """Animasyon modunu çalışma zamanında günceller ('full', 'reduced', 'disabled' veya None)."""
        cls._mode_override = mode

    @classmethod
    def get_animation_mode(cls, cfg=None) -> str:
        if cls._mode_override in ('full', 'reduced', 'disabled'):
            return cls._mode_override
        return get_effective_animation_mode(cfg)

    @classmethod
    def get_duration(cls, base_ms: int, cfg=None) -> int:
        """Etkin animasyon moduna göre ölçeklenmiş süreyi (ms) döndürür."""
        mode = cls.get_animation_mode(cfg)
        if mode == 'disabled':
            return 0
        if mode == 'reduced':
            return max(40, int(base_ms * 0.45))
        return int(base_ms)

    @classmethod
    def cancel_job(cls, widget, prop_key: str):
        """Belirli bir widget ve özellik üzerindeki devam eden animasyonu iptal eder."""
        key = (id(widget), prop_key)
        entry = cls._active_jobs.pop(key, None)
        if entry:
            w, after_id = entry
            try:
                if w.winfo_exists():
                    w.after_cancel(after_id)
            except Exception:
                pass

    @classmethod
    def cancel_chunk_render(cls, container=None):
        """Devam eden parçalı (chunked) liste çizim görevlerini iptal eder."""
        if container is not None:
            cid = id(container)
            entry = cls._chunk_jobs.pop(cid, None)
            if entry:
                w, aid = entry
                try:
                    if w.winfo_exists():
                        w.after_cancel(aid)
                except Exception:
                    pass
            return

        for cid, (w, aid) in list(cls._chunk_jobs.items()):
            try:
                if w.winfo_exists():
                    w.after_cancel(aid)
            except Exception:
                pass
        cls._chunk_jobs.clear()

    @classmethod
    def render_chunked(
        cls,
        container,
        items: list,
        render_item_fn,
        initial_batch: int = 12,
        chunk_size: int = 12,
        interval_ms: int = 8,
        on_complete=None
    ):
        """
        Büyük listeleri ana UI iş parçacığını (main thread) kilitlemeden çizer.
        İlk görünür dilimi (initial_batch) anında oluşturur, kalan öğeleri ise
        mikro-dilimler (chunk_size) halinde olay döngüsü boşta kaldıkça ekler.
        """
        if not container:
            return
        cls.cancel_chunk_render(container)
        total = len(items)
        if total == 0:
            if callable(on_complete):
                on_complete()
            return

        first_end = min(total, max(1, initial_batch))
        for idx in range(0, first_end):
            try:
                if not container.winfo_exists():
                    return
                render_item_fn(items[idx], idx)
            except Exception:
                pass

        if first_end >= total:
            if callable(on_complete):
                on_complete()
            return

        cid = id(container)

        def _next_chunk(start_idx):
            cls._chunk_jobs.pop(cid, None)
            try:
                if not container.winfo_exists():
                    return
                end_idx = min(total, start_idx + chunk_size)
                for i in range(start_idx, end_idx):
                    render_item_fn(items[i], i)
                if end_idx < total:
                    aid = container.after(interval_ms, lambda: _next_chunk(end_idx))
                    cls._chunk_jobs[cid] = (container, aid)
                elif callable(on_complete):
                    on_complete()
            except Exception:
                pass

        try:
            aid = container.after(interval_ms, lambda: _next_chunk(first_end))
            cls._chunk_jobs[cid] = (container, aid)
        except Exception:
            pass

    @classmethod
    def cancel_all(cls):
        """Tüm aktif animasyon zamanlayıcılarını güvenli şekilde temizler."""
        cls.cancel_chunk_render()
        for key, (w, after_id) in list(cls._active_jobs.items()):
            try:
                if w.winfo_exists():
                    w.after_cancel(after_id)
            except Exception:
                pass
        cls._active_jobs.clear()

    @classmethod
    def animate_color(
        cls,
        widget,
        prop: str,
        start_hex: str,
        end_hex: str,
        duration_ms: int = TIMING_HOVER,
        easing=Easing.ease_in_out,
        on_complete=None
    ):
        """
        Bir CustomTkinter bileşeninin renk özelliğini (fg_color, border_color, text_color)
        başlangıç renginden hedef renge yumuşakça dönüştürür.
        """
        if not widget:
            return
        try:
            if not widget.winfo_exists():
                return
        except Exception:
            return

        cls.cancel_job(widget, prop)
        eff_duration = cls.get_duration(duration_ms)

        if eff_duration <= 0 or start_hex == end_hex:
            try:
                widget.configure(**{prop: end_hex})
                if callable(on_complete):
                    on_complete()
            except Exception:
                pass
            return

        steps = max(4, min(14, eff_duration // 16))
        interval = max(12, eff_duration // steps)
        key = (id(widget), prop)

        def _step(current_step):
            cls._active_jobs.pop(key, None)
            try:
                if not widget.winfo_exists():
                    return
                t = current_step / float(steps)
                eased_t = easing(t)
                cur_hex = FluentTheme.interpolate_color(start_hex, end_hex, eased_t)
                widget.configure(**{prop: cur_hex})
                if current_step < steps:
                    aid = widget.after(interval, lambda: _step(current_step + 1))
                    cls._active_jobs[key] = (widget, aid)
                elif callable(on_complete):
                    on_complete()
            except Exception:
                pass

        _step(1)

    @classmethod
    def animate_Entrance(cls, widget, start_pady=10, end_pady=0, steps=6, delay=14):
        """
        Geriye dönük uyumluluk ve güvenli sayfa giriş efekti.
        Tıklama koordinatlarını (hitbox) kaydırmamak için geometriyi sabit tutar.
        """
        try:
            if widget and widget.winfo_exists():
                widget.pack_configure(pady=end_pady)
        except Exception:
            pass

    @classmethod
    def fade_in_surface(cls, widget, base_bg: str, target_bg: str, duration_ms: int = TIMING_PAGE):
        """
        Bir kart veya yüzeyin arka plan rengini taban renkten hedef renge
        yumuşakça (Ease-Out) aydınlatarak/belirginleştirerek görünür kılar.
        Geometriyi değiştirmediği için tıklama kayması yaratmaz.
        """
        cls.animate_color(
            widget,
            'fg_color',
            base_bg,
            target_bg,
            duration_ms=duration_ms,
            easing=Easing.ease_out
        )

    @classmethod
    def animate_counter(
        cls,
        label_widget,
        start_val: float,
        end_val: float,
        duration_ms: int = TIMING_COMPLEX,
        prefix: str = "",
        suffix: str = "",
        formatter=None
    ):
        """
        Dashboard istatistik sayaçlarını başlangıç değerinden hedef değere
        akıcı bir şekilde (Ease-Out) sayarak günceller.
        """
        if not label_widget:
            return
        try:
            if not label_widget.winfo_exists():
                return
        except Exception:
            return

        cls.cancel_job(label_widget, "counter")
        eff_duration = cls.get_duration(duration_ms)

        def _format(val):
            if callable(formatter):
                return formatter(val)
            iv = int(round(val))
            return f"{prefix}{iv:,}{suffix}".replace(',', '.')

        if eff_duration <= 0 or start_val == end_val:
            try:
                label_widget.configure(text=_format(end_val))
            except Exception:
                pass
            return

        steps = max(6, min(18, eff_duration // 16))
        interval = max(14, eff_duration // steps)
        key = (id(label_widget), "counter")

        def _step(current_step):
            cls._active_jobs.pop(key, None)
            try:
                if not label_widget.winfo_exists():
                    return
                t = current_step / float(steps)
                eased_t = Easing.ease_out(t)
                cur_val = start_val + (end_val - start_val) * eased_t
                label_widget.configure(text=_format(cur_val))
                if current_step < steps:
                    aid = label_widget.after(interval, lambda: _step(current_step + 1))
                    cls._active_jobs[key] = (label_widget, aid)
            except Exception:
                pass

        _step(1)

    @classmethod
    def animate_progress(
        cls,
        progress_bar,
        target_val: float,
        duration_ms: int = TIMING_COMPLEX,
        start_val: float = None
    ):
        """
        CTkProgressBar bileşenini mevcut değerinden hedef değere (0.0 - 1.0)
        yumuşak Ease-Out eğrisi ile taşır.
        """
        if not progress_bar:
            return
        try:
            if not progress_bar.winfo_exists():
                return
        except Exception:
            return

        cls.cancel_job(progress_bar, "progress")
        target_val = max(0.0, min(1.0, float(target_val)))
        eff_duration = cls.get_duration(duration_ms)

        if start_val is None:
            try:
                start_val = float(progress_bar.get())
            except Exception:
                start_val = 0.0

        if eff_duration <= 0 or abs(target_val - start_val) < 0.005:
            try:
                progress_bar.set(target_val)
            except Exception:
                pass
            return

        steps = max(6, min(18, eff_duration // 16))
        interval = max(14, eff_duration // steps)
        key = (id(progress_bar), "progress")

        def _step(current_step):
            cls._active_jobs.pop(key, None)
            try:
                if not progress_bar.winfo_exists():
                    return
                t = current_step / float(steps)
                eased_t = Easing.ease_out(t)
                cur_v = start_val + (target_val - start_val) * eased_t
                progress_bar.set(max(0.0, min(1.0, cur_v)))
                if current_step < steps:
                    aid = progress_bar.after(interval, lambda: _step(current_step + 1))
                    cls._active_jobs[key] = (progress_bar, aid)
            except Exception:
                pass

        _step(1)

    @classmethod
    def bind_card_hover(
        cls,
        card_widget,
        theme_mode: str = 'dark',
        normal_bg_token: str = 'bg_card',
        hover_bg_token: str = 'bg_card_hover',
        normal_border_token: str = 'border',
        hover_border_token: str = 'border_hover'
    ):
        """
        Kart bileşenlerine Windows 11 Fluent hover (yüzey aydınlanması ve kenarlık vurgusu)
        mikro-etkileşimini sıfır gecikme ve tekil aktif kart takibi ile bağlar.
        """
        if not card_widget:
            return

        normal_bg = FluentTheme.c(normal_bg_token, theme_mode)
        hover_bg = FluentTheme.c(hover_bg_token, theme_mode)
        normal_border = FluentTheme.c(normal_border_token, theme_mode)
        hover_border = FluentTheme.c(hover_border_token, theme_mode)

        state = {'hovered': False}

        def _force_reset():
            if not state['hovered']:
                return
            state['hovered'] = False
            try:
                if card_widget.winfo_exists():
                    card_widget.configure(fg_color=normal_bg, border_color=normal_border)
            except Exception:
                pass

        def _on_enter(_event=None):
            if state['hovered']:
                return
            if cls._active_hover_reset is not None and cls._active_hover_reset is not _force_reset:
                try:
                    cls._active_hover_reset()
                except Exception:
                    pass
            state['hovered'] = True
            cls._active_hover_reset = _force_reset
            try:
                card_widget.configure(fg_color=hover_bg, border_color=hover_border)
            except Exception:
                pass

        def _on_leave(event=None):
            if not state['hovered']:
                return
            if event is not None:
                try:
                    mx, my = card_widget.winfo_pointerxy()
                    wx = card_widget.winfo_rootx()
                    wy = card_widget.winfo_rooty()
                    ww = card_widget.winfo_width()
                    wh = card_widget.winfo_height()
                    if wx <= mx <= wx + ww and wy <= my <= wy + wh:
                        return
                except Exception:
                    pass
            _force_reset()
            if cls._active_hover_reset is _force_reset:
                cls._active_hover_reset = None

        try:
            card_widget.bind("<Enter>", _on_enter, add="+")
            card_widget.bind("<Leave>", _on_leave, add="+")
        except Exception:
            pass

    @classmethod
    def bind_input_focus(cls, entry_widget, theme_mode: str = 'dark'):
        """Giriş kutularına (CTkEntry) odaklanıldığında yumuşak mavi vurgu kenarlığı uygular."""
        if not entry_widget:
            return
        normal_border = FluentTheme.c('border', theme_mode)
        focus_border = FluentTheme.c('border_focus', theme_mode)

        def _on_focus_in(_e=None):
            cls.animate_color(entry_widget, 'border_color', normal_border, focus_border, duration_ms=cls.TIMING_MICRO)

        def _on_focus_out(_e=None):
            cls.animate_color(entry_widget, 'border_color', focus_border, normal_border, duration_ms=cls.TIMING_MICRO)

        try:
            entry_widget.bind("<FocusIn>", _on_focus_in, add="+")
            entry_widget.bind("<FocusOut>", _on_focus_out, add="+")
        except Exception:
            pass

    @classmethod
    def create_skeleton(cls, parent, rows: int = 3, row_height: int = 54, theme_mode: str = 'dark'):
        """
        Veri yüklenirken gösterilecek şık Windows 11 Fluent İskelet (Skeleton) yer tutucusu oluşturur.
        Azaltılmış/Tam animasyon modunda hafif nefes alma (pulse) efekti uygular.
        """
        base_col = FluentTheme.c('skeleton_base', theme_mode)
        high_col = FluentTheme.c('skeleton_highlight', theme_mode)
        card_col = FluentTheme.c('bg_card', theme_mode)
        border_col = FluentTheme.c('border_subtle', theme_mode)

        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(fill="x", pady=6)

        bars = []
        for _ in range(rows):
            row_card = ctk.CTkFrame(
                container,
                fg_color=card_col,
                corner_radius=10,
                border_width=1,
                border_color=border_col,
                height=row_height
            )
            row_card.pack(fill="x", pady=4)
            row_card.pack_propagate(False)

            inner = ctk.CTkFrame(row_card, fg_color="transparent")
            inner.pack(fill="both", expand=True, padx=14, pady=10)

            b1 = ctk.CTkFrame(inner, fg_color=base_col, width=220, height=12, corner_radius=6)
            b1.pack(anchor="w", pady=(2, 6))
            b2 = ctk.CTkFrame(inner, fg_color=base_col, width=140, height=9, corner_radius=4)
            b2.pack(anchor="w")
            bars.extend([b1, b2])

        if cls.get_animation_mode() != 'disabled':
            state = {'step': 0, 'dir': 1}

            def _pulse():
                try:
                    if not container.winfo_exists():
                        return
                    state['step'] += state['dir']
                    if state['step'] >= 6:
                        state['dir'] = -1
                    elif state['step'] <= 0:
                        state['dir'] = 1
                    t = state['step'] / 6.0
                    col = FluentTheme.interpolate_color(base_col, high_col, t)
                    for b in bars:
                        if b.winfo_exists():
                            b.configure(fg_color=col)
                    container.after(90, _pulse)
                except Exception:
                    pass

            container.after(90, _pulse)

        return container

    @classmethod
    def show_toast(
        cls,
        root_widget,
        title: str,
        message: str,
        theme_mode: str = 'dark',
        duration_ms: int = 3200,
        level: str = 'info'
    ):
        """
        Sağ alt köşede beliren Windows 11 Fluent Toast bildirimi.
        - Seviyeler: 'info', 'success', 'warning', 'error'
        - Mükerrer bildirim engelleme (Deduplication)
        - Bildirim Merkezi (NotificationCenter) geçmişine otomatik kayıt
        """
        # Bildirim Merkezine kaydet
        try:
            from notification_center import NotificationCenter
            NotificationCenter.add(title=title, message=message, level=level)
            if hasattr(root_widget, 'update_notification_badge'):
                root_widget.update_notification_badge()
        except Exception:
            pass

        if not root_widget:
            return
        try:
            if not root_widget.winfo_exists():
                return
        except Exception:
            return

        # Deduplication: 1.5 saniye içinde birebir aynı bildirim geldiyse tekrar açma
        now = time.time()
        dedup_key = f"{level}:{title}:{message}"
        if cls._last_toast_key == dedup_key and (now - cls._last_toast_time) < 1.5:
            return
        cls._last_toast_key = dedup_key
        cls._last_toast_time = now

        c = lambda token: FluentTheme.c(token, theme_mode)

        level_map = {
            'success': ('✅', c('success')),
            'warning': ('⚠️', c('warning')),
            'error': ('❌', c('danger')),
            'info': ('✨', c('accent_light'))
        }
        icon_char, accent_col = level_map.get(level, level_map['info'])

        # Mevcut aktif toastları temizle (üst üste binmeyi önle)
        for old_t in list(cls._active_toasts):
            try:
                if old_t.winfo_exists():
                    old_t.destroy()
            except Exception:
                pass
        cls._active_toasts.clear()

        toast = ctk.CTkFrame(
            root_widget,
            fg_color=c('bg_elevated'),
            corner_radius=10,
            border_width=1,
            border_color=accent_col,
            width=340,
            height=74
        )
        cls._active_toasts.append(toast)

        # Sol vurgu şeridi
        stripe = ctk.CTkFrame(toast, fg_color=accent_col, width=4, corner_radius=2)
        stripe.pack(side="left", fill="y", padx=(6, 0), pady=8)

        inner = ctk.CTkFrame(toast, fg_color="transparent")
        inner.pack(side="left", fill="both", expand=True, padx=12, pady=10)

        top_row = ctk.CTkFrame(inner, fg_color="transparent")
        top_row.pack(fill="x")

        ctk.CTkLabel(
            top_row,
            text=f"{icon_char}  {title}",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=accent_col
        ).pack(side="left", anchor="w")

        close_btn = ctk.CTkButton(
            top_row,
            text="✕",
            width=20,
            height=20,
            corner_radius=4,
            fg_color="transparent",
            hover_color=c('bg_card_hover'),
            text_color=c('text_muted'),
            font=ctk.CTkFont(size=11),
            command=lambda: _dismiss()
        )
        close_btn.pack(side="right")

        ctk.CTkLabel(
            inner,
            text=message[:65] + ("..." if len(message) > 65 else ""),
            font=ctk.CTkFont(size=11),
            text_color=c('text_primary')
        ).pack(anchor="w", pady=(2, 0))

        eff_dur = cls.get_duration(cls.TIMING_MODAL)

        def _dismiss():
            if toast in cls._active_toasts:
                cls._active_toasts.remove(toast)
            try:
                if toast.winfo_exists():
                    toast.destroy()
            except Exception:
                pass

        if eff_dur <= 0:
            toast.place(relx=0.98, rely=0.95, anchor="se")
        else:
            # Yumuşak kayarak giriş (Ease-Out: rely 1.03 -> 0.95)
            steps = 7
            interval = max(14, eff_dur // steps)

            def _slide_in(step_idx):
                try:
                    if not toast.winfo_exists():
                        return
                    t = Easing.ease_out(step_idx / float(steps))
                    cur_rely = 1.03 - (0.08 * t)
                    toast.place(relx=0.98, rely=cur_rely, anchor="se")
                    if step_idx < steps:
                        toast.after(interval, lambda: _slide_in(step_idx + 1))
                except Exception:
                    pass

            _slide_in(1)

        try:
            root_widget.after(duration_ms, _dismiss)
        except Exception:
            pass
