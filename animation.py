"""
Fluent & Modern Linux-style Animation Engine (60 FPS Non-blocking)
Provides smooth easing, subtle page slide-in transitions,
breathing pulse indicators, card hover glow, and toast popups.
"""

import math
import customtkinter as ctk

def ease_out_cubic(x: float) -> float:
    return 1.0 - math.pow(1.0 - x, 3)

def ease_in_out_quad(x: float) -> float:
    return 2 * x * x if x < 0.5 else 1 - math.pow(-2 * x + 2, 2) / 2

class FluidAnimator:
    """Hafif, 60 FPS zamanlamalı akıcı animasyon kontrolcüsü."""

    @staticmethod
    def animate_progress_bar(progress_bar, target_val, duration_ms=350, steps=18):
        """İlerleme çubuğunu akıcı bir yay (easing) ile hedefe ulaştırır."""
        start_val = progress_bar.get()
        diff = target_val - start_val
        interval = max(10, duration_ms // steps)

        def step(current_step):
            if not progress_bar.winfo_exists():
                return
            progress = (current_step + 1) / steps
            eased = ease_out_cubic(progress)
            new_val = start_val + diff * eased
            progress_bar.set(new_val)
            if current_step + 1 < steps:
                progress_bar.after(interval, lambda: step(current_step + 1))

        progress_bar.after(interval, lambda: step(0))

    @staticmethod
    def start_pulse_badge(label_widget, color_base="#10B981", color_glow="#34D399", interval_ms=80):
        """Sabit, yüksek kontrastlı ve temiz durum rozeti (Titreşimsiz ve stabil)."""
        try:
            if label_widget.winfo_exists():
                label_widget.configure(text_color=color_base)
        except Exception:
            pass
        return {'running': False}

    @staticmethod
    def slide_in_view(view_widget, start_offset_y=16, duration_ms=180, steps=8):
        """Sayfa geçişini sıfır gecikmeyle stabil ve anında yapar (Tıklama kaçırmaz)."""
        # Geometriyi kaydırmak butonların tıklama koordinatlarını bozduğundan doğrudan stabil pack yapılır
        try:
            view_widget.pack_configure(pady=(0, 10))
        except Exception:
            pass

    @staticmethod
    def show_toast(root_window, message, icon="✨", bg_color="#1E1E1E", border_color="#0078D4", text_color="#FFFFFF"):
        """Windows 11 / GNOME üstten yumuşakça inen bildirim hapı (Toast Notification)."""
        toast = ctk.CTkFrame(
            root_window,
            fg_color=bg_color,
            corner_radius=20,
            border_width=1,
            border_color=border_color
        )

        inner = ctk.CTkFrame(toast, fg_color="transparent")
        inner.pack(padx=16, pady=8)

        ctk.CTkLabel(inner, text=f"{icon}  {message}", font=ctk.CTkFont(size=12, weight="bold"), text_color=text_color).pack(side="left")

        # Animasyon: Yukarıdan aşağıya yumuşak iniş
        toast.place(relx=0.5, y=-50, anchor="n")

        steps = 10
        interval = 15

        def slide_down(step_idx):
            if not toast.winfo_exists():
                return
            prog = (step_idx + 1) / steps
            eased = ease_out_cubic(prog)
            target_y = int(-50 + (18 - (-50)) * eased)
            toast.place_configure(y=target_y)
            if step_idx + 1 < steps:
                toast.after(interval, lambda: slide_down(step_idx + 1))
            else:
                # 2.8 saniye bekle ve yukarı kayarak kapan
                toast.after(2800, lambda: slide_up(0))

        def slide_up(step_idx):
            if not toast.winfo_exists():
                return
            prog = (step_idx + 1) / steps
            eased = ease_in_out_quad(prog)
            target_y = int(18 - 70 * eased)
            toast.place_configure(y=target_y)
            if step_idx + 1 < steps:
                toast.after(interval, lambda: slide_up(step_idx + 1))
            else:
                toast.destroy()

        toast.after(interval, lambda: slide_down(0))
