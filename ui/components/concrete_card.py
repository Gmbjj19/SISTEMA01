import customtkinter as ctk
from typing import Callable, Optional
from ui.theme import FONT_FAMILY, COLORS
from models.concrete import ConcreteMeasurement

class ConcreteCard(ctk.CTkFrame):
    """Card moderno para exibição de Boletim de Medição de Concreto com ação de emissão em PDF."""
    def __init__(
        self,
        master,
        bm: ConcreteMeasurement,
        on_export_pdf: Optional[Callable[[ConcreteMeasurement], None]] = None,
        on_delete: Optional[Callable[[ConcreteMeasurement], None]] = None,
        **kwargs
    ):
        super().__init__(
            master,
            corner_radius=12,
            border_width=1,
            fg_color=COLORS["card_bg"],
            border_color=COLORS["card_border"],
            **kwargs
        )

        self.bm = bm
        self.on_export_pdf = on_export_pdf
        self.on_delete = on_delete

        self.grid_columnconfigure(1, weight=1)

        # Barra lateral indicadora azul concreto
        self.accent_bar = ctk.CTkFrame(self, width=5, corner_radius=2, fg_color=COLORS["primary"])
        self.accent_bar.grid(row=0, column=0, rowspan=3, sticky="ns", padx=(4, 10), pady=6)

        # Container Principal
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=0, column=1, sticky="nsew", padx=(0, 10), pady=10)
        content.grid_columnconfigure(0, weight=1)

        # Linha 1: Código + Obra + Elemento
        top_line = ctk.CTkFrame(content, fg_color="transparent")
        top_line.pack(fill="x", pady=(0, 4))

        # Badge do Código
        code_badge = ctk.CTkFrame(
            top_line, corner_radius=6,
            fg_color=COLORS["primary_subtle"],
            border_width=1, border_color=COLORS["primary_border"]
        )
        code_badge.pack(side="left", padx=(0, 8))

        ctk.CTkLabel(
            code_badge, text=bm.boletim_code,
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            text_color=COLORS["primary"]
        ).pack(padx=8, pady=2)

        ctk.CTkLabel(
            top_line, text=f"🏗️ {bm.obra}",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(side="left", padx=(0, 12))

        ctk.CTkLabel(
            top_line, text=f"📅 {bm.data_concretagem_br}",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=COLORS["text_muted"]
        ).pack(side="left")

        # Linha 2: Elemento Concretado
        elem_label = ctk.CTkLabel(
            content, text=f"🧱 {bm.elemento}",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
            text_color=COLORS["text_primary"],
            anchor="w"
        )
        elem_label.pack(fill="x", pady=(0, 4))

        # Linha 3: Especificações Técnicas (fck, slump, brita, fornecedor, peças)
        chips_line = ctk.CTkFrame(content, fg_color="transparent")
        chips_line.pack(fill="x")

        num_pecas = len(bm.itens)
        specs_text = (
            f"⚡ fck {bm.fck_mpa} MPa  •  "
            f"💧 Slump {bm.slump_cm} cm  •  "
            f"📦 {bm.brita_tipo}  •  "
            f"👤 {bm.responsavel}  •  "
            f"Peças: {num_pecas} cadastradas"
        )
        ctk.CTkLabel(
            chips_line, text=specs_text,
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=COLORS["text_secondary"]
        ).pack(side="left")

        # Coluna Direita: Volume Total em Destaque + Botões
        actions_frame = ctk.CTkFrame(self, fg_color="transparent")
        actions_frame.grid(row=0, column=2, rowspan=3, sticky="e", padx=(0, 14), pady=10)

        # Volume Destaque
        vol_box = ctk.CTkFrame(actions_frame, corner_radius=8, fg_color=COLORS["card_inner_bg"])
        vol_box.pack(side="left", padx=(0, 12))

        ctk.CTkLabel(
            vol_box, text=f"{bm.volume_total:.2f} m³",
            font=ctk.CTkFont(family=FONT_FAMILY, size=15, weight="bold"),
            text_color=COLORS["primary"]
        ).pack(padx=10, pady=(4, 0))

        ctk.CTkLabel(
            vol_box, text="Volume Efetivo",
            font=ctk.CTkFont(family=FONT_FAMILY, size=9),
            text_color=COLORS["text_muted"]
        ).pack(padx=10, pady=(0, 4))

        # Botão Gerar PDF
        pdf_btn = ctk.CTkButton(
            actions_frame,
            text="📄 Gerar PDF",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            height=34,
            width=115,
            fg_color=COLORS["success"],
            hover_color=COLORS["success_hover"],
            command=self._handle_pdf
        )
        pdf_btn.pack(side="left", padx=(0, 6))

        # Botão Excluir
        del_btn = ctk.CTkButton(
            actions_frame,
            text="✕",
            width=32,
            height=34,
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            fg_color="transparent",
            text_color=COLORS["text_muted"],
            hover_color=COLORS["danger_subtle"],
            command=self._handle_delete
        )
        del_btn.pack(side="left")

        # Hover Effect
        self.bind("<Enter>", lambda e: self.configure(border_color=COLORS["card_hover_border"]))
        self.bind("<Leave>", lambda e: self.configure(border_color=COLORS["card_border"]))

    def _handle_pdf(self):
        if self.on_export_pdf:
            self.on_export_pdf(self.bm)

    def _handle_delete(self):
        if self.on_delete:
            self.on_delete(self.bm)
