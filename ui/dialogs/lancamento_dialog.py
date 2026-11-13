import customtkinter as ctk
from typing import Callable, Optional, Dict, Any
from ui.theme import FONT_FAMILY, COLORS

class LancamentoDialog(ctk.CTkToplevel):
    """Modal para adicionar lançamento de peça estrutural com cálculo dinâmico de concreto e formas."""
    def __init__(
        self,
        master,
        default_local: str,
        on_save_callback: Callable[[Dict[str, Any]], None]
    ):
        super().__init__(master)

        self.default_local = default_local
        self.on_save_callback = on_save_callback

        self.title("Novo Lançamento de Peça Estrutural")
        self.geometry("520x600")
        self.resizable(False, False)

        self.transient(master)
        self.grab_set()

        self._center_window()
        self._build_ui()

    def _center_window(self):
        self.update_idletasks()
        width = 520
        height = 600
        x = max(0, (self.winfo_screenwidth() // 2) - (width // 2))
        y = max(0, (self.winfo_screenheight() // 2) - (height // 2))
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _build_ui(self):
        # Cabeçalho
        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", padx=24, pady=(20, 10))

        ctk.CTkLabel(
            head, text="➕ Adicionar Lançamento de Peça",
            font=ctk.CTkFont(family=FONT_FAMILY, size=16, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w")

        ctk.CTkLabel(
            head, text="Informe as dimensões em metros para cálculo automático de cubagem e formas",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11), text_color=COLORS["text_secondary"]
        ).pack(anchor="w")

        form = ctk.CTkFrame(self, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=24)

        # 1. Elemento e Tipo
        r1 = ctk.CTkFrame(form, fg_color="transparent")
        r1.pack(fill="x", pady=(0, 10))
        r1.grid_columnconfigure(0, weight=6)
        r1.grid_columnconfigure(1, weight=4)

        c_el = ctk.CTkFrame(r1, fg_color="transparent")
        c_el.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ctk.CTkLabel(c_el, text="Elemento (ex: B101, P1, V102) *", font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"), text_color=COLORS["text_secondary"]).pack(anchor="w")
        self.elem_entry = ctk.CTkEntry(c_el, placeholder_text="B101", height=34)
        self.elem_entry.pack(fill="x", pady=(2, 0))

        c_tp = ctk.CTkFrame(r1, fg_color="transparent")
        c_tp.grid(row=0, column=1, sticky="ew", padx=(6, 0))
        ctk.CTkLabel(c_tp, text="Tipo Estrutural", font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"), text_color=COLORS["text_secondary"]).pack(anchor="w")
        self.tipo_menu = ctk.CTkOptionMenu(c_tp, values=["Bloco", "Pilar", "Viga", "Laje", "Sapata", "Estaca", "Escada"], height=34)
        self.tipo_menu.set("Bloco")
        self.tipo_menu.pack(fill="x", pady=(2, 0))

        # 2. Local
        ctk.CTkLabel(form, text="Local / Pavimento", font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"), text_color=COLORS["text_secondary"]).pack(anchor="w")
        self.local_entry = ctk.CTkEntry(form, height=34)
        self.local_entry.insert(0, self.default_local)
        self.local_entry.pack(fill="x", pady=(2, 10))

        # 3. Dimensões (Largura, Comprimento, Altura em metros)
        ctk.CTkLabel(form, text="Dimensões Geométricas (metros)", font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"), text_color=COLORS["text_secondary"]).pack(anchor="w")

        r_dim = ctk.CTkFrame(form, fg_color="transparent")
        r_dim.pack(fill="x", pady=(2, 10))
        for i in range(3):
            r_dim.grid_columnconfigure(i, weight=1)

        c_l = ctk.CTkFrame(r_dim, fg_color="transparent")
        c_l.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        ctk.CTkLabel(c_l, text="Largura (L)", font=ctk.CTkFont(family=FONT_FAMILY, size=10), text_color=COLORS["text_muted"]).pack(anchor="w")
        self.larg_entry = ctk.CTkEntry(c_l, placeholder_text="0.90", height=34)
        self.larg_entry.pack(fill="x")
        self.larg_entry.bind("<KeyRelease>", lambda e: self._update_preview())

        c_c = ctk.CTkFrame(r_dim, fg_color="transparent")
        c_c.grid(row=0, column=1, sticky="ew", padx=4)
        ctk.CTkLabel(c_c, text="Comprimento (C)", font=ctk.CTkFont(family=FONT_FAMILY, size=10), text_color=COLORS["text_muted"]).pack(anchor="w")
        self.comp_entry = ctk.CTkEntry(c_c, placeholder_text="0.90", height=34)
        self.comp_entry.pack(fill="x")
        self.comp_entry.bind("<KeyRelease>", lambda e: self._update_preview())

        c_h = ctk.CTkFrame(r_dim, fg_color="transparent")
        c_h.grid(row=0, column=2, sticky="ew", padx=(4, 0))
        ctk.CTkLabel(c_h, text="Altura/Esp (H)", font=ctk.CTkFont(family=FONT_FAMILY, size=10), text_color=COLORS["text_muted"]).pack(anchor="w")
        self.alt_entry = ctk.CTkEntry(c_h, placeholder_text="1.00", height=34)
        self.alt_entry.pack(fill="x")
        self.alt_entry.bind("<KeyRelease>", lambda e: self._update_preview())

        # 4. Peças e Multiplicador Qtd
        r_pq = ctk.CTkFrame(form, fg_color="transparent")
        r_pq.pack(fill="x", pady=(0, 10))
        r_pq.grid_columnconfigure(0, weight=1)
        r_pq.grid_columnconfigure(1, weight=1)

        c_p = ctk.CTkFrame(r_pq, fg_color="transparent")
        c_p.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        ctk.CTkLabel(c_p, text="Nº de Peças", font=ctk.CTkFont(family=FONT_FAMILY, size=10), text_color=COLORS["text_muted"]).pack(anchor="w")
        self.pecas_entry = ctk.CTkEntry(c_p, placeholder_text="1", height=34)
        self.pecas_entry.insert(0, "1")
        self.pecas_entry.pack(fill="x")
        self.pecas_entry.bind("<KeyRelease>", lambda e: self._update_preview())

        c_q = ctk.CTkFrame(r_pq, fg_color="transparent")
        c_q.grid(row=0, column=1, sticky="ew", padx=(4, 0))
        ctk.CTkLabel(c_q, text="Multiplicador (QTD)", font=ctk.CTkFont(family=FONT_FAMILY, size=10), text_color=COLORS["text_muted"]).pack(anchor="w")
        self.qtd_entry = ctk.CTkEntry(c_q, placeholder_text="1.00", height=34)
        self.qtd_entry.insert(0, "1.00")
        self.qtd_entry.pack(fill="x")
        self.qtd_entry.bind("<KeyRelease>", lambda e: self._update_preview())

        # Banner de Preview em Tempo Real
        self.preview_box = ctk.CTkFrame(
            form, corner_radius=8,
            fg_color=("#ecfdf5", "#064e3b"),
            border_width=1, border_color=("#a7f3d0", "#065f46")
        )
        self.preview_box.pack(fill="x", pady=(4, 12))

        self.preview_label = ctk.CTkLabel(
            self.preview_box,
            text="Concreto Estimado: 0,000 m³  •  Área de Formas: 0,00 m²",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"),
            text_color=("#065f46", "#a7f3d0")
        )
        self.preview_label.pack(pady=10)

        # Erro inline
        self.error_label = ctk.CTkLabel(
            form, text="", font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            text_color=COLORS["danger"]
        )
        self.error_label.pack(fill="x", pady=(0, 6))

        # Botão Salvar
        self.save_btn = ctk.CTkButton(
            self, text="Salvar Lançamento",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
            height=42, fg_color=("#064e3b", "#10b981"), hover_color=("#04382a", "#059669"),
            command=self._handle_save
        )
        self.save_btn.pack(fill="x", padx=24, pady=(0, 20))

    def _update_preview(self):
        try:
            l = float(self.larg_entry.get().replace(",", "."))
            c = float(self.comp_entry.get().replace(",", "."))
            h = float(self.alt_entry.get().replace(",", "."))
            p = int(self.pecas_entry.get())
            q = float(self.qtd_entry.get().replace(",", "."))

            fator = p * q
            conc = c * l * h * fator
            tp = self.tipo_menu.get().lower()
            if "laje" in tp:
                formas = c * l * fator
            elif "viga" in tp:
                formas = (l + 2 * h) * c * fator
            else:
                formas = 2 * (l + c) * h * fator

            self.preview_label.configure(
                text=f"Concreto Estimado: {conc:.3f} m³  •  Área de Formas: {formas:.2f} m²"
            )
        except Exception:
            self.preview_label.configure(
                text="Preencha os valores para calcular o volume e a área de formas"
            )

    def _handle_save(self):
        el = self.elem_entry.get().strip()
        if not el:
            self.error_label.configure(text="⚠️ Informe o código ou nome do elemento.")
            return

        try:
            l = float(self.larg_entry.get().replace(",", "."))
            c = float(self.comp_entry.get().replace(",", "."))
            h = float(self.alt_entry.get().replace(",", "."))
            p = int(self.pecas_entry.get())
            q = float(self.qtd_entry.get().replace(",", "."))
        except ValueError:
            self.error_label.configure(text="⚠️ Valores de dimensões e quantidades inválidos.")
            return

        payload = {
            "elemento": el,
            "tipo": self.tipo_menu.get(),
            "local": self.local_entry.get().strip(),
            "largura": l,
            "comprimento": c,
            "altura": h,
            "pecas": p,
            "qtd": q,
            "execucao": "Não executado"
        }
        self.on_save_callback(payload)
        self.destroy()

