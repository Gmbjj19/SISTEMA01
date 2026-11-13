import customtkinter as ctk
from datetime import date
from typing import Callable, Optional

from ui.theme import FONT_FAMILY, COLORS, DEADLINE_COLORS, PRIORITY_COLORS
from ui.components.kpi_card import KPICard
from services.metrics_service import MetricsService
from services.task_service import TaskService
from models.metrics import DashboardMetrics, ObraMetrics
from models.task import Task
from models.enums import TaskPriority

class DashboardView(ctk.CTkFrame):
    """Cockpit executivo moderno com indicadores estratégicos, progresso por canteiro e alertas de SLA."""
    def __init__(
        self,
        master,
        metrics_service: MetricsService,
        task_service: TaskService,
        on_navigate_to_tasks: Optional[Callable[[], None]] = None,
        **kwargs
    ):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.metrics_service = metrics_service
        self.task_service = task_service
        self.on_navigate_to_tasks = on_navigate_to_tasks

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._build_hero_header()
        self._build_kpi_cards()
        self._build_panels()

        self.refresh()

    def _build_hero_header(self):
        hero_frame = ctk.CTkFrame(self, fg_color="transparent")
        hero_frame.grid(row=0, column=0, sticky="ew", padx=25, pady=(20, 15))
        hero_frame.grid_columnconfigure(0, weight=1)

        left_box = ctk.CTkFrame(hero_frame, fg_color="transparent")
        left_box.grid(row=0, column=0, sticky="w")

        title = ctk.CTkLabel(
            left_box,
            text="📊 Painel Executivo de Obras",
            font=ctk.CTkFont(family=FONT_FAMILY, size=24, weight="bold"),
            text_color=COLORS["text_primary"]
        )
        title.pack(anchor="w")

        today = date.today()
        week_num = today.isocalendar()[1]
        meses = ["Janeiro","Fevereiro","Março","Abril","Maio","Junho","Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"]
        month_name = meses[today.month - 1]
        today_str = f"{today.day} de {month_name} de {today.year}"
        week_str = f"Semana {week_num}"
        self.subtitle = ctk.CTkLabel(
            left_box,
            text=f"Acompanhamento em tempo real dos cronogramas e entregas de canteiro • {today_str} • {week_str}",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color=COLORS["text_secondary"]
        )
        self.subtitle.pack(anchor="w")

        # Botão Ação e Alertas
        right_box = ctk.CTkFrame(hero_frame, fg_color="transparent")
        right_box.grid(row=0, column=1, sticky="e")

        self.alert_badge = ctk.CTkLabel(
            right_box,
            text="",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            text_color=COLORS["danger"]
        )
        self.alert_badge.pack(side="left", padx=(0, 10))

        refresh_btn = ctk.CTkButton(
            right_box,
            text="🔄 Atualizar Indicadores",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            height=36,
            width=165,
            fg_color="transparent",
            border_width=1,
            border_color=COLORS["card_border"],
            text_color=COLORS["text_primary"],
            hover_color=COLORS["primary_subtle"],
            command=self.refresh
        )
        refresh_btn.pack(side="left")

        # Barra de Progresso Global do Cronograma Geral
        progress_frame = ctk.CTkFrame(hero_frame, fg_color="transparent")
        progress_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10, 0))

        self.global_progress_label = ctk.CTkLabel(
            progress_frame,
            text="Progresso geral: 0% concluído",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            text_color=COLORS["text_secondary"]
        )
        self.global_progress_label.pack(anchor="w", pady=(0, 3))

        self.global_progress_bar = ctk.CTkProgressBar(
            progress_frame, height=8, corner_radius=4
        )
        self.global_progress_bar.pack(fill="x")
        self.global_progress_bar.set(0)

    def _build_kpi_cards(self):
        self.kpi_container = ctk.CTkFrame(self, fg_color="transparent")
        self.kpi_container.grid(row=1, column=0, sticky="ew", padx=25, pady=(0, 16))

        for i in range(5):
            self.kpi_container.grid_columnconfigure(i, weight=1, uniform="kpi")

        self.card_total = KPICard(
            self.kpi_container, title="Total de Tarefas", value="0", subtitle="Monitoradas",
            icon="📋", accent_color=COLORS["primary"]
        )
        self.card_total.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        self.card_progress = KPICard(
            self.kpi_container, title="Em Andamento", value="0", subtitle="Em execução",
            icon="⏳", accent_color=COLORS["info"]
        )
        self.card_progress.grid(row=0, column=1, sticky="ew", padx=6)

        self.card_done = KPICard(
            self.kpi_container, title="Concluídas", value="0", subtitle="0% de avanço",
            icon="✅", accent_color=COLORS["success"]
        )
        self.card_done.grid(row=0, column=2, sticky="ew", padx=6)

        self.card_overdue = KPICard(
            self.kpi_container, title="Atrasadas", value="0", subtitle="Atenção imediata",
            icon="🚨", accent_color=COLORS["danger"]
        )
        self.card_overdue.grid(row=0, column=3, sticky="ew", padx=6)

        self.card_obras = KPICard(
            self.kpi_container, title="Obras Ativas", value="0", subtitle="Canteiros ativos",
            icon="🏗️", accent_color=COLORS["warning"]
        )
        self.card_obras.grid(row=0, column=4, sticky="ew", padx=(6, 0))

    def _build_panels(self):
        content_grid = ctk.CTkFrame(self, fg_color="transparent")
        content_grid.grid(row=2, column=0, sticky="nsew", padx=25, pady=(0, 20))
        content_grid.grid_columnconfigure(0, weight=6)
        content_grid.grid_columnconfigure(1, weight=4)
        content_grid.grid_rowconfigure(0, weight=1)

        # Painel Esquerdo: Avanço Consolidado por Obra
        self.obras_panel = ctk.CTkFrame(
            content_grid,
            corner_radius=14,
            border_width=1,
            fg_color=COLORS["card_bg"],
            border_color=COLORS["card_border"]
        )
        self.obras_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.obras_panel.grid_rowconfigure(1, weight=1)
        self.obras_panel.grid_columnconfigure(0, weight=1)

        obras_header = ctk.CTkFrame(self.obras_panel, fg_color="transparent")
        obras_header.grid(row=0, column=0, sticky="ew", padx=18, pady=(16, 10))

        ctk.CTkLabel(
            obras_header,
            text="🏗️ Progresso Físico por Obra",
            font=ctk.CTkFont(family=FONT_FAMILY, size=15, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(side="left")

        self.obras_scroll = ctk.CTkScrollableFrame(self.obras_panel, fg_color="transparent")
        self.obras_scroll.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))

        # Painel Direito: Tarefas Críticas (Atrasadas ou Urgentes)
        self.critical_panel = ctk.CTkFrame(
            content_grid,
            corner_radius=14,
            border_width=1,
            fg_color=COLORS["card_bg"],
            border_color=COLORS["card_border"]
        )
        self.critical_panel.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        self.critical_panel.grid_rowconfigure(1, weight=1)
        self.critical_panel.grid_columnconfigure(0, weight=1)

        crit_header = ctk.CTkFrame(self.critical_panel, fg_color="transparent")
        crit_header.grid(row=0, column=0, sticky="ew", padx=18, pady=(16, 10))

        ctk.CTkLabel(
            crit_header,
            text="🚨 Foco Imediato (Atrasos & Urgências)",
            font=ctk.CTkFont(family=FONT_FAMILY, size=15, weight="bold"),
            text_color=COLORS["danger"]
        ).pack(side="left")

        self.crit_scroll = ctk.CTkScrollableFrame(self.critical_panel, fg_color="transparent")
        self.crit_scroll.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))

    def refresh(self):
        metrics: DashboardMetrics = self.metrics_service.get_dashboard_metrics()

        # Atualização dos Cards
        self.card_total.update_values(str(metrics.total), "Tarefas no banco")
        self.card_progress.update_values(str(metrics.em_andamento), f"{metrics.pendentes} a iniciar")
        self.card_done.update_values(str(metrics.concluidas), f"{metrics.taxa_conclusao}% do cronograma")

        overdue_sub = f"{metrics.taxa_atraso}% de atraso"
        if metrics.vencendo_hoje > 0:
            overdue_sub += f" • ⏰ {metrics.vencendo_hoje} vencem hoje"
        self.card_overdue.update_values(str(metrics.atrasadas), overdue_sub)
        self.card_obras.update_values(str(metrics.obras_ativas), "Canteiros ativos")

        # Atualização da Barra de Progresso Global
        taxa = metrics.taxa_conclusao / 100.0
        self.global_progress_bar.set(taxa)
        bar_color = COLORS["success"] if taxa >= 0.8 else (COLORS["info"] if taxa >= 0.4 else COLORS["warning"])
        self.global_progress_bar.configure(progress_color=bar_color)
        self.global_progress_label.configure(
            text=f"Avanço Geral do Cronograma: {metrics.taxa_conclusao}% concluído • {metrics.concluidas} de {metrics.total} atividades finalizadas"
        )

        # Atualização do Badge de Alerta
        if metrics.atrasadas > 0 or metrics.urgentes > 0:
            alerts = []
            if metrics.atrasadas > 0:
                alerts.append(f"🚨 {metrics.atrasadas} Atrasada(s)")
            if metrics.urgentes > 0:
                alerts.append(f"⚡ {metrics.urgentes} Urgente(s)")
            self.alert_badge.configure(text=" | ".join(alerts), text_color=COLORS["danger"])
        else:
            self.alert_badge.configure(text="✅ Cronograma em Dia", text_color=COLORS["success"])

        # Atualização de Obras
        for child in self.obras_scroll.winfo_children():
            child.destroy()

        if not metrics.obras_detalhes:
            empty_lbl = ctk.CTkLabel(
                self.obras_scroll, text="Nenhum canteiro de obras registrado.",
                font=ctk.CTkFont(family=FONT_FAMILY, size=12), text_color=COLORS["text_muted"]
            )
            empty_lbl.pack(pady=50)
        else:
            for om in metrics.obras_detalhes:
                self._render_obra_card(om)

        # Atualização de Tarefas Críticas
        for child in self.crit_scroll.winfo_children():
            child.destroy()

        critical_tasks = self.task_service.list_tasks(order_by="deadline")
        filtered_crit = [
            t for t in critical_tasks
            if not t.is_completed and (t.is_overdue or t.priority == TaskPriority.URGENTE)
        ][:8]

        if not filtered_crit:
            clean_box = ctk.CTkFrame(self.crit_scroll, fg_color="transparent")
            clean_box.pack(pady=50)

            ctk.CTkLabel(
                clean_box, text="✨ Nenhum atraso ou urgência pendente!",
                font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
                text_color=COLORS["success"]
            ).pack(pady=(0, 4))
            ctk.CTkLabel(
                clean_box, text="Todas as obras estão dentro do prazo estipulado.",
                font=ctk.CTkFont(family=FONT_FAMILY, size=11), text_color=COLORS["text_muted"]
            ).pack()
        else:
            for ct in filtered_crit:
                self._render_critical_card(ct)

    def _render_obra_card(self, om: ObraMetrics):
        card = ctk.CTkFrame(
            self.obras_scroll,
            corner_radius=10,
            fg_color=COLORS["card_inner_bg"],
            border_width=1,
            border_color=COLORS["card_border"]
        )
        card.pack(fill="x", pady=5, padx=2)
        card.grid_columnconfigure(0, weight=1)

        # Topo: Nome da Obra + Percentual
        top_line = ctk.CTkFrame(card, fg_color="transparent")
        top_line.pack(fill="x", padx=14, pady=(12, 4))

        ctk.CTkLabel(
            top_line, text=f"🏗️ {om.obra}",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(side="left")

        # Badge de Percentual
        perc_badge = ctk.CTkFrame(
            top_line, corner_radius=6,
            fg_color=COLORS["primary_subtle"],
            border_width=1, border_color=COLORS["primary_border"]
        )
        perc_badge.pack(side="right")

        ctk.CTkLabel(
            perc_badge, text=f"{om.percentual}% Avanço",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            text_color=COLORS["primary"]
        ).pack(padx=8, pady=2)

        # Barra de Progresso Arredondada
        p_bar = ctk.CTkProgressBar(card, height=8, corner_radius=4)
        p_bar.pack(fill="x", padx=14, pady=(0, 8))
        p_bar.set(om.percentual / 100.0)

        # Chips de Métricas Inferiores
        chips_line = ctk.CTkFrame(card, fg_color="transparent")
        chips_line.pack(fill="x", padx=14, pady=(0, 10))

        counts = f"Total: {om.total}  •  ✅ {om.concluidas}  •  ⏳ {om.em_andamento}"
        ctk.CTkLabel(
            chips_line, text=counts,
            font=ctk.CTkFont(family=FONT_FAMILY, size=11), text_color=COLORS["text_muted"]
        ).pack(side="left")

        if om.atrasadas > 0:
            overdue_chip = ctk.CTkLabel(
                chips_line, text=f"🚨 {om.atrasadas} Atrasada(s)",
                font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
                text_color=COLORS["danger"]
            )
            overdue_chip.pack(side="right")

    def _render_critical_card(self, task: Task):
        crit_card = ctk.CTkFrame(
            self.crit_scroll,
            corner_radius=10,
            fg_color=COLORS["danger_subtle"],
            border_width=1,
            border_color=COLORS["danger_border"]
        )
        crit_card.pack(fill="x", pady=4, padx=2)

        # Topo
        top_row = ctk.CTkFrame(crit_card, fg_color="transparent")
        top_row.pack(fill="x", padx=10, pady=(8, 2))

        ctk.CTkLabel(
            top_row, text=task.name,
            font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"),
            text_color=COLORS["text_primary"],
            anchor="w"
        ).pack(side="left", fill="x", expand=True)

        # Badge SLA
        if task.is_overdue:
            days = abs(task.days_remaining() or 0)
            badge_text = f"Atrasada {days}d"
        else:
            badge_text = task.priority.value

        ctk.CTkLabel(
            top_row, text=badge_text,
            font=ctk.CTkFont(family=FONT_FAMILY, size=10, weight="bold"),
            text_color=COLORS["danger"]
        ).pack(side="right")

        sub = f"🏗️ {task.obra}   •   👤 {task.responsible}   •   Prazo: {task.end_date_br}"
        ctk.CTkLabel(
            crit_card, text=sub,
            font=ctk.CTkFont(family=FONT_FAMILY, size=10),
            text_color=COLORS["text_secondary"],
            anchor="w"
        ).pack(fill="x", padx=10, pady=(0, 8))
