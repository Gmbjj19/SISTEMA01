import os
import customtkinter as ctk
from tkinter import filedialog, messagebox
from pathlib import Path
from datetime import datetime
from typing import Callable, Optional, List

from ui.theme import FONT_FAMILY, COLORS
from ui.components.kpi_card import KPICard
from ui.components.concrete_card import ConcreteCard
from ui.dialogs.concrete_dialog import ConcreteDialog
from services.concrete_service import ConcreteService
from services.task_service import TaskService
from models.concrete import ConcreteMeasurement

class ConcreteView(ctk.CTkFrame):
    """Visão executiva e operacional de Boletins de Medição e Levantamento de Concreto Usinado."""
    def __init__(
        self,
        master,
        concrete_service: ConcreteService,
        task_service: TaskService,
        on_notify: Optional[Callable[[str, str, str], None]] = None,
        **kwargs
    ):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.concrete_service = concrete_service
        self.task_service = task_service
        self.on_notify = on_notify

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        self._build_header()
        self._build_kpi_cards()
        self._build_filters()
        self._build_list_container()

        self.refresh()

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=25, pady=(20, 10))
        header.grid_columnconfigure(0, weight=1)

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            title_box,
            text="🏗️ Boletins de Medição & Concreto Usinado",
            font=ctk.CTkFont(family=FONT_FAMILY, size=24, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w")

        self.subtitle = ctk.CTkLabel(
            title_box,
            text="Levantamento geométrico de peças estruturais, controle tecnológico e emissão de laudos ABNT em PDF",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color=COLORS["text_secondary"]
        )
        self.subtitle.pack(anchor="w")

        # Botão Novo Boletim
        new_bm_btn = ctk.CTkButton(
            header,
            text="+ Novo Boletim de Medição",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"),
            height=38,
            width=210,
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            command=self.open_new_dialog
        )
        new_bm_btn.grid(row=0, column=1, sticky="e")

    def _build_kpi_cards(self):
        self.kpi_container = ctk.CTkFrame(self, fg_color="transparent")
        self.kpi_container.grid(row=1, column=0, sticky="ew", padx=25, pady=(0, 14))

        for i in range(4):
            self.kpi_container.grid_columnconfigure(i, weight=1, uniform="concrete_kpi")

        self.card_vol = KPICard(self.kpi_container, title="Volume Concretado", value="0.0 m³", subtitle="Total acumulado", icon="📊", accent_color=COLORS["primary"])
        self.card_vol.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        self.card_bms = KPICard(self.kpi_container, title="Boletins Emitidos", value="0", subtitle="Laudos registrados", icon="📋", accent_color=COLORS["info"])
        self.card_bms.grid(row=0, column=1, sticky="ew", padx=6)

        self.card_obras = KPICard(self.kpi_container, title="Obras Atendidas", value="0", subtitle="Canteiros ativos", icon="🏗️", accent_color=COLORS["warning"])
        self.card_obras.grid(row=0, column=2, sticky="ew", padx=6)

        self.card_fck = KPICard(self.kpi_container, title="Resistência Média", value="30 MPa", subtitle="Classe fck ponderada", icon="⚡", accent_color=COLORS["success"])
        self.card_fck.grid(row=0, column=3, sticky="ew", padx=(6, 0))

    def _build_filters(self):
        filter_row = ctk.CTkFrame(self, fg_color="transparent")
        filter_row.grid(row=2, column=0, sticky="ew", padx=25, pady=(0, 10))
        filter_row.grid_columnconfigure(0, weight=1)

        # Campo de Busca
        self.search_entry = ctk.CTkEntry(
            filter_row,
            placeholder_text="🔍 Pesquisar por código (ex: BM-2026), peça concretada, obra, fornecedor ou responsável...",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            height=36,
            corner_radius=8
        )
        self.search_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.search_entry.bind("<KeyRelease>", lambda e: self.refresh_list())

        # Filtro de Obra
        self.obra_var = ctk.StringVar(value="Todas as Obras")
        self.obra_menu = ctk.CTkOptionMenu(
            filter_row,
            variable=self.obra_var,
            values=["Todas as Obras"],
            width=180,
            height=36,
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            command=lambda v: self.refresh_list()
        )
        self.obra_menu.grid(row=0, column=1, sticky="e")

    def _build_list_container(self):
        self.scrollable_container = ctk.CTkScrollableFrame(
            self,
            corner_radius=14,
            border_width=1,
            fg_color=COLORS["sidebar_bg"],
            border_color=COLORS["card_border"]
        )
        self.scrollable_container.grid(row=3, column=0, sticky="nsew", padx=25, pady=(0, 20))
        self.scrollable_container.grid_columnconfigure(0, weight=1)

    def refresh(self):
        """Atualiza indicadores analíticos e a lista de medições."""
        stats = self.concrete_service.get_stats()
        self.card_vol.update_values(f"{stats['volume_total_m3']} m³", "Total acumulado de concreto")
        self.card_bms.update_values(str(stats["total_boletins"]), "Laudos registrados")
        self.card_obras.update_values(str(stats["obras_atendidas"]), "Canteiros com medição")
        self.card_fck.update_values(f"{stats['fck_medio']:.0f} MPa", "Classe fck média")

        # Atualiza lista de obras
        obras = self.task_service.get_obras()
        current_obra = self.obra_var.get()
        new_values = ["Todas as Obras"] + obras
        self.obra_menu.configure(values=new_values)
        if current_obra in new_values:
            self.obra_var.set(current_obra)
        else:
            self.obra_var.set("Todas as Obras")

        self.refresh_list()

    def refresh_list(self):
        search = self.search_entry.get().strip()
        obra_filter = None if self.obra_var.get() == "Todas as Obras" else self.obra_var.get()

        measurements = self.concrete_service.list_measurements(search=search, obra=obra_filter)

        for child in self.scrollable_container.winfo_children():
            child.destroy()

        if not measurements:
            empty_box = ctk.CTkFrame(self.scrollable_container, fg_color="transparent")
            empty_box.pack(pady=70)

            ctk.CTkLabel(
                empty_box, text="📋 Nenhum boletim de medição cadastrado",
                font=ctk.CTkFont(family=FONT_FAMILY, size=16, weight="bold"),
                text_color=COLORS["text_secondary"]
            ).pack(pady=(0, 4))
            ctk.CTkLabel(
                empty_box, text="Clique em '+ Novo Boletim de Medição' para realizar o levantamento de cubagem.",
                font=ctk.CTkFont(family=FONT_FAMILY, size=12), text_color=COLORS["text_muted"]
            ).pack()
            return

        for bm in measurements:
            card = ConcreteCard(
                self.scrollable_container,
                bm=bm,
                on_export_pdf=self.export_pdf,
                on_delete=self.delete_measurement
            )
            card.pack(fill="x", pady=4, padx=2)

    def open_new_dialog(self):
        obras = self.task_service.get_obras()
        resps = self.task_service.get_responsibles()
        ConcreteDialog(
            self.winfo_toplevel(),
            on_save_callback=self._handle_save_dialog,
            obras_suggestions=obras,
            responsibles_suggestions=resps
        )

    def _handle_save_dialog(self, payload: dict, _unused_id, dialog: ConcreteDialog):
        bm, err = self.concrete_service.create_measurement(payload)
        if err:
            dialog.show_error(err)
            return

        dialog.destroy()
        self.refresh()

        if self.on_notify:
            self.on_notify("Boletim Criado", f"Boletim {bm.boletim_code} registrado com sucesso!", "success")

    def export_pdf(self, bm: ConcreteMeasurement):
        default_name = f"Boletim_{bm.boletim_code.replace('-', '_')}_{bm.obra.replace(' ', '_')}.pdf"

        file_path = filedialog.asksaveasfilename(
            parent=self.winfo_toplevel(),
            defaultextension=".pdf",
            initialfile=default_name,
            filetypes=[("Documentos PDF", "*.pdf"), ("Todos os Arquivos", "*.*")]
        )

        if not file_path:
            return

        try:
            saved_path = self.concrete_service.export_pdf(bm.id, Path(file_path))

            if self.on_notify:
                self.on_notify("PDF Gerado!", f"Laudo {bm.boletim_code} exportado com sucesso.", "success")

            # Pergunta se deseja abrir o PDF
            open_file = messagebox.askyesno(
                "PDF Gerado com Sucesso",
                f"O Boletim de Medição foi gerado em:\n{saved_path}\n\nDeseja abrir o documento agora?",
                parent=self.winfo_toplevel()
            )
            if open_file:
                os.startfile(str(saved_path))
        except Exception as e:
            messagebox.showerror("Erro ao Gerar PDF", f"Falha ao compilar documento:\n{e}", parent=self.winfo_toplevel())

    def delete_measurement(self, bm: ConcreteMeasurement):
        confirm = messagebox.askyesno(
            "Confirmar Exclusão",
            f"Deseja realmente excluir o Boletim de Medição {bm.boletim_code} ({bm.elemento})?",
            parent=self.winfo_toplevel()
        )
        if confirm:
            self.concrete_service.delete_measurement(bm.id)
            self.refresh()
            if self.on_notify:
                self.on_notify("Boletim Excluído", f"{bm.boletim_code} foi removido com sucesso.", "info")
