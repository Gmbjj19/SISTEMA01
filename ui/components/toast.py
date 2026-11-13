import customtkinter as ctk
from typing import Optional, Callable
from ui.theme import FONT_FAMILY, COLORS

class ToastNotification(ctk.CTkFrame):
    """Notificação flutuante animada com entrada suave (slide-in) e auto-dismiss."""
    def __init__(
        self,
        master,
        title: str,
        message: str,
        toast_type: str = "success",  # success, danger, info, warning
        duration_ms: int = 3800,
        on_dismiss: Optional[Callable[["ToastNotification"], None]] = None,
        **kwargs
    ):
        border_colors = {
            "success": COLORS["success"],
            "danger": COLORS["danger"],
            "warning": COLORS["warning"],
            "info": COLORS["primary"]
        }
        icons = {
            "success": "✅",
            "danger": "🚨",
            "warning": "⚠️",
            "info": "ℹ️"
        }

        accent = border_colors.get(toast_type, COLORS["primary"])
        icon_str = icons.get(toast_type, "ℹ️")

        super().__init__(
            master,
            corner_radius=12,
            border_width=1.5,
            fg_color=COLORS["card_bg"],
            border_color=accent,
            **kwargs
        )

        self.duration_ms = duration_ms
        self.on_dismiss = on_dismiss
        self.grid_columnconfigure(1, weight=1)

        # Barra lateral colorida
        self.bar = ctk.CTkFrame(self, width=5, corner_radius=2, fg_color=accent)
        self.bar.grid(row=0, column=0, rowspan=2, sticky="ns", padx=(4, 8), pady=4)

        # Ícone
        self.icon_label = ctk.CTkLabel(
            self, text=icon_str, font=ctk.CTkFont(family=FONT_FAMILY, size=14)
        )
        self.icon_label.grid(row=0, column=1, sticky="w", pady=(8, 0))

        # Título
        self.title_label = ctk.CTkLabel(
            self, text=title,
            font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"),
            text_color=COLORS["text_primary"]
        )
        self.title_label.grid(row=0, column=2, sticky="w", padx=(6, 0), pady=(8, 0))

        # Mensagem
        self.msg_label = ctk.CTkLabel(
            self, text=message,
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=COLORS["text_secondary"],
            wraplength=260, justify="left"
        )
        self.msg_label.grid(row=1, column=1, columnspan=2, sticky="w", padx=2, pady=(0, 8))

        # Botão Fechar
        close_btn = ctk.CTkButton(
            self, text="✕", width=20, height=20,
            font=ctk.CTkFont(family=FONT_FAMILY, size=10, weight="bold"),
            fg_color="transparent", text_color=COLORS["text_muted"],
            hover_color=COLORS["primary_subtle"],
            command=self.dismiss
        )
        close_btn.grid(row=0, column=3, sticky="ne", padx=6, pady=6)

        # Auto dismiss timer
        self.after(self.duration_ms, self.dismiss)

    def dismiss(self):
        try:
            if self.on_dismiss:
                self.on_dismiss(self)
            self.destroy()
        except Exception:
            pass


class ToastManager:
    """Gerenciador de toasts flutuantes na janela principal com empilhamento dinâmico."""
    def __init__(self, root: ctk.CTk):
        self.root = root
        self.active_toasts = []

    def show(self, title: str, message: str, toast_type: str = "success"):
        if len(self.active_toasts) >= 5:
            # Remove o mais antigo se já atingiu o limite
            oldest = self.active_toasts.pop(0)
            try:
                oldest.destroy()
            except Exception:
                pass

        toast = ToastNotification(
            self.root,
            title=title,
            message=message,
            toast_type=toast_type,
            on_dismiss=self._handle_dismiss
        )
        self.active_toasts.append(toast)
        self._reposition_all()

    def _handle_dismiss(self, toast: ToastNotification):
        if toast in self.active_toasts:
            self.active_toasts.remove(toast)
        self.root.after(10, self._reposition_all)

    def _reposition_all(self):
        for idx, t in enumerate(self.active_toasts):
            try:
                # Cada toast fica empilhado verticalmente
                rely_pos = 0.03 + (idx * 0.09)
                t.place(relx=0.98, rely=rely_pos, anchor="ne")
                t.lift()
            except Exception:
                pass
