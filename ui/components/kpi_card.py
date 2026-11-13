import customtkinter as ctk
from ui.theme import FONT_FAMILY, COLORS

class KPICard(ctk.CTkFrame):
    """Card de indicador executivo moderno com top glow, ícone estilizado e métricas de tendência."""
    def __init__(
        self, master,
        title: str,
        value: str,
        subtitle: str = "",
        icon: str = "📊",
        accent_color: str = "#3b82f6",
        badge_text: str = "",
        badge_color: str = "",
        **kwargs
    ):
        super().__init__(
            master,
            corner_radius=14,
            border_width=1,
            fg_color=COLORS["card_bg"],
            border_color=COLORS["card_border"],
            **kwargs
        )

        self.accent_color = accent_color
        self.grid_columnconfigure(0, weight=1)

        # Barra superior luminosa (Glow bar)
        self.top_glow = ctk.CTkFrame(
            self, height=3, corner_radius=2, fg_color=accent_color
        )
        self.top_glow.pack(fill="x", padx=12, pady=(3, 0))

        # Conteúdo interno
        inner_frame = ctk.CTkFrame(self, fg_color="transparent")
        inner_frame.pack(fill="both", expand=True, padx=16, pady=(10, 14))
        inner_frame.grid_columnconfigure(0, weight=1)

        # Linha 1: Ícone + Título + Badge opcional
        header_row = ctk.CTkFrame(inner_frame, fg_color="transparent")
        header_row.pack(fill="x", pady=(0, 6))

        # Ícone em container arredondado
        icon_box = ctk.CTkFrame(
            header_row, width=32, height=32, corner_radius=8,
            fg_color=COLORS["card_inner_bg"],
            border_width=1, border_color=COLORS["card_border"]
        )
        icon_box.pack(side="left", padx=(0, 8))
        icon_box.pack_propagate(False)

        self.icon_label = ctk.CTkLabel(
            icon_box, text=icon, font=ctk.CTkFont(family=FONT_FAMILY, size=15)
        )
        self.icon_label.pack(expand=True)

        # Título
        self.title_label = ctk.CTkLabel(
            header_row, text=title.upper(),
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            text_color=COLORS["text_secondary"]
        )
        self.title_label.pack(side="left")

        # Linha 2: Grande Valor Numérico
        self.value_label = ctk.CTkLabel(
            inner_frame, text=value,
            font=ctk.CTkFont(family=FONT_FAMILY, size=28, weight="bold"),
            text_color=COLORS["text_primary"]
        )
        self.value_label.pack(anchor="w", pady=(0, 2))

        # Linha 3: Subtítulo de Apoio
        self.subtitle_label = ctk.CTkLabel(
            inner_frame, text=subtitle,
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=COLORS["text_muted"]
        )
        self.subtitle_label.pack(anchor="w")

        # Hover Effect Sofisticado
        def on_enter(e):
            self.configure(border_color=self.accent_color)
            self.top_glow.configure(height=5)

        def on_leave(e):
            self.configure(border_color=COLORS["card_border"])
            self.top_glow.configure(height=3)

        self.bind("<Enter>", on_enter)
        self.bind("<Leave>", on_leave)

    def update_values(self, value: str, subtitle: str = ""):
        self.value_label.configure(text=value)
        if subtitle:
            self.subtitle_label.configure(text=subtitle)
