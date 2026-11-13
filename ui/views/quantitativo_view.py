import os
import customtkinter as ctk
from tkinter import filedialog, messagebox
from pathlib import Path
from datetime import date, datetime
from typing import Callable, Optional, List, Dict, Any

from ui.theme import FONT_FAMILY, COLORS
from ui.dialogs.lancamento_dialog import LancamentoDialog
from services.quantitativo_service import QuantitativoService
from services.task_service import TaskService
from models.quantitativo import Quantitativo, LancamentoItem

class QuantitativoView(ctk.CTkFrame):
    """Visão de Quantitativos Estruturais de Concreto e Formas com navegação fluida de aplicativo."""
    def __init__(
        self,
        master,
        quantitativo_service: QuantitativoService,
        task_service: TaskService,
        on_notify: Optional[Callable[[str, str, str], None]] = None,
        **kwargs
    ):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.quantitativo_service = quantitativo_service
        self.task_service = task_service
        self.on_notify = on_notify

        self.active_quantitativo: Optional[Quantitativo] = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Container Principal
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=0, column=0, sticky="nsew")
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(0, weight=1)

        # Inicia listando os quantitativos
        self.show_list_view()

    def _clear_container(self):
        for child in self.main_container.winfo_children():
            child.destroy()

    # =========================================================================
    # 1. ESTADO: LISTAGEM DE QUANTITATIVOS
    # =========================================================================
    def show_list_view(self):
        self._clear_container()
        self.active_quantitativo = None

        view_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        view_frame.grid(row=0, column=0, sticky="nsew", padx=25, pady=20)
        view_frame.grid_columnconfigure(0, weight=1)
        view_frame.grid_rowconfigure(2, weight=1)

        # Topo
        top_row = ctk.CTkFrame(view_frame, fg_color="transparent")
        top_row.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        top_row.grid_columnconfigure(0, weight=1)

        t_box = ctk.CTkFrame(top_row, fg_color="transparent")
        t_box.grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            t_box, text="🏗️ Levantamentos Estruturais & Quantitativos",
            font=ctk.CTkFont(family=FONT_FAMILY, size=24, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w")

        ctk.CTkLabel(
            t_box, text="Controle de cubagem de concreto (m³), áreas de formas (m²) e avanço físico executivo",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12), text_color=COLORS["text_secondary"]
        ).pack(anchor="w")

        new_btn = ctk.CTkButton(
            top_row, text="+ Novo Quantitativo",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"),
            height=38, width=175,
            fg_color=("#064e3b", "#10b981"), hover_color=("#04382a", "#059669"),
            command=self.show_create_view
        )
        new_btn.grid(row=0, column=1, sticky="e")

        # Stats Cards
        stats = self.quantitativo_service.get_stats()
        stats_frame = ctk.CTkFrame(view_frame, fg_color="transparent")
        stats_frame.grid(row=1, column=0, sticky="ew", pady=(0, 15))
        for i in range(4):
            stats_frame.grid_columnconfigure(i, weight=1)

        def make_kpi(col, title, val, sub):
            card = ctk.CTkFrame(stats_frame, corner_radius=12, fg_color=COLORS["card_bg"], border_width=1, border_color=COLORS["card_border"])
            card.grid(row=0, column=col, sticky="ew", padx=4)
            ctk.CTkLabel(card, text=title.upper(), font=ctk.CTkFont(family=FONT_FAMILY, size=10, weight="bold"), text_color=COLORS["text_muted"]).pack(anchor="w", padx=14, pady=(10, 2))
            ctk.CTkLabel(card, text=val, font=ctk.CTkFont(family=FONT_FAMILY, size=20, weight="bold"), text_color=COLORS["text_primary"]).pack(anchor="w", padx=14, pady=(0, 2))
            ctk.CTkLabel(card, text=sub, font=ctk.CTkFont(family=FONT_FAMILY, size=11), text_color=COLORS["text_secondary"]).pack(anchor="w", padx=14, pady=(0, 10))

        make_kpi(0, "Concreto Total", f"{stats['concreto_total_m3']:.3f} m³".replace(".", ","), "Volume medido")
        make_kpi(1, "Concreto Executado", f"{stats['concreto_executado_m3']:.3f} m³".replace(".", ","), f"{stats['percentual_execucao']}% de avanço")
        make_kpi(2, "Área de Formas", f"{stats['formas_total_m2']:.2f} m²".replace(".", ","), "Contato de formas")
        make_kpi(3, "Lançamentos Ativos", f"{stats['total_lancamentos']} peças", f"{stats['total_quantitativos']} levantamentos")

        # Lista de Quantitativos
        scroll = ctk.CTkScrollableFrame(view_frame, corner_radius=14, fg_color=COLORS["sidebar_bg"], border_width=1, border_color=COLORS["card_border"])
        scroll.grid(row=2, column=0, sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)

        quantitativos = self.quantitativo_service.list_quantitativos()

        if not quantitativos:
            empty = ctk.CTkFrame(scroll, fg_color="transparent")
            empty.pack(pady=70)
            ctk.CTkLabel(empty, text="📋 Nenhum levantamento cadastrado", font=ctk.CTkFont(family=FONT_FAMILY, size=16, weight="bold"), text_color=COLORS["text_secondary"]).pack(pady=(0, 4))
            ctk.CTkLabel(empty, text="Clique em '+ Novo Quantitativo' para cadastrar a primeira medição.", font=ctk.CTkFont(family=FONT_FAMILY, size=12), text_color=COLORS["text_muted"]).pack()
            return

        for q in quantitativos:
            self._render_quantitativo_card(scroll, q)

    def _render_quantitativo_card(self, master, q: Quantitativo):
        card = ctk.CTkFrame(
            master, corner_radius=12,
            fg_color=COLORS["card_bg"],
            border_width=1, border_color=COLORS["card_border"]
        )
        card.pack(fill="x", pady=5, padx=2)
        card.grid_columnconfigure(0, weight=1)

        # Header do Card
        h_row = ctk.CTkFrame(card, fg_color="transparent")
        h_row.pack(fill="x", padx=16, pady=(12, 4))

        title_txt = f"{q.disciplina} · {q.pavimento.upper()}"
        ctk.CTkLabel(
            h_row, text=title_txt,
            font=ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(side="left")

        # Badge Status
        st_badge = ctk.CTkFrame(h_row, corner_radius=6, fg_color=("#ecfdf5", "#064e3b"))
        st_badge.pack(side="right")
        ctk.CTkLabel(
            st_badge, text=q.status.upper(),
            font=ctk.CTkFont(family=FONT_FAMILY, size=10, weight="bold"),
            text_color=("#065f46", "#a7f3d0")
        ).pack(padx=8, pady=2)

        # Subtítulo
        sub_txt = f"{q.obra.upper()} · {q.torre_setor.upper()} · Rev. {q.revisao} · {q.data_levantamento_br}"
        ctk.CTkLabel(
            card, text=sub_txt,
            font=ctk.CTkFont(family=FONT_FAMILY, size=11), text_color=COLORS["text_secondary"], anchor="w"
        ).pack(fill="x", padx=16, pady=(0, 8))

        # Linha de Métricas
        m_row = ctk.CTkFrame(card, fg_color="transparent")
        m_row.pack(fill="x", padx=16, pady=(0, 12))

        m_text = (
            f"📦 Concreto: <b>{q.concreto_total:.3f} m³</b>   •   "
            f"📐 Formas: <b>{q.formas_total:.2f} m²</b>   •   "
            f"🏗️ Peças: <b>{q.total_lancamentos}</b>   •   "
            f"Executado: <b>{q.percentual_execucao:.1f}%</b>"
        )
        ctk.CTkLabel(
            m_row, text=m_text,
            font=ctk.CTkFont(family=FONT_FAMILY, size=11), text_color=COLORS["text_primary"]
        ).pack(side="left")

        open_btn = ctk.CTkButton(
            m_row, text="Abrir Detalhamento ➔",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            height=30, width=150,
            fg_color=("#064e3b", "#10b981"), hover_color=("#04382a", "#059669"),
            command=lambda q_id=q.id: self.show_detail_view(q_id)
        )
        open_btn.pack(side="right")

    # =========================================================================
    # 2. ESTADO: DETALHAMENTO DO QUANTITATIVO (EXATAMENTE COMO O PRINT 1)
    # =========================================================================
    def show_detail_view(self, q_id: int):
        self._clear_container()
        q = self.quantitativo_service.get_quantitativo(q_id)
        if not q:
            self.show_list_view()
            return

        self.active_quantitativo = q

        scroll_detail = ctk.CTkScrollableFrame(self.main_container, fg_color="transparent")
        scroll_detail.grid(row=0, column=0, sticky="nsew", padx=20, pady=15)
        scroll_detail.grid_columnconfigure(0, weight=1)

        # 1. HEADER COM BREADCRUMB
        top_header = ctk.CTkFrame(scroll_detail, fg_color="transparent")
        top_header.pack(fill="x", pady=(0, 12))
        top_header.grid_columnconfigure(0, weight=1)

        t_left = ctk.CTkFrame(top_header, fg_color="transparent")
        t_left.grid(row=0, column=0, sticky="w")

        title_row = ctk.CTkFrame(t_left, fg_color="transparent")
        title_row.pack(anchor="w")

        # Botão Voltar `<`
        back_btn = ctk.CTkButton(
            title_row, text="<", width=30, height=30,
            font=ctk.CTkFont(family=FONT_FAMILY, size=16, weight="bold"),
            fg_color="transparent", text_color=COLORS["text_primary"],
            hover_color=COLORS["card_inner_bg"],
            command=self.show_list_view
        )
        back_btn.pack(side="left", padx=(0, 6))

        title_lbl = ctk.CTkLabel(
            title_row, text=f"{q.disciplina} · {q.pavimento.upper()}",
            font=ctk.CTkFont(family=FONT_FAMILY, size=18, weight="bold"),
            text_color=COLORS["text_primary"]
        )
        title_lbl.pack(side="left")

        # Subtítulo (CHRONOS · TORRE 01 E 02 · Rev. 01 · finalizado)
        sub_text = f"{q.obra.upper()} · {q.torre_setor.upper()} · Rev. {q.revisao} · {q.status.lower()}"
        ctk.CTkLabel(
            t_left, text=sub_text,
            font=ctk.CTkFont(family=FONT_FAMILY, size=11), text_color=COLORS["text_secondary"]
        ).pack(anchor="w", padx=(36, 0))

        # Ações do Topo Direito (Gerar PDF + Novo Lançamento)
        t_right = ctk.CTkFrame(top_header, fg_color="transparent")
        t_right.grid(row=0, column=1, sticky="e")

        pdf_btn = ctk.CTkButton(
            t_right, text="📄 Gerar Laudo PDF",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            height=34, width=135,
            fg_color=("#064e3b", "#10b981"), hover_color=("#04382a", "#059669"),
            command=self._export_pdf
        )
        pdf_btn.pack(side="left", padx=(0, 6))

        add_p_btn = ctk.CTkButton(
            t_right, text="+ Adicionar Peça",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            height=34, width=130,
            fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
            command=self._open_add_lancamento_dialog
        )
        add_p_btn.pack(side="left")

        # 2. BANNER FOREST GREEN ESCURO (IDÊNTICO AO PRINT 1)
        # Background: #062e25
        hero_banner = ctk.CTkFrame(
            scroll_detail, corner_radius=12,
            fg_color="#062e25", border_width=1, border_color="#0a392f"
        )
        hero_banner.pack(fill="x", pady=(0, 14))

        # Linha 1 de Métricas no Banner
        b_metrics_row = ctk.CTkFrame(hero_banner, fg_color="transparent")
        b_metrics_row.pack(fill="x", padx=24, pady=(16, 6))
        for i in range(3):
            b_metrics_row.grid_columnconfigure(i, weight=1)

        # Coluna 1: CONCRETO
        c_c = ctk.CTkFrame(b_metrics_row, fg_color="transparent")
        c_c.grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(c_c, text="CONCRETO", font=ctk.CTkFont(family=FONT_FAMILY, size=10, weight="bold"), text_color="#a7f3d0").pack(anchor="w")
        ctk.CTkLabel(c_c, text=f"{q.concreto_total:.3f} m³".replace(".", ","), font=ctk.CTkFont(family=FONT_FAMILY, size=20, weight="bold"), text_color="#ffffff").pack(anchor="w")

        # Coluna 2: EXECUTADO
        c_e = ctk.CTkFrame(b_metrics_row, fg_color="transparent")
        c_e.grid(row=0, column=1, sticky="w")
        ctk.CTkLabel(c_e, text="EXECUTADO", font=ctk.CTkFont(family=FONT_FAMILY, size=10, weight="bold"), text_color="#a7f3d0").pack(anchor="w")
        ctk.CTkLabel(c_e, text=f"{q.concreto_executado:.3f} m³".replace(".", ","), font=ctk.CTkFont(family=FONT_FAMILY, size=20, weight="bold"), text_color="#ffffff").pack(anchor="w")

        # Coluna 3: EXECUÇÃO
        c_x = ctk.CTkFrame(b_metrics_row, fg_color="transparent")
        c_x.grid(row=0, column=2, sticky="e")
        ctk.CTkLabel(c_x, text="EXECUÇÃO", font=ctk.CTkFont(family=FONT_FAMILY, size=10, weight="bold"), text_color="#a7f3d0").pack(anchor="e")
        ctk.CTkLabel(c_x, text=f"{q.percentual_execucao:.1f}%".replace(".", ","), font=ctk.CTkFont(family=FONT_FAMILY, size=20, weight="bold"), text_color="#ffffff").pack(anchor="e")

        # Divisor sutil no banner
        sep_b = ctk.CTkFrame(hero_banner, height=1, fg_color="#0a392f")
        sep_b.pack(fill="x", padx=24, pady=4)

        # Linha 2 de Sub-Métricas no Banner (Formas e Qtd de lançamentos)
        b_sub_row = ctk.CTkFrame(hero_banner, fg_color="transparent")
        b_sub_row.pack(fill="x", padx=24, pady=(6, 16))

        formas_txt = f"Formas {q.formas_total:.2f} m² · exec. {q.formas_executadas:.2f} m²".replace(".", ",")
        ctk.CTkLabel(
            b_sub_row, text=formas_txt,
            font=ctk.CTkFont(family=FONT_FAMILY, size=11), text_color="#d1fae5"
        ).pack(side="left")

        ctk.CTkLabel(
            b_sub_row, text=f"{q.total_lancamentos} lançamento(s)",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11), text_color="#d1fae5"
        ).pack(side="right")

        # 3. CARD DE METADADOS (IDÊNTICO AO PRINT 1)
        meta_card = ctk.CTkFrame(
            scroll_detail, corner_radius=12,
            fg_color=COLORS["card_bg"],
            border_width=1, border_color=COLORS["card_border"]
        )
        meta_card.pack(fill="x", pady=(0, 16))

        m_cols_row = ctk.CTkFrame(meta_card, fg_color="transparent")
        m_cols_row.pack(fill="x", padx=24, pady=(16, 12))
        for i in range(2):
            m_cols_row.grid_columnconfigure(i, weight=1)

        # Esquerda: Folha e Data
        m_left = ctk.CTkFrame(m_cols_row, fg_color="transparent")
        m_left.grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(m_left, text="FOLHA", font=ctk.CTkFont(family=FONT_FAMILY, size=10, weight="bold"), text_color=COLORS["text_muted"]).pack(anchor="w")
        ctk.CTkLabel(m_left, text=q.folha_projeto, font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"), text_color=COLORS["text_primary"]).pack(anchor="w", pady=(0, 8))

        ctk.CTkLabel(m_left, text="DATA DO LEVANTAMENTO", font=ctk.CTkFont(family=FONT_FAMILY, size=10, weight="bold"), text_color=COLORS["text_muted"]).pack(anchor="w")
        ctk.CTkLabel(m_left, text=q.data_levantamento_br, font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"), text_color=COLORS["text_primary"]).pack(anchor="w")

        # Direita: Revisão e Responsável
        m_right = ctk.CTkFrame(m_cols_row, fg_color="transparent")
        m_right.grid(row=0, column=1, sticky="w")

        ctk.CTkLabel(m_right, text="REVISÃO DO PROJETO", font=ctk.CTkFont(family=FONT_FAMILY, size=10, weight="bold"), text_color=COLORS["text_muted"]).pack(anchor="w")
        ctk.CTkLabel(m_right, text=q.revisao, font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"), text_color=COLORS["text_primary"]).pack(anchor="w", pady=(0, 8))

        ctk.CTkLabel(m_right, text="RESPONSÁVEL", font=ctk.CTkFont(family=FONT_FAMILY, size=10, weight="bold"), text_color=COLORS["text_muted"]).pack(anchor="w")
        ctk.CTkLabel(m_right, text=q.responsavel, font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"), text_color=COLORS["text_primary"]).pack(anchor="w")

        # Botão Reabrir para Correção (Centro)
        reopen_btn = ctk.CTkButton(
            meta_card, text="🔄  Reabrir para correção",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"),
            height=36,
            fg_color="transparent",
            border_width=1, border_color=COLORS["card_border"],
            text_color=COLORS["text_primary"],
            hover_color=COLORS["card_inner_bg"],
            command=self._handle_reopen
        )
        reopen_btn.pack(fill="x", padx=24, pady=(4, 12))

        # Ações Inferiores (Criar revisão à esquerda, Excluir à direita)
        bot_actions_row = ctk.CTkFrame(meta_card, fg_color="transparent")
        bot_actions_row.pack(fill="x", padx=24, pady=(0, 16))

        rev_btn = ctk.CTkButton(
            bot_actions_row, text="⚲ Criar revisão",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            fg_color="transparent", text_color=COLORS["text_primary"],
            hover_color=COLORS["card_inner_bg"],
            command=self._handle_create_revision
        )
        rev_btn.pack(side="left")

        del_btn = ctk.CTkButton(
            bot_actions_row, text="🗑️ Excluir",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            fg_color="transparent", text_color=COLORS["danger"],
            hover_color=COLORS["danger_subtle"],
            command=self._handle_delete_quantitativo
        )
        del_btn.pack(side="right")

        # 4. TABELA DE LANÇAMENTOS (IDÊNTICO AO PRINT 1)
        ctk.CTkLabel(
            scroll_detail, text="LANÇAMENTOS",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"),
            text_color=COLORS["text_muted"]
        ).pack(anchor="w", padx=4, pady=(0, 6))

        table_card = ctk.CTkFrame(
            scroll_detail, corner_radius=12,
            fg_color=COLORS["card_bg"],
            border_width=1, border_color=COLORS["card_border"]
        )
        table_card.pack(fill="x", pady=(0, 20))
        table_card.grid_columnconfigure(0, weight=1)

        # Cabeçalho da Tabela
        th_row = ctk.CTkFrame(table_card, fg_color=COLORS["card_inner_bg"], height=38, corner_radius=8)
        th_row.pack(fill="x", padx=8, pady=(8, 4))
        th_row.grid_columnconfigure(0, weight=2) # ELEMENTO
        th_row.grid_columnconfigure(1, weight=3) # LOCAL
        th_row.grid_columnconfigure(2, weight=1) # PEÇAS
        th_row.grid_columnconfigure(3, weight=2) # DIMENSÕES
        th_row.grid_columnconfigure(4, weight=1) # QTD
        th_row.grid_columnconfigure(5, weight=1) # CONCRETO
        th_row.grid_columnconfigure(6, weight=1) # FORMAS
        th_row.grid_columnconfigure(7, weight=2) # EXECUÇÃO
        th_row.grid_columnconfigure(8, weight=1) # AÇÃO

        headers = ["ELEMENTO", "LOCAL", "PEÇAS", "DIMENSÕES", "QTD", "CONCRETO", "FORMAS", "EXECUÇÃO", ""]
        for idx, h in enumerate(headers):
            lbl = ctk.CTkLabel(
                th_row, text=h,
                font=ctk.CTkFont(family=FONT_FAMILY, size=10, weight="bold"),
                text_color=COLORS["text_muted"]
            )
            lbl.grid(row=0, column=idx, padx=6, pady=8, sticky="w" if idx < 2 else "")

        # Linhas de Lançamentos
        if not q.lancamentos:
            empty_l = ctk.CTkLabel(
                table_card, text="Nenhum lançamento registrado neste quantitativo.",
                font=ctk.CTkFont(family=FONT_FAMILY, size=11), text_color=COLORS["text_muted"]
            )
            empty_l.pack(pady=20)
        else:
            for l_item in q.lancamentos:
                self._render_lancamento_row(table_card, l_item)

    def _render_lancamento_row(self, master, item: LancamentoItem):
        row = ctk.CTkFrame(master, fg_color="transparent", height=42)
        row.pack(fill="x", padx=8, pady=2)
        row.grid_columnconfigure(0, weight=2)
        row.grid_columnconfigure(1, weight=3)
        row.grid_columnconfigure(2, weight=1)
        row.grid_columnconfigure(3, weight=2)
        row.grid_columnconfigure(4, weight=1)
        row.grid_columnconfigure(5, weight=1)
        row.grid_columnconfigure(6, weight=1)
        row.grid_columnconfigure(7, weight=2)
        row.grid_columnconfigure(8, weight=1)

        # Col 0: ELEMENTO (B101 / Bloco)
        c0 = ctk.CTkFrame(row, fg_color="transparent")
        c0.grid(row=0, column=0, sticky="w", padx=6)
        ctk.CTkLabel(c0, text=item.elemento, font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"), text_color=COLORS["text_primary"]).pack(anchor="w")
        ctk.CTkLabel(c0, text=item.tipo, font=ctk.CTkFont(family=FONT_FAMILY, size=9), text_color=COLORS["text_muted"]).pack(anchor="w")

        # Col 1: LOCAL (TORRE 01 E 02 · FUNDAÇÃO)
        ctk.CTkLabel(row, text=item.local, font=ctk.CTkFont(family=FONT_FAMILY, size=10), text_color=COLORS["text_secondary"]).grid(row=0, column=1, sticky="w", padx=6)

        # Col 2: PEÇAS (1)
        ctk.CTkLabel(row, text=str(item.pecas), font=ctk.CTkFont(family=FONT_FAMILY, size=11), text_color=COLORS["text_primary"]).grid(row=0, column=2, padx=6)

        # Col 3: DIMENSÕES (L 0.9 · C 0.9 · H 1)
        ctk.CTkLabel(row, text=item.dimensoes_display, font=ctk.CTkFont(family=FONT_FAMILY, size=10, weight="bold"), text_color=COLORS["text_secondary"]).grid(row=0, column=3, sticky="w", padx=6)

        # Col 4: QTD (1,00)
        ctk.CTkLabel(row, text=f"{item.qtd:.2f}".replace(".", ","), font=ctk.CTkFont(family=FONT_FAMILY, size=11), text_color=COLORS["text_primary"]).grid(row=0, column=4, padx=6)

        # Col 5: CONCRETO (0,810)
        ctk.CTkLabel(row, text=f"{item.concreto_m3:.3f}".replace(".", ","), font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"), text_color=COLORS["primary"]).grid(row=0, column=5, padx=6)

        # Col 6: FORMAS (3,60)
        ctk.CTkLabel(row, text=f"{item.formas_m2:.2f}".replace(".", ","), font=ctk.CTkFont(family=FONT_FAMILY, size=11), text_color=COLORS["text_primary"]).grid(row=0, column=6, padx=6)

        # Col 7: EXECUÇÃO (Pill Badge Clicável: Não executado / Executado)
        badge_bg = ("#ecfdf5", "#064e3b") if item.is_executado else ("#f1f5f9", "#1e293b")
        badge_txt = ("#065f46", "#a7f3d0") if item.is_executado else COLORS["text_secondary"]
        exec_btn = ctk.CTkButton(
            row, text=item.execucao,
            font=ctk.CTkFont(family=FONT_FAMILY, size=10, weight="bold"),
            height=26, width=105, corner_radius=13,
            fg_color=badge_bg, text_color=badge_txt,
            hover_color=("#e2e8f0", "#334155"),
            command=lambda i_id=item.id: self._toggle_execucao(i_id)
        )
        exec_btn.grid(row=0, column=7, padx=4)

        # Col 8: Excluir Linha
        del_btn = ctk.CTkButton(
            row, text="✕", width=22, height=22,
            font=ctk.CTkFont(family=FONT_FAMILY, size=9),
            fg_color="transparent", text_color=COLORS["text_muted"],
            hover_color=COLORS["danger_subtle"],
            command=lambda i_id=item.id: self._delete_lancamento(i_id)
        )
        del_btn.grid(row=0, column=8)

        # Hover Effect
        row.bind("<Enter>", lambda e: row.configure(fg_color=COLORS["card_inner_bg"]))
        row.bind("<Leave>", lambda e: row.configure(fg_color="transparent"))

    def _toggle_execucao(self, item_id: int):
        new_val = self.quantitativo_service.toggle_execucao(item_id)
        if new_val:
            self.show_detail_view(self.active_quantitativo.id)
            if self.on_notify:
                self.on_notify("Status Atualizado", f"Lançamento marcado como '{new_val}'.", "info")

    def _delete_lancamento(self, item_id: int):
        self.quantitativo_service.delete_lancamento(item_id)
        self.show_detail_view(self.active_quantitativo.id)

    def _open_add_lancamento_dialog(self):
        default_local = f"{self.active_quantitativo.torre_setor} · {self.active_quantitativo.pavimento}"
        LancamentoDialog(
            self.winfo_toplevel(),
            default_local=default_local,
            on_save_callback=self._handle_add_lancamento_save
        )

    def _handle_add_lancamento_save(self, data: Dict[str, Any]):
        item, err = self.quantitativo_service.add_lancamento(self.active_quantitativo.id, data)
        if err and self.on_notify:
            self.on_notify("Erro", err, "danger")
        else:
            self.show_detail_view(self.active_quantitativo.id)
            if self.on_notify:
                self.on_notify("Peça Lançada", f"Elemento {data['elemento']} adicionado com sucesso!", "success")

    def _handle_reopen(self):
        self.quantitativo_service.reopen_for_correction(self.active_quantitativo.id)
        self.show_detail_view(self.active_quantitativo.id)
        if self.on_notify:
            self.on_notify("Quantitativo Reaberto", "Status alterado para 'em revisão'.", "info")

    def _handle_create_revision(self):
        new_q = self.quantitativo_service.create_revision(self.active_quantitativo.id)
        if new_q:
            self.show_detail_view(new_q.id)
            if self.on_notify:
                self.on_notify("Nova Revisão Criada", f"Revisão {new_q.revisao} gerada com sucesso!", "success")

    def _handle_delete_quantitativo(self):
        confirm = messagebox.askyesno(
            "Excluir Quantitativo",
            f"Deseja realmente excluir o quantitativo {self.active_quantitativo.titulo_completo}?",
            parent=self.winfo_toplevel()
        )
        if confirm:
            self.quantitativo_service.delete_quantitativo(self.active_quantitativo.id)
            self.show_list_view()
            if self.on_notify:
                self.on_notify("Excluído", "Quantitativo removido com sucesso.", "info")

    def _export_pdf(self):
        q = self.active_quantitativo
        default_name = f"Quantitativo_{q.obra}_{q.pavimento}_{q.revisao}.pdf".replace(" ", "_")

        file_path = filedialog.asksaveasfilename(
            parent=self.winfo_toplevel(),
            defaultextension=".pdf",
            initialfile=default_name,
            filetypes=[("Documentos PDF", "*.pdf"), ("Todos os Arquivos", "*.*")]
        )
        if not file_path:
            return

        try:
            saved_path = self.quantitativo_service.export_pdf(q.id, Path(file_path))
            if self.on_notify:
                self.on_notify("PDF Gerado!", f"Laudo de {q.pavimento} salvo com sucesso.", "success")
            open_f = messagebox.askyesno("PDF Gerado", f"Arquivo salvo em:\n{saved_path}\n\nDeseja abrir agora?", parent=self.winfo_toplevel())
            if open_f:
                os.startfile(str(saved_path))
        except Exception as e:
            messagebox.showerror("Erro ao Gerar PDF", f"Falha na compilação:\n{e}", parent=self.winfo_toplevel())

    # =========================================================================
    # 3. ESTADO: CRIAR NOVO QUANTITATIVO (IDÊNTICO AO PRINT 2)
    # =========================================================================
    def show_create_view(self):
        self._clear_container()

        scroll_create = ctk.CTkScrollableFrame(self.main_container, fg_color="transparent")
        scroll_create.grid(row=0, column=0, sticky="nsew", padx=25, pady=20)
        scroll_create.grid_columnconfigure(0, weight=1)

        # Header com Voltar `< Novo quantitativo`
        top_header = ctk.CTkFrame(scroll_create, fg_color="transparent")
        top_header.pack(fill="x", pady=(0, 14))

        title_row = ctk.CTkFrame(top_header, fg_color="transparent")
        title_row.pack(anchor="w")

        back_btn = ctk.CTkButton(
            title_row, text="<", width=30, height=30,
            font=ctk.CTkFont(family=FONT_FAMILY, size=16, weight="bold"),
            fg_color="transparent", text_color=COLORS["text_primary"],
            hover_color=COLORS["card_inner_bg"],
            command=self.show_list_view
        )
        back_btn.pack(side="left", padx=(0, 6))

        ctk.CTkLabel(
            title_row, text="Novo quantitativo",
            font=ctk.CTkFont(family=FONT_FAMILY, size=18, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(side="left")

        ctk.CTkLabel(
            top_header, text="Obra, torre e pavimento do levantamento",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11), text_color=COLORS["text_secondary"]
        ).pack(anchor="w", padx=(36, 0))

        # CARD PRINCIPAL BRANCO COM BORDA SUTIL (IDÊNTICO AO PRINT 2)
        card_form = ctk.CTkFrame(
            scroll_create, corner_radius=14,
            fg_color=COLORS["card_bg"],
            border_width=1, border_color=COLORS["card_border"]
        )
        card_form.pack(fill="x", pady=(0, 20))

        inner = ctk.CTkFrame(card_form, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=28, pady=24)

        # 1. Obra *
        ctk.CTkLabel(inner, text="Obra *", font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"), text_color=COLORS["text_secondary"]).pack(anchor="w")
        obras_disponiveis = self.task_service.get_obras()
        if not obras_disponiveis:
            obras_disponiveis = ["CHRONOS", "Residencial Bela Vista", "Torre Alpha"]
        elif "CHRONOS" not in obras_disponiveis:
            obras_disponiveis.insert(0, "CHRONOS")

        self.create_obra_combo = ctk.CTkComboBox(
            inner, values=obras_disponiveis, height=36
        )
        self.create_obra_combo.set("CHRONOS")
        self.create_obra_combo.pack(fill="x", pady=(2, 14))

        # 2. Torre / setor e Pavimento * (Lado a Lado)
        r_tp = ctk.CTkFrame(inner, fg_color="transparent")
        r_tp.pack(fill="x", pady=(0, 14))
        r_tp.grid_columnconfigure(0, weight=1)
        r_tp.grid_columnconfigure(1, weight=1)

        c_torre = ctk.CTkFrame(r_tp, fg_color="transparent")
        c_torre.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ctk.CTkLabel(c_torre, text="Torre / setor", font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"), text_color=COLORS["text_secondary"]).pack(anchor="w")
        self.create_torre_entry = ctk.CTkEntry(c_torre, placeholder_text="Torre A", height=36)
        self.create_torre_entry.insert(0, "TORRE 01 E 02")
        self.create_torre_entry.pack(fill="x", pady=(2, 0))

        c_pav = ctk.CTkFrame(r_tp, fg_color="transparent")
        c_pav.grid(row=0, column=1, sticky="ew", padx=(8, 0))
        ctk.CTkLabel(c_pav, text="Pavimento *", font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"), text_color=COLORS["text_secondary"]).pack(anchor="w")
        self.create_pav_entry = ctk.CTkEntry(c_pav, placeholder_text="3º pavimento", height=36)
        self.create_pav_entry.insert(0, "FUNDAÇÃO")
        self.create_pav_entry.pack(fill="x", pady=(2, 0))

        # 3. Tipo de quantitativo (Dois Cards Grandes de Seleção)
        ctk.CTkLabel(inner, text="Tipo de quantitativo", font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"), text_color=COLORS["text_secondary"]).pack(anchor="w", pady=(0, 4))

        self.selected_disciplina = "Estrutural"

        cards_row = ctk.CTkFrame(inner, fg_color="transparent")
        cards_row.pack(fill="x", pady=(0, 14))
        cards_row.grid_columnconfigure(0, weight=1)
        cards_row.grid_columnconfigure(1, weight=1)

        # Card 1: Estrutural (Concreto e formas)
        self.card_est = ctk.CTkFrame(
            cards_row, corner_radius=10,
            fg_color="#064e3b", border_width=1.5, border_color="#0a392f", cursor="hand2"
        )
        self.card_est.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.lbl_est_title = ctk.CTkLabel(self.card_est, text="Estrutural", font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"), text_color="#ffffff")
        self.lbl_est_title.pack(anchor="w", padx=16, pady=(12, 2))
        self.lbl_est_sub = ctk.CTkLabel(self.card_est, text="Concreto e formas", font=ctk.CTkFont(family=FONT_FAMILY, size=10), text_color="#a7f3d0")
        self.lbl_est_sub.pack(anchor="w", padx=16, pady=(0, 12))
        self.card_est.bind("<Button-1>", lambda e: self._select_disciplina("Estrutural"))
        self.lbl_est_title.bind("<Button-1>", lambda e: self._select_disciplina("Estrutural"))
        self.lbl_est_sub.bind("<Button-1>", lambda e: self._select_disciplina("Estrutural"))

        # Card 2: Alvenaria (Áreas e vãos)
        self.card_alv = ctk.CTkFrame(
            cards_row, corner_radius=10,
            fg_color=COLORS["card_bg"], border_width=1, border_color=COLORS["card_border"], cursor="hand2"
        )
        self.card_alv.grid(row=0, column=1, sticky="ew", padx=(8, 0))
        self.lbl_alv_title = ctk.CTkLabel(self.card_alv, text="Alvenaria", font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"), text_color=COLORS["text_primary"])
        self.lbl_alv_title.pack(anchor="w", padx=16, pady=(12, 2))
        self.lbl_alv_sub = ctk.CTkLabel(self.card_alv, text="Áreas e vãos", font=ctk.CTkFont(family=FONT_FAMILY, size=10), text_color=COLORS["text_muted"])
        self.lbl_alv_sub.pack(anchor="w", padx=16, pady=(0, 12))
        self.card_alv.bind("<Button-1>", lambda e: self._select_disciplina("Alvenaria"))
        self.lbl_alv_title.bind("<Button-1>", lambda e: self._select_disciplina("Alvenaria"))
        self.lbl_alv_sub.bind("<Button-1>", lambda e: self._select_disciplina("Alvenaria"))

        # 4. Folha do projeto e Revisão do projeto (Lado a Lado)
        r_fr = ctk.CTkFrame(inner, fg_color="transparent")
        r_fr.pack(fill="x", pady=(0, 14))
        r_fr.grid_columnconfigure(0, weight=1)
        r_fr.grid_columnconfigure(1, weight=1)

        c_folha = ctk.CTkFrame(r_fr, fg_color="transparent")
        c_folha.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ctk.CTkLabel(c_folha, text="Folha do projeto", font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"), text_color=COLORS["text_secondary"]).pack(anchor="w")
        self.create_folha_entry = ctk.CTkEntry(c_folha, placeholder_text="EST-12", height=36)
        self.create_folha_entry.insert(0, "EST-12")
        self.create_folha_entry.pack(fill="x", pady=(2, 0))

        c_rev = ctk.CTkFrame(r_fr, fg_color="transparent")
        c_rev.grid(row=0, column=1, sticky="ew", padx=(8, 0))
        ctk.CTkLabel(c_rev, text="Revisão do projeto", font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"), text_color=COLORS["text_secondary"]).pack(anchor="w")
        self.create_rev_entry = ctk.CTkEntry(c_rev, placeholder_text="R03", height=36)
        self.create_rev_entry.insert(0, "R02")
        self.create_rev_entry.pack(fill="x", pady=(2, 0))

        # 5. Data do levantamento 📅
        ctk.CTkLabel(inner, text="Data do levantamento", font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"), text_color=COLORS["text_secondary"]).pack(anchor="w")
        self.create_data_entry = ctk.CTkEntry(inner, placeholder_text="DD/MM/AAAA", height=36)
        self.create_data_entry.insert(0, date.today().strftime("%d/%m/%Y"))
        self.create_data_entry.pack(fill="x", pady=(2, 14))

        # 6. Observações técnicas
        ctk.CTkLabel(inner, text="Observações técnicas", font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"), text_color=COLORS["text_secondary"]).pack(anchor="w")
        self.create_obs_text = ctk.CTkTextbox(inner, height=80, corner_radius=8)
        self.create_obs_text.pack(fill="x", pady=(2, 20))

        # Erro inline
        self.create_error_lbl = ctk.CTkLabel(inner, text="", font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"), text_color=COLORS["danger"])
        self.create_error_lbl.pack(fill="x", pady=(0, 6))

        # 7. Botão Grande Verde Escuro "Criar quantitativo" (IDÊNTICO AO PRINT 2)
        submit_btn = ctk.CTkButton(
            inner, text="Criar quantitativo",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
            height=44, corner_radius=8,
            fg_color="#064e3b", hover_color="#04382a", text_color="#ffffff",
            command=self._handle_create_quantitativo
        )
        submit_btn.pack(fill="x")

    def _select_disciplina(self, disc: str):
        self.selected_disciplina = disc
        if disc == "Estrutural":
            self.card_est.configure(fg_color="#064e3b", border_color="#0a392f")
            self.lbl_est_title.configure(text_color="#ffffff")
            self.lbl_est_sub.configure(text_color="#a7f3d0")

            self.card_alv.configure(fg_color=COLORS["card_bg"], border_color=COLORS["card_border"])
            self.lbl_alv_title.configure(text_color=COLORS["text_primary"])
            self.lbl_alv_sub.configure(text_color=COLORS["text_muted"])
        else:
            self.card_alv.configure(fg_color="#064e3b", border_color="#0a392f")
            self.lbl_alv_title.configure(text_color="#ffffff")
            self.lbl_alv_sub.configure(text_color="#a7f3d0")

            self.card_est.configure(fg_color=COLORS["card_bg"], border_color=COLORS["card_border"])
            self.lbl_est_title.configure(text_color=COLORS["text_primary"])
            self.lbl_est_sub.configure(text_color=COLORS["text_muted"])

    def _handle_create_quantitativo(self):
        obra = self.create_obra_combo.get().strip()
        pav = self.create_pav_entry.get().strip()
        if not obra or not pav:
            self.create_error_lbl.configure(text="⚠️ Preencha os campos obrigatórios (*).")
            return

        payload = {
            "obra": obra,
            "torre_setor": self.create_torre_entry.get().strip(),
            "pavimento": pav,
            "disciplina": self.selected_disciplina,
            "folha_projeto": self.create_folha_entry.get().strip(),
            "revisao": self.create_rev_entry.get().strip(),
            "data_levantamento": self.create_data_entry.get().strip(),
            "responsavel": "Gil Márcio Bispo de Jesus Júnior",
            "observacoes": self.create_obs_text.get("1.0", "end").strip()
        }

        created, err = self.quantitativo_service.create_quantitativo(payload)
        if err:
            self.create_error_lbl.configure(text=f"⚠️ {err}")
            return

        if self.on_notify:
            self.on_notify("Quantitativo Criado", f"{created.titulo_completo} cadastrado com sucesso!", "success")

        # Abre diretamente o detalhamento do quantitativo recém-criado
        self.show_detail_view(created.id)
