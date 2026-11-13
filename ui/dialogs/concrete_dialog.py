import customtkinter as ctk
from datetime import date, datetime
from typing import Callable, Optional, List, Dict, Any

from ui.theme import FONT_FAMILY, COLORS
from models.concrete import ConcreteMeasurement, ConcreteItem

class ConcreteDialog(ctk.CTkToplevel):
    """Janela modal para Criação e Levantamento Geométrico de Concreto com cálculo de cubagem em tempo real."""
    def __init__(
        self,
        master,
        on_save_callback: Callable[[Dict[str, Any], Optional[int], Any], None],
        obras_suggestions: Optional[List[str]] = None,
        responsibles_suggestions: Optional[List[str]] = None
    ):
        super().__init__(master)

        self.on_save_callback = on_save_callback
        self.itens: List[ConcreteItem] = []

        self.title("🏗️ Novo Boletim de Medição & Cubagem de Concreto")
        self.geometry("740x840")
        self.minsize(700, 780)

        self.transient(master)
        self.grab_set()

        self._center_window()
        self._build_ui(obras_suggestions or [], responsibles_suggestions or [])

    def _center_window(self):
        self.update_idletasks()
        width = 740
        height = 840
        x = max(0, (self.winfo_screenwidth() // 2) - (width // 2))
        y = max(0, (self.winfo_screenheight() // 2) - (height // 2) - 20)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _build_ui(self, obras_list: List[str], resp_list: List[str]):
        # Cabeçalho Principal
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=28, pady=(18, 8))

        ctk.CTkLabel(
            header_frame,
            text="🏗️ Novo Boletim de Medição de Concreto",
            font=ctk.CTkFont(family=FONT_FAMILY, size=18, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w")

        ctk.CTkLabel(
            header_frame,
            text="Levantamento geométrico de peças, parâmetros tecnológicos e cálculo de cubagem usinada",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=COLORS["text_secondary"]
        ).pack(anchor="w")

        # Container com rolagem para o formulário
        self.scroll_body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_body.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        # --- SEÇÃO 1: DADOS GERAIS DA OBRA ---
        sec1 = ctk.CTkFrame(self.scroll_body, corner_radius=10, fg_color=COLORS["card_bg"], border_width=1, border_color=COLORS["card_border"])
        sec1.pack(fill="x", pady=(0, 10), padx=8)

        ctk.CTkLabel(
            sec1, text="1. DADOS DA OBRA & ELEMENTO ESTRUTURAL",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            text_color=COLORS["primary"]
        ).pack(anchor="w", padx=14, pady=(10, 8))

        row1 = ctk.CTkFrame(sec1, fg_color="transparent")
        row1.pack(fill="x", padx=14, pady=(0, 10))
        row1.grid_columnconfigure(0, weight=1)
        row1.grid_columnconfigure(1, weight=1)

        # Obra
        col_o = ctk.CTkFrame(row1, fg_color="transparent")
        col_o.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ctk.CTkLabel(col_o, text="Canteiro / Obra *", font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"), text_color=COLORS["text_secondary"]).pack(anchor="w")
        self.obra_combo = ctk.CTkComboBox(col_o, values=obras_list if obras_list else ["Geral", "Residencial Park"], height=34)
        self.obra_combo.pack(fill="x", pady=(2, 0))

        # Responsável
        col_r = ctk.CTkFrame(row1, fg_color="transparent")
        col_r.grid(row=0, column=1, sticky="ew", padx=(6, 0))
        ctk.CTkLabel(col_r, text="Responsável Técnico *", font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"), text_color=COLORS["text_secondary"]).pack(anchor="w")
        self.resp_combo = ctk.CTkComboBox(col_r, values=resp_list if resp_list else ["Eng. Fiscal", "Eng. Carlos"], height=34)
        self.resp_combo.pack(fill="x", pady=(2, 0))

        # Elemento e Data
        row2 = ctk.CTkFrame(sec1, fg_color="transparent")
        row2.pack(fill="x", padx=14, pady=(0, 14))
        row2.grid_columnconfigure(0, weight=7)
        row2.grid_columnconfigure(1, weight=3)

        col_el = ctk.CTkFrame(row2, fg_color="transparent")
        col_el.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ctk.CTkLabel(col_el, text="Elemento Concretado *", font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"), text_color=COLORS["text_secondary"]).pack(anchor="w")
        self.elemento_entry = ctk.CTkEntry(col_el, placeholder_text="Ex: Vigas e Laje do 4º Pavimento - Bloco B", height=34)
        self.elemento_entry.pack(fill="x", pady=(2, 0))

        col_dt = ctk.CTkFrame(row2, fg_color="transparent")
        col_dt.grid(row=0, column=1, sticky="ew", padx=(6, 0))
        ctk.CTkLabel(col_dt, text="Data da Concretagem *", font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"), text_color=COLORS["text_secondary"]).pack(anchor="w")
        self.data_entry = ctk.CTkEntry(col_dt, placeholder_text="DD/MM/AAAA", height=34)
        self.data_entry.insert(0, date.today().strftime("%d/%m/%Y"))
        self.data_entry.pack(fill="x", pady=(2, 0))

        # --- SEÇÃO 2: ESPECIFICAÇÕES DO CONCRETO ---
        sec2 = ctk.CTkFrame(self.scroll_body, corner_radius=10, fg_color=COLORS["card_bg"], border_width=1, border_color=COLORS["card_border"])
        sec2.pack(fill="x", pady=(0, 10), padx=8)

        ctk.CTkLabel(
            sec2, text="2. ESPECIFICAÇÕES TÉCNICAS DO CONCRETO USINADO",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            text_color=COLORS["primary"]
        ).pack(anchor="w", padx=14, pady=(10, 8))

        row_sp = ctk.CTkFrame(sec2, fg_color="transparent")
        row_sp.pack(fill="x", padx=14, pady=(0, 10))
        for i in range(4):
            row_sp.grid_columnconfigure(i, weight=1)

        # Fck
        c_fck = ctk.CTkFrame(row_sp, fg_color="transparent")
        c_fck.grid(row=0, column=0, sticky="ew", padx=3)
        ctk.CTkLabel(c_fck, text="fck (MPa)", font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"), text_color=COLORS["text_secondary"]).pack(anchor="w")
        self.fck_menu = ctk.CTkOptionMenu(c_fck, values=["20", "25", "30", "35", "40", "50"], height=32)
        self.fck_menu.set("30")
        self.fck_menu.pack(fill="x", pady=(2, 0))

        # Slump
        c_slump = ctk.CTkFrame(row_sp, fg_color="transparent")
        c_slump.grid(row=0, column=1, sticky="ew", padx=3)
        ctk.CTkLabel(c_slump, text="Slump (cm)", font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"), text_color=COLORS["text_secondary"]).pack(anchor="w")
        self.slump_entry = ctk.CTkEntry(c_slump, height=32)
        self.slump_entry.insert(0, "12.0")
        self.slump_entry.pack(fill="x", pady=(2, 0))

        # Brita
        c_brita = ctk.CTkFrame(row_sp, fg_color="transparent")
        c_brita.grid(row=0, column=2, sticky="ew", padx=3)
        ctk.CTkLabel(c_brita, text="Brita", font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"), text_color=COLORS["text_secondary"]).pack(anchor="w")
        self.brita_menu = ctk.CTkOptionMenu(c_brita, values=["Brita 0", "Brita 1", "Brita 2", "Mista"], height=32)
        self.brita_menu.set("Brita 1")
        self.brita_menu.pack(fill="x", pady=(2, 0))

        # Perda %
        c_perda = ctk.CTkFrame(row_sp, fg_color="transparent")
        c_perda.grid(row=0, column=3, sticky="ew", padx=3)
        ctk.CTkLabel(c_perda, text="Perda Técnica (%)", font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"), text_color=COLORS["text_secondary"]).pack(anchor="w")
        self.perda_entry = ctk.CTkEntry(c_perda, height=32)
        self.perda_entry.insert(0, "5.0")
        self.perda_entry.pack(fill="x", pady=(2, 0))
        self.perda_entry.bind("<KeyRelease>", lambda e: self._recalculate_totals())

        # Fornecedor & NF
        row_fn = ctk.CTkFrame(sec2, fg_color="transparent")
        row_fn.pack(fill="x", padx=14, pady=(0, 14))
        row_fn.grid_columnconfigure(0, weight=1)
        row_fn.grid_columnconfigure(1, weight=1)

        c_fn = ctk.CTkFrame(row_fn, fg_color="transparent")
        c_fn.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ctk.CTkLabel(c_fn, text="Usina / Fornecedor", font=ctk.CTkFont(family=FONT_FAMILY, size=11), text_color=COLORS["text_secondary"]).pack(anchor="w")
        self.fornecedor_entry = ctk.CTkEntry(c_fn, placeholder_text="Ex: Polimix Concreto", height=32)
        self.fornecedor_entry.pack(fill="x", pady=(2, 0))

        c_nf = ctk.CTkFrame(row_fn, fg_color="transparent")
        c_nf.grid(row=0, column=1, sticky="ew", padx=(6, 0))
        ctk.CTkLabel(c_nf, text="Nota Fiscal / Lacres", font=ctk.CTkFont(family=FONT_FAMILY, size=11), text_color=COLORS["text_secondary"]).pack(anchor="w")
        self.nf_entry = ctk.CTkEntry(c_nf, placeholder_text="Ex: NF 14208 - Lacre 88219", height=32)
        self.nf_entry.pack(fill="x", pady=(2, 0))

        # --- SEÇÃO 3: CALCULADORA GEOMÉTRICA DE PEÇAS ---
        sec3 = ctk.CTkFrame(self.scroll_body, corner_radius=10, fg_color=COLORS["card_bg"], border_width=1, border_color=COLORS["card_border"])
        sec3.pack(fill="x", pady=(0, 10), padx=8)

        ctk.CTkLabel(
            sec3, text="3. LEVANTAMENTO GEOMÉTRICO DAS PEÇAS ESTRUTURAIS",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            text_color=COLORS["primary"]
        ).pack(anchor="w", padx=14, pady=(10, 6))

        # Formulário para adicionar peça
        add_box = ctk.CTkFrame(sec3, corner_radius=8, fg_color=COLORS["card_inner_bg"], border_width=1, border_color=COLORS["card_border"])
        add_box.pack(fill="x", padx=14, pady=(0, 8))

        row_in1 = ctk.CTkFrame(add_box, fg_color="transparent")
        row_in1.pack(fill="x", padx=8, pady=(8, 4))
        row_in1.grid_columnconfigure(0, weight=4)
        row_in1.grid_columnconfigure(1, weight=2)
        row_in1.grid_columnconfigure(2, weight=1)
        row_in1.grid_columnconfigure(3, weight=1)
        row_in1.grid_columnconfigure(4, weight=1)
        row_in1.grid_columnconfigure(5, weight=1)

        # Identificação da Peça
        c1 = ctk.CTkFrame(row_in1, fg_color="transparent")
        c1.grid(row=0, column=0, sticky="ew", padx=2)
        ctk.CTkLabel(c1, text="Identificação Peça", font=ctk.CTkFont(family=FONT_FAMILY, size=10, weight="bold"), text_color=COLORS["text_secondary"]).pack(anchor="w")
        self.item_name_entry = ctk.CTkEntry(c1, placeholder_text="Ex: Pilares P1 a P8", height=28)
        self.item_name_entry.pack(fill="x")

        # Tipo
        c2 = ctk.CTkFrame(row_in1, fg_color="transparent")
        c2.grid(row=0, column=1, sticky="ew", padx=2)
        ctk.CTkLabel(c2, text="Tipo", font=ctk.CTkFont(family=FONT_FAMILY, size=10, weight="bold"), text_color=COLORS["text_secondary"]).pack(anchor="w")
        self.item_tipo_menu = ctk.CTkOptionMenu(c2, values=["Pilar", "Viga", "Laje", "Sapata/Bloco", "Estaca", "Escada", "Radier"], height=28)
        self.item_tipo_menu.pack(fill="x")

        # Comp (m)
        c3 = ctk.CTkFrame(row_in1, fg_color="transparent")
        c3.grid(row=0, column=2, sticky="ew", padx=2)
        ctk.CTkLabel(c3, text="Comp (m)", font=ctk.CTkFont(family=FONT_FAMILY, size=10, weight="bold"), text_color=COLORS["text_secondary"]).pack(anchor="w")
        self.item_c_entry = ctk.CTkEntry(c3, placeholder_text="0.00", height=28)
        self.item_c_entry.pack(fill="x")

        # Larg (m)
        c4 = ctk.CTkFrame(row_in1, fg_color="transparent")
        c4.grid(row=0, column=3, sticky="ew", padx=2)
        ctk.CTkLabel(c4, text="Larg (m)", font=ctk.CTkFont(family=FONT_FAMILY, size=10, weight="bold"), text_color=COLORS["text_secondary"]).pack(anchor="w")
        self.item_l_entry = ctk.CTkEntry(c4, placeholder_text="0.00", height=28)
        self.item_l_entry.pack(fill="x")

        # Alt (m)
        c5 = ctk.CTkFrame(row_in1, fg_color="transparent")
        c5.grid(row=0, column=4, sticky="ew", padx=2)
        ctk.CTkLabel(c5, text="Alt/Esp (m)", font=ctk.CTkFont(family=FONT_FAMILY, size=10, weight="bold"), text_color=COLORS["text_secondary"]).pack(anchor="w")
        self.item_h_entry = ctk.CTkEntry(c5, placeholder_text="0.00", height=28)
        self.item_h_entry.pack(fill="x")

        # Qtd
        c6 = ctk.CTkFrame(row_in1, fg_color="transparent")
        c6.grid(row=0, column=5, sticky="ew", padx=2)
        ctk.CTkLabel(c6, text="Qtd", font=ctk.CTkFont(family=FONT_FAMILY, size=10, weight="bold"), text_color=COLORS["text_secondary"]).pack(anchor="w")
        self.item_q_entry = ctk.CTkEntry(c6, placeholder_text="1", height=28)
        self.item_q_entry.insert(0, "1")
        self.item_q_entry.pack(fill="x")

        # Botão Adicionar Item
        btn_add = ctk.CTkButton(
            add_box, text="+ Adicionar Peça ao Levantamento",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            height=30, fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
            command=self._handle_add_item
        )
        btn_add.pack(fill="x", padx=8, pady=(4, 8))

        # Lista de Itens Adicionados
        self.itens_frame = ctk.CTkFrame(sec3, fg_color="transparent")
        self.itens_frame.pack(fill="x", padx=14, pady=(0, 10))
        self._refresh_itens_ui()

        # Banner de Totais de Concreto
        self.totals_banner = ctk.CTkFrame(
            sec3, corner_radius=8,
            fg_color=COLORS["primary_subtle"],
            border_width=1, border_color=COLORS["primary_border"]
        )
        self.totals_banner.pack(fill="x", padx=14, pady=(0, 12))

        self.totals_label = ctk.CTkLabel(
            self.totals_banner,
            text="Volume Teórico: 0.000 m³  •  Perda (5.0%): 0.00 m³  ➔  TOTAL: 0.00 m³",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
            text_color=COLORS["primary"]
        )
        self.totals_label.pack(pady=10)

        # Seção 4: Observações de Campo
        sec4 = ctk.CTkFrame(self.scroll_body, corner_radius=10, fg_color=COLORS["card_bg"], border_width=1, border_color=COLORS["card_border"])
        sec4.pack(fill="x", pady=(0, 10), padx=8)

        ctk.CTkLabel(
            sec4, text="4. OBSERVAÇÕES E NOTAS DE CAMPO",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            text_color=COLORS["primary"]
        ).pack(anchor="w", padx=14, pady=(10, 4))

        self.obs_text = ctk.CTkTextbox(sec4, height=60, corner_radius=8)
        self.obs_text.pack(fill="x", padx=14, pady=(0, 12))

        # Rodapé: Erro e Botão Salvar
        self.error_label = ctk.CTkLabel(
            self, text="",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            text_color=COLORS["danger"]
        )
        self.error_label.pack(fill="x", padx=28, pady=(4, 2))

        self.save_btn = ctk.CTkButton(
            self,
            text="💾 Salvar e Emitir Boletim de Medição",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
            height=42,
            fg_color=COLORS["success"],
            hover_color=COLORS["success_hover"],
            command=self._handle_save
        )
        self.save_btn.pack(fill="x", padx=28, pady=(0, 18))

    def _handle_add_item(self):
        name = self.item_name_entry.get().strip()
        tipo = self.item_tipo_menu.get()
        try:
            c = float(self.item_c_entry.get().replace(",", "."))
            l = float(self.item_l_entry.get().replace(",", "."))
            h = float(self.item_h_entry.get().replace(",", "."))
            q = int(self.item_q_entry.get())
        except ValueError:
            self.show_error("Dimensões devem ser números válidos (ex: 3.50).")
            return

        if not name:
            name = f"{tipo} {len(self.itens) + 1}"

        item = ConcreteItem(
            elemento=name,
            tipo=tipo,
            comprimento=c,
            largura=l,
            altura=h,
            quantidade=q
        )
        item.calculate_volume()
        self.itens.append(item)

        # Limpar campos
        self.item_name_entry.delete(0, "end")
        self.item_c_entry.delete(0, "end")
        self.item_l_entry.delete(0, "end")
        self.item_h_entry.delete(0, "end")
        self.item_q_entry.delete(0, "end")
        self.item_q_entry.insert(0, "1")

        self.error_label.configure(text="")
        self._refresh_itens_ui()
        self._recalculate_totals()

    def _refresh_itens_ui(self):
        for child in self.itens_frame.winfo_children():
            child.destroy()

        if not self.itens:
            ctk.CTkLabel(
                self.itens_frame, text="Nenhuma peça adicionada ainda. Preencha os campos acima para cubagem.",
                font=ctk.CTkFont(family=FONT_FAMILY, size=11), text_color=COLORS["text_muted"]
            ).pack(pady=4)
            return

        for idx, it in enumerate(self.itens):
            item_row = ctk.CTkFrame(self.itens_frame, fg_color=COLORS["card_inner_bg"], corner_radius=6)
            item_row.pack(fill="x", pady=2)

            info_text = f"#{idx+1} {it.elemento} ({it.tipo}): {it.comprimento:.2f}m x {it.largura:.2f}m x {it.altura:.2f}m | Qtd: {it.quantidade} ➔ {it.volume_total:.3f} m³"
            ctk.CTkLabel(
                item_row, text=info_text,
                font=ctk.CTkFont(family=FONT_FAMILY, size=11), text_color=COLORS["text_primary"]
            ).pack(side="left", padx=10, pady=4)

            del_btn = ctk.CTkButton(
                item_row, text="✕", width=22, height=22,
                font=ctk.CTkFont(family=FONT_FAMILY, size=10, weight="bold"),
                fg_color="transparent", text_color=COLORS["danger"],
                command=lambda i=idx: self._remove_item(i)
            )
            del_btn.pack(side="right", padx=6)

    def _remove_item(self, idx: int):
        if 0 <= idx < len(self.itens):
            self.itens.pop(idx)
            self._refresh_itens_ui()
            self._recalculate_totals()

    def _recalculate_totals(self):
        teorico = sum(it.volume_total for it in self.itens)
        try:
            perda = float(self.perda_entry.get().replace(",", "."))
        except ValueError:
            perda = 5.0
        fator = 1.0 + (perda / 100.0)
        total = round(teorico * fator, 2)
        perda_m3 = round(total - teorico, 2)

        self.totals_label.configure(
            text=f"Volume Teórico: {teorico:.3f} m³   •   Perda ({perda:.1f}%): +{perda_m3:.2f} m³   ➔   TOTAL SOLICITADO: {total:.2f} m³"
        )

    def _handle_save(self):
        obra = self.obra_combo.get().strip()
        elemento = self.elemento_entry.get().strip()
        data_c = self.data_entry.get().strip()
        responsavel = self.resp_combo.get().strip()

        if not obra or not elemento:
            self.show_error("Preencha a Obra e a descrição do Elemento Concretado.")
            return

        try:
            perda = float(self.perda_entry.get().replace(",", "."))
        except ValueError:
            perda = 5.0

        try:
            slump = float(self.slump_entry.get().replace(",", "."))
        except ValueError:
            slump = 12.0

        payload = {
            "obra": obra,
            "elemento": elemento,
            "data_concretagem": data_c,
            "responsavel": responsavel,
            "fck_mpa": int(self.fck_menu.get()),
            "slump_cm": slump,
            "brita_tipo": self.brita_menu.get(),
            "perda_percentual": perda,
            "fornecedor": self.fornecedor_entry.get().strip(),
            "nota_fiscal": self.nf_entry.get().strip(),
            "observacoes": self.obs_text.get("1.0", "end").strip(),
            "itens": self.itens
        }

        self.on_save_callback(payload, None, self)

    def show_error(self, message: str):
        self.error_label.configure(text=f"⚠️ {message}")
