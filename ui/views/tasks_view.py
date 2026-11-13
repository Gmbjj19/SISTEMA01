import customtkinter as ctk
from tkinter import messagebox, filedialog
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional, List, Dict

from ui.theme import FONT_FAMILY, COLORS, STATUS_COLORS
from ui.components.task_card import TaskCard
from ui.components.kanban_card import KanbanCard
from ui.components.filter_bar import FilterBar
from ui.dialogs.task_dialog import TaskDialog
from services.task_service import TaskService
from services.export_service import ExportService
from models.task import Task
from models.enums import TaskStatus

class TasksView(ctk.CTkFrame):
    """Visão operacional avançada suportando Lista Detalhada e Quadro Visual Kanban."""
    def __init__(
        self,
        master,
        task_service: TaskService,
        export_service: ExportService,
        on_data_changed: Optional[Callable[[], None]] = None,
        **kwargs
    ):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.task_service = task_service
        self.export_service = export_service
        self.on_data_changed = on_data_changed
        self.current_view_mode = "📋 Lista"

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._build_header()
        self._build_filters()
        self._build_containers()

        self.refresh_tasks()

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=25, pady=(20, 10))
        header.grid_columnconfigure(0, weight=1)

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.grid(row=0, column=0, sticky="w")

        title = ctk.CTkLabel(
            title_box,
            text="📋 Gestão de Tarefas & Cronograma",
            font=ctk.CTkFont(family=FONT_FAMILY, size=24, weight="bold"),
            text_color=COLORS["text_primary"]
        )
        title.pack(anchor="w")

        self.counter_label = ctk.CTkLabel(
            title_box,
            text="Carregando tarefas...",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color=COLORS["text_secondary"]
        )
        self.counter_label.pack(anchor="w")

        # Botões de Ação Superiores
        actions_box = ctk.CTkFrame(header, fg_color="transparent")
        actions_box.grid(row=0, column=1, sticky="e")

        # Botão Nova Tarefa
        new_task_btn = ctk.CTkButton(
            actions_box,
            text="+ Nova Tarefa",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"),
            height=38,
            width=140,
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            command=self.open_new_task_dialog
        )
        new_task_btn.pack(side="left", padx=(0, 8))

        # Botão Exportar Excel
        export_btn = ctk.CTkButton(
            actions_box,
            text="📊 Exportar Excel",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"),
            height=38,
            width=140,
            fg_color=COLORS["success"],
            hover_color=COLORS["success_hover"],
            command=self.export_to_excel
        )
        export_btn.pack(side="left", padx=(0, 8))

        # Botão Limpar Concluídas
        clear_btn = ctk.CTkButton(
            actions_box,
            text="Limpar Concluídas",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            height=38,
            width=135,
            fg_color="transparent",
            border_width=1,
            border_color=COLORS["card_border"],
            text_color=COLORS["danger"],
            hover_color=COLORS["danger_subtle"],
            command=self.clear_completed_tasks
        )
        clear_btn.pack(side="left")

    def _build_filters(self):
        obras = self.task_service.get_obras()
        self.filter_bar = FilterBar(
            self,
            on_filter_changed=self.refresh_tasks,
            on_view_mode_changed=self._handle_view_mode_change,
            obras_list=obras
        )
        self.filter_bar.grid(row=1, column=0, sticky="ew", padx=25, pady=(0, 10))

    def _build_containers(self):
        # 1. Container para Modo Lista
        self.list_container = ctk.CTkScrollableFrame(
            self,
            corner_radius=14,
            border_width=1,
            fg_color=COLORS["sidebar_bg"],
            border_color=COLORS["card_border"]
        )
        self.list_container.grid(row=2, column=0, sticky="nsew", padx=25, pady=(0, 20))
        self.list_container.grid_columnconfigure(0, weight=1)

        # 2. Container para Modo Kanban (Grid de 4 Colunas)
        self.kanban_container = ctk.CTkFrame(self, fg_color="transparent")
        for i in range(4):
            self.kanban_container.grid_columnconfigure(i, weight=1, uniform="kanban")
        self.kanban_container.grid_rowconfigure(0, weight=1)

        self._init_kanban_columns()

    def _init_kanban_columns(self):
        self.kanban_scrolls: Dict[TaskStatus, ctk.CTkScrollableFrame] = {}
        self.kanban_badges: Dict[TaskStatus, ctk.CTkLabel] = {}

        cols_data = [
            (TaskStatus.PENDENTE, "📌 Pendente", COLORS["text_secondary"]),
            (TaskStatus.EM_ANDAMENTO, "⏳ Em Andamento", COLORS["info"]),
            (TaskStatus.BLOQUEADA, "⛔ Bloqueada", COLORS["purple"]),
            (TaskStatus.CONCLUIDA, "✅ Concluída", COLORS["success"])
        ]

        for idx, (status, col_title, col_accent) in enumerate(cols_data):
            col_frame = ctk.CTkFrame(
                self.kanban_container,
                corner_radius=12,
                border_width=1,
                fg_color=COLORS["card_bg"],
                border_color=COLORS["card_border"]
            )
            col_frame.grid(row=0, column=idx, sticky="nsew", padx=4, pady=(0, 20))
            col_frame.grid_rowconfigure(1, weight=1)
            col_frame.grid_columnconfigure(0, weight=1)

            # Cabeçalho da Coluna
            c_header = ctk.CTkFrame(col_frame, fg_color="transparent")
            c_header.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 8))

            ctk.CTkLabel(
                c_header, text=col_title,
                font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
                text_color=col_accent
            ).pack(side="left")

            count_badge = ctk.CTkLabel(
                c_header, text="0",
                font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
                text_color=COLORS["text_muted"]
            )
            count_badge.pack(side="right")
            self.kanban_badges[status] = count_badge

            # Scroll da Coluna
            c_scroll = ctk.CTkScrollableFrame(col_frame, fg_color="transparent")
            c_scroll.grid(row=1, column=0, sticky="nsew", padx=4, pady=(0, 8))
            self.kanban_scrolls[status] = c_scroll

    def _handle_view_mode_change(self, mode: str):
        self.current_view_mode = mode
        if mode == "📌 Kanban":
            self.list_container.grid_forget()
            self.kanban_container.grid(row=2, column=0, sticky="nsew", padx=25, pady=(0, 0))
        else:
            self.kanban_container.grid_forget()
            self.list_container.grid(row=2, column=0, sticky="nsew", padx=25, pady=(0, 20))
        self.refresh_tasks()

    def refresh_tasks(self):
        """Consulta tarefas filtradas e renderiza na view ativa (Lista ou Kanban)."""
        filter_params = self.filter_bar.get_filter_values()
        tasks = self.task_service.list_tasks(**filter_params)

        self.filter_bar.update_obras(self.task_service.get_obras())

        total = len(tasks)
        completed_count = sum(1 for t in tasks if t.is_completed)

        self.counter_label.configure(
            text=f"Exibindo {total} tarefas ({completed_count} concluídas • {total - completed_count} em aberto)"
        )

        if self.current_view_mode == "📌 Kanban":
            self._render_kanban_view(tasks)
        else:
            self._render_list_view(tasks)

    def _render_list_view(self, tasks: List[Task]):
        for child in self.list_container.winfo_children():
            child.destroy()

        if not tasks:
            empty_frame = ctk.CTkFrame(self.list_container, fg_color="transparent")
            empty_frame.pack(pady=70)

            ctk.CTkLabel(
                empty_frame, text="🔍 Nenhuma tarefa encontrada",
                font=ctk.CTkFont(family=FONT_FAMILY, size=16, weight="bold"),
                text_color=COLORS["text_secondary"]
            ).pack(pady=(0, 4))
            ctk.CTkLabel(
                empty_frame, text="Ajuste os filtros ou cadastre uma nova atividade de obra.",
                font=ctk.CTkFont(family=FONT_FAMILY, size=12), text_color=COLORS["text_muted"]
            ).pack()
            return

        for task in tasks:
            card = TaskCard(
                self.list_container,
                task=task,
                on_toggle_complete=self.handle_toggle_complete,
                on_edit=self.open_edit_task_dialog,
                on_delete=self.handle_delete_task,
                on_status_change=self.handle_status_change
            )
            card.pack(fill="x", pady=4, padx=2)

    def _render_kanban_view(self, tasks: List[Task]):
        for status, scroll in self.kanban_scrolls.items():
            for child in scroll.winfo_children():
                child.destroy()

        counts = {s: 0 for s in TaskStatus}

        for task in tasks:
            counts[task.status] += 1
            col_scroll = self.kanban_scrolls.get(task.status)
            if col_scroll:
                k_card = KanbanCard(
                    col_scroll,
                    task=task,
                    on_move_next=self._kanban_move_next,
                    on_move_prev=self._kanban_move_prev,
                    on_edit=self.open_edit_task_dialog
                )
                k_card.pack(fill="x", pady=4, padx=2)

        for status, badge in self.kanban_badges.items():
            badge.configure(text=str(counts[status]))

    def _kanban_move_next(self, task: Task):
        transitions = {
            TaskStatus.PENDENTE: TaskStatus.EM_ANDAMENTO,
            TaskStatus.EM_ANDAMENTO: TaskStatus.CONCLUIDA,
            TaskStatus.BLOQUEADA: TaskStatus.EM_ANDAMENTO
        }
        next_st = transitions.get(task.status)
        if next_st:
            self.task_service.change_status(task.id, next_st)
            self.refresh_tasks()
            if self.on_data_changed:
                self.on_data_changed()

    def _kanban_move_prev(self, task: Task):
        transitions = {
            TaskStatus.EM_ANDAMENTO: TaskStatus.PENDENTE,
            TaskStatus.BLOQUEADA: TaskStatus.PENDENTE,
            TaskStatus.CONCLUIDA: TaskStatus.EM_ANDAMENTO
        }
        prev_st = transitions.get(task.status)
        if prev_st:
            self.task_service.change_status(task.id, prev_st)
            self.refresh_tasks()
            if self.on_data_changed:
                self.on_data_changed()

    def open_new_task_dialog(self):
        obras = self.task_service.get_obras()
        resps = self.task_service.get_responsibles()
        TaskDialog(
            self.winfo_toplevel(),
            on_save_callback=self._handle_save_dialog,
            task_to_edit=None,
            obras_suggestions=obras,
            responsibles_suggestions=resps
        )

    def open_edit_task_dialog(self, task: Task):
        obras = self.task_service.get_obras()
        resps = self.task_service.get_responsibles()
        TaskDialog(
            self.winfo_toplevel(),
            on_save_callback=self._handle_save_dialog,
            task_to_edit=task,
            obras_suggestions=obras,
            responsibles_suggestions=resps
        )

    def _handle_save_dialog(self, payload: dict, task_id: Optional[int], dialog: TaskDialog):
        if task_id is None:
            created, err = self.task_service.create_task(payload)
            if err:
                dialog.show_error(err)
                return
        else:
            updated, err = self.task_service.update_task(task_id, payload)
            if err:
                dialog.show_error(err)
                return

        dialog.destroy()
        self.refresh_tasks()
        if self.on_data_changed:
            self.on_data_changed()

    def handle_toggle_complete(self, task: Task):
        self.task_service.toggle_completed(task.id)
        self.refresh_tasks()
        if self.on_data_changed:
            self.on_data_changed()

    def handle_status_change(self, task: Task, new_status: TaskStatus):
        self.task_service.change_status(task.id, new_status)
        self.refresh_tasks()
        if self.on_data_changed:
            self.on_data_changed()

    def handle_delete_task(self, task: Task):
        self.task_service.delete_task(task.id)
        self.refresh_tasks()
        if self.on_data_changed:
            self.on_data_changed()

    def clear_completed_tasks(self):
        confirm = messagebox.askyesno(
            "Limpar Concluídas",
            "Deseja remover todas as tarefas concluídas do sistema?",
            parent=self.winfo_toplevel()
        )
        if confirm:
            deleted_count = self.task_service.delete_completed()
            messagebox.showinfo("Sucesso", f"{deleted_count} tarefas concluídas foram removidas.", parent=self.winfo_toplevel())
            self.refresh_tasks()
            if self.on_data_changed:
                self.on_data_changed()

    def export_to_excel(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"Relatorio_Obras_{timestamp}.xlsx"

        file_path = filedialog.asksaveasfilename(
            parent=self.winfo_toplevel(),
            defaultextension=".xlsx",
            initialfile=default_name,
            filetypes=[("Arquivos Excel", "*.xlsx"), ("Todos os Arquivos", "*.*")]
        )

        if not file_path:
            return

        try:
            saved_path = self.export_service.export_tasks_to_excel(Path(file_path))
            messagebox.showinfo(
                "Exportação Concluída",
                f"Relatório exportado com sucesso!\n\nSalvo em:\n{saved_path}",
                parent=self.winfo_toplevel()
            )
        except Exception as e:
            messagebox.showerror("Erro na Exportação", f"Falha ao gerar planilha:\n{e}", parent=self.winfo_toplevel())
