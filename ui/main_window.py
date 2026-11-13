import customtkinter as ctk
from typing import Optional
from pathlib import Path

from config import APP_TITLE, APP_VERSION, LOGGER
from ui.theme import FONT_FAMILY, COLORS
from ui.components.toast import ToastManager
from ui.views.dashboard_view import DashboardView
from ui.views.tasks_view import TasksView
from ui.views.quantitativo_view import QuantitativoView

from services.task_service import TaskService
from services.metrics_service import MetricsService
from services.export_service import ExportService
from services.quantitativo_service import QuantitativoService

from repositories.task_repository import TaskRepository
from repositories.quantitativo_repository import QuantitativoRepository

class MainWindow(ctk.CTk):
    """Janela principal moderna com visual de aplicativo desktop, navegação SPA e alta responsividade."""
    def __init__(self):
        super().__init__()

        # Configurações da Janela Responsiva
        self.title(f"{APP_TITLE} • {APP_VERSION}")
        self.geometry("1240x820")
        self.minsize(1020, 680)

        # Injeção de Dependências
        self.task_repo = TaskRepository()
        self.quant_repo = QuantitativoRepository()

        self.task_service = TaskService(self.task_repo)
        self.metrics_service = MetricsService(self.task_repo)
        self.export_service = ExportService(self.task_repo)
        self.quant_service = QuantitativoService(self.quant_repo)

        # Gerenciador de Notificações Toast Flutuantes
        self.toast_manager = ToastManager(self)

        # Layout Principal (Grid 1x2: Sidebar Fixa + Workspace Responsivo)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.current_view_name = "dashboard"

        self._build_sidebar()
        self._build_workspace()
        self._bind_shortcuts()

        # Inicia na aba Dashboard
        self.switch_view("dashboard")
        self.update_sidebar_badges()

    def notify(self, title: str, message: str, toast_type: str = "success"):
        """Dispara uma notificação toast animada no canto superior da tela."""
        self.toast_manager.show(title=title, message=message, toast_type=toast_type)

    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(
            self,
            width=235,
            corner_radius=0,
            fg_color=COLORS["sidebar_bg"],
            border_width=1,
            border_color=COLORS["card_border"]
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_rowconfigure(4, weight=1)

        # Marca e Identidade Visual Superior
        brand_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand_frame.grid(row=0, column=0, sticky="ew", padx=16, pady=(24, 16))

        logo_box = ctk.CTkFrame(
            brand_frame, width=38, height=38, corner_radius=10,
            fg_color="#064e3b",
        )
        logo_box.pack(side="left", padx=(0, 10))
        logo_box.pack_propagate(False)

        ctk.CTkLabel(
            logo_box, text="🏗️", font=ctk.CTkFont(family=FONT_FAMILY, size=18)
        ).pack(expand=True)

        text_brand = ctk.CTkFrame(brand_frame, fg_color="transparent")
        text_brand.pack(side="left")

        ctk.CTkLabel(
            text_brand, text="OBRAS PRO",
            font=ctk.CTkFont(family=FONT_FAMILY, size=15, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w")

        ctk.CTkLabel(
            text_brand, text="ENGENHARIA & GESTÃO",
            font=ctk.CTkFont(family=FONT_FAMILY, size=9, weight="bold"),
            text_color=("#064e3b", "#10b981")
        ).pack(anchor="w")

        # Divisor Sutil
        sep1 = ctk.CTkFrame(self.sidebar, height=1, fg_color=COLORS["card_border"])
        sep1.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 16))

        # Navegação Principal
        nav_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        nav_frame.grid(row=2, column=0, sticky="ew", padx=12)

        # 1. Painel Executivo
        self.btn_dashboard = ctk.CTkButton(
            nav_frame,
            text=" 📊  Painel Executivo",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
            height=42,
            anchor="w",
            corner_radius=8,
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            command=lambda: self.switch_view("dashboard")
        )
        self.btn_dashboard.pack(fill="x", pady=(0, 6))

        # 2. Gerenciar Tarefas
        self.btn_tasks = ctk.CTkButton(
            nav_frame,
            text=" 📋  Gerenciar Tarefas",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
            height=42,
            anchor="w",
            corner_radius=8,
            fg_color="transparent",
            text_color=COLORS["text_primary"],
            hover_color=COLORS["primary_subtle"],
            command=lambda: self.switch_view("tasks")
        )
        self.btn_tasks.pack(fill="x", pady=(0, 6))

        # 3. Quantitativos & Concreto (MÓDULO AVANÇADO CONFORME PROJETO)
        self.btn_concrete = ctk.CTkButton(
            nav_frame,
            text=" 🏗️  Concreto & Formas",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
            height=42,
            anchor="w",
            corner_radius=8,
            fg_color="transparent",
            text_color=COLORS["text_primary"],
            hover_color=COLORS["primary_subtle"],
            command=lambda: self.switch_view("concrete")
        )
        self.btn_concrete.pack(fill="x")

        # Atalhos Rápidos Informativos
        shortcuts_box = ctk.CTkFrame(
            self.sidebar, corner_radius=8,
            fg_color=COLORS["card_inner_bg"],
            border_width=1, border_color=COLORS["card_border"]
        )
        shortcuts_box.grid(row=3, column=0, sticky="ew", padx=14, pady=16)

        ctk.CTkLabel(
            shortcuts_box, text="⚡ Atalhos de App",
            font=ctk.CTkFont(family=FONT_FAMILY, size=10, weight="bold"),
            text_color=COLORS["text_secondary"]
        ).pack(anchor="w", padx=10, pady=(8, 2))

        ctk.CTkLabel(
            shortcuts_box,
            text="Ctrl+N : Nova Tarefa\nCtrl+Q : Novo Quantitativo\nCtrl+E : Exportar Excel\nF5 : Recarregar",
            font=ctk.CTkFont(family=FONT_FAMILY, size=10),
            text_color=COLORS["text_muted"], justify="left"
        ).pack(anchor="w", padx=10, pady=(0, 8))

        # Rodapé da Sidebar (Tema & Status)
        bottom_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        bottom_frame.grid(row=5, column=0, sticky="ew", padx=16, pady=20)

        # Alternador de Tema
        self.theme_label = ctk.CTkLabel(
            bottom_frame, text="Aparência Visual:",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            text_color=COLORS["text_secondary"]
        )
        self.theme_label.pack(anchor="w", pady=(0, 4))

        self.theme_switch = ctk.CTkSegmentedButton(
            bottom_frame,
            values=["Escuro", "Claro"],
            command=self._handle_theme_change
        )
        self.theme_switch.set("Escuro" if ctk.get_appearance_mode() == "Dark" else "Claro")
        self.theme_switch.pack(fill="x", pady=(0, 10))

        # Status do Banco
        db_badge = ctk.CTkLabel(
            bottom_frame,
            text="🟢 SQLite WAL • Modo App Ativo",
            font=ctk.CTkFont(family=FONT_FAMILY, size=10, weight="bold"),
            text_color=COLORS["success"]
        )
        db_badge.pack(anchor="w")

    def _build_workspace(self):
        self.main_container = ctk.CTkFrame(self, fg_color=COLORS["main_bg"], corner_radius=0)
        self.main_container.grid(row=0, column=1, sticky="nsew")
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(0, weight=1)

        # Instanciação das Telas
        self.dashboard_view = DashboardView(
            self.main_container,
            metrics_service=self.metrics_service,
            task_service=self.task_service,
            on_navigate_to_tasks=lambda: self.switch_view("tasks")
        )

        self.tasks_view = TasksView(
            self.main_container,
            task_service=self.task_service,
            export_service=self.export_service,
            on_data_changed=self._on_data_changed
        )

        self.quantitativo_view = QuantitativoView(
            self.main_container,
            quantitativo_service=self.quant_service,
            task_service=self.task_service,
            on_notify=self.notify
        )

    def _bind_shortcuts(self):
        self.bind("<Control-n>", lambda e: self.tasks_view.open_new_task_dialog())
        self.bind("<Control-N>", lambda e: self.tasks_view.open_new_task_dialog())
        self.bind("<Control-q>", lambda e: self._shortcut_novo_quantitativo())
        self.bind("<Control-Q>", lambda e: self._shortcut_novo_quantitativo())
        self.bind("<Control-e>", lambda e: self.tasks_view.export_to_excel())
        self.bind("<Control-E>", lambda e: self.tasks_view.export_to_excel())
        self.bind("<F5>", lambda e: self._on_data_changed())

    def _shortcut_novo_quantitativo(self):
        self.switch_view("concrete")
        self.quantitativo_view.show_create_view()

    def switch_view(self, view_name: str):
        self.current_view_name = view_name

        # Esconder todas as views
        self.dashboard_view.grid_forget()
        self.tasks_view.grid_forget()
        self.quantitativo_view.grid_forget()

        # Resetar estilos de botão da sidebar
        for btn in (self.btn_dashboard, self.btn_tasks, self.btn_concrete):
            btn.configure(fg_color="transparent", text_color=COLORS["text_primary"])

        if view_name == "dashboard":
            self.dashboard_view.grid(row=0, column=0, sticky="nsew")
            self.dashboard_view.refresh()
            self.btn_dashboard.configure(fg_color=COLORS["primary"], text_color="#ffffff")
        elif view_name == "tasks":
            self.tasks_view.grid(row=0, column=0, sticky="nsew")
            self.tasks_view.refresh_tasks()
            self.btn_tasks.configure(fg_color=COLORS["primary"], text_color="#ffffff")
        elif view_name == "concrete":
            self.quantitativo_view.grid(row=0, column=0, sticky="nsew")
            if not self.quantitativo_view.active_quantitativo:
                self.quantitativo_view.show_list_view()
            self.btn_concrete.configure(fg_color=("#064e3b", "#10b981"), text_color="#ffffff")

        self.update_sidebar_badges()

    def update_sidebar_badges(self):
        metrics = self.metrics_service.get_dashboard_metrics()
        overdue_note = f" 🚨 {metrics.atrasadas}" if metrics.atrasadas > 0 else ""
        self.btn_dashboard.configure(text=f" 📊  Painel Executivo{overdue_note}")
        self.btn_tasks.configure(text=f" 📋  Gerenciar Tarefas ({metrics.total})")

        q_stats = self.quant_service.get_stats()
        self.btn_concrete.configure(text=f" 🏗️  Concreto & Formas ({q_stats['total_quantitativos']})")

    def _on_data_changed(self):
        self.update_sidebar_badges()
        self.dashboard_view.refresh()
        self.tasks_view.refresh_tasks()
        self.notify("Sincronizado", "Dados e indicadores atualizados com sucesso.", "info")

    def _handle_theme_change(self, mode: str):
        ctk_mode = "Dark" if mode == "Escuro" else "Light"
        ctk.set_appearance_mode(ctk_mode)
