import customtkinter as ctk
from datetime import datetime, date, timedelta
from typing import Callable, Optional, List, Dict, Any

from ui.theme import FONT_FAMILY, COLORS, PRIORITY_COLORS
from models.task import Task
from models.enums import TaskPriority, TaskStatus

class TaskDialog(ctk.CTkToplevel):
    """Janela modal para Criação e Edição Completa de Tarefas com atalhos de data e validação."""
    def __init__(
        self,
        master,
        on_save_callback: Callable[[Dict[str, Any], Optional[int]], None],
        task_to_edit: Optional[Task] = None,
        obras_suggestions: Optional[List[str]] = None,
        responsibles_suggestions: Optional[List[str]] = None
    ):
        super().__init__(master)

        self.on_save_callback = on_save_callback
        self.task_to_edit = task_to_edit
        self.is_edit_mode = task_to_edit is not None

        # Configurações da Janela Responsiva
        mode_title = f"Editar Tarefa #{task_to_edit.id}" if self.is_edit_mode else "Nova Tarefa de Obra"
        self.title(f"🏗️ {mode_title}")
        self.minsize(480, 500)
        self.resizable(True, True)
        
        # Garante foco modal
        self.transient(master)
        self.grab_set()

        self._center_window()
        self._build_ui(obras_suggestions or [], responsibles_suggestions or [])

    def _center_window(self):
        self.update_idletasks()
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        width = 540
        height = min(710, screen_h - 70)
        x = max(0, (screen_w // 2) - (width // 2))
        y = max(0, (screen_h // 2) - (height // 2) - 20)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _build_ui(self, obras_list: List[str], resp_list: List[str]):
        # Cabeçalho Elegante
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=24, pady=(16, 8))

        header_text = f"✏️ Editar Tarefa #{self.task_to_edit.id}" if self.is_edit_mode else "📋 Nova Tarefa de Canteiro"
        title_label = ctk.CTkLabel(
            header_frame,
            text=header_text,
            font=ctk.CTkFont(family=FONT_FAMILY, size=18, weight="bold"),
            text_color=COLORS["text_primary"]
        )
        title_label.pack(anchor="w")

        sub_label = ctk.CTkLabel(
            header_frame,
            text="Preencha as informações técnicas e cronograma da atividade",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=COLORS["text_secondary"]
        )
        sub_label.pack(anchor="w")

        # Container do Formulário Scrollable (Garante exibição perfeita em qualquer resolução)
        form_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        form_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        # 1. Nome da Tarefa
        ctk.CTkLabel(
            form_frame, text="Nome da Tarefa / Atividade *",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            text_color=COLORS["text_secondary"]
        ).pack(anchor="w")
        self.name_entry = ctk.CTkEntry(
            form_frame, placeholder_text="Ex: Armação e concretagem de vigas do 3º pavimento", height=36
        )
        self.name_entry.pack(fill="x", pady=(2, 10))

        # 2. Obra e Responsável (Lado a Lado)
        row1 = ctk.CTkFrame(form_frame, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 10))
        row1.grid_columnconfigure(0, weight=1)
        row1.grid_columnconfigure(1, weight=1)

        # Obra
        col_obra = ctk.CTkFrame(row1, fg_color="transparent")
        col_obra.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ctk.CTkLabel(
            col_obra, text="Obra / Canteiro *",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            text_color=COLORS["text_secondary"]
        ).pack(anchor="w")
        self.obra_combo = ctk.CTkComboBox(
            col_obra, values=obras_list if obras_list else ["Geral", "Residencial Vista Verde", "Torre Alpha"],
            height=36
        )
        self.obra_combo.pack(fill="x", pady=(2, 0))

        # Responsável
        col_resp = ctk.CTkFrame(row1, fg_color="transparent")
        col_resp.grid(row=0, column=1, sticky="ew", padx=(6, 0))
        ctk.CTkLabel(
            col_resp, text="Responsável *",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            text_color=COLORS["text_secondary"]
        ).pack(anchor="w")
        self.resp_combo = ctk.CTkComboBox(
            col_resp, values=resp_list if resp_list else ["Eng. Carlos", "Encarregado Gil", "Mestre João"],
            height=36
        )
        self.resp_combo.pack(fill="x", pady=(2, 0))

        # 3. Cronograma (Datas de Início e Término + Atalhos Rápidos)
        dates_header_row = ctk.CTkFrame(form_frame, fg_color="transparent")
        dates_header_row.pack(fill="x", pady=(0, 2))

        ctk.CTkLabel(
            dates_header_row, text="Cronograma de Execução *",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            text_color=COLORS["text_secondary"]
        ).pack(side="left")

        # Atalhos de Prazo
        shortcuts_frame = ctk.CTkFrame(dates_header_row, fg_color="transparent")
        shortcuts_frame.pack(side="right")

        for label, days in [("+7 dias", 7), ("+15 dias", 15), ("+30 dias", 30)]:
            btn = ctk.CTkButton(
                shortcuts_frame, text=label, width=54, height=20,
                font=ctk.CTkFont(family=FONT_FAMILY, size=9, weight="bold"),
                fg_color=COLORS["card_inner_bg"], text_color=COLORS["primary"],
                hover_color=COLORS["primary_subtle"],
                command=lambda d=days: self._set_end_date_offset(d)
            )
            btn.pack(side="left", padx=2)

        # Campos de Data
        row_dates = ctk.CTkFrame(form_frame, fg_color="transparent")
        row_dates.pack(fill="x", pady=(0, 10))
        row_dates.grid_columnconfigure(0, weight=1)
        row_dates.grid_columnconfigure(1, weight=1)

        # Data Início
        col_start = ctk.CTkFrame(row_dates, fg_color="transparent")
        col_start.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self.start_entry = ctk.CTkEntry(col_start, placeholder_text="DD/MM/AAAA", height=36)
        self.start_entry.pack(fill="x")

        # Data Término
        col_end = ctk.CTkFrame(row_dates, fg_color="transparent")
        col_end.grid(row=0, column=1, sticky="ew", padx=(6, 0))
        self.end_entry = ctk.CTkEntry(col_end, placeholder_text="DD/MM/AAAA", height=36)
        self.end_entry.pack(fill="x")

        # 4. Prioridade e Status
        row_prio = ctk.CTkFrame(form_frame, fg_color="transparent")
        row_prio.pack(fill="x", pady=(0, 10))
        row_prio.grid_columnconfigure(0, weight=1)
        row_prio.grid_columnconfigure(1, weight=1)

        # Prioridade
        col_prio = ctk.CTkFrame(row_prio, fg_color="transparent")
        col_prio.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ctk.CTkLabel(
            col_prio, text="Prioridade",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            text_color=COLORS["text_secondary"]
        ).pack(anchor="w")
        self.priority_var = ctk.StringVar(value="Média")
        self.priority_menu = ctk.CTkOptionMenu(
            col_prio, values=TaskPriority.list_values(), variable=self.priority_var, height=36
        )
        self.priority_menu.pack(fill="x", pady=(2, 0))

        # Status
        col_status = ctk.CTkFrame(row_prio, fg_color="transparent")
        col_status.grid(row=0, column=1, sticky="ew", padx=(6, 0))
        ctk.CTkLabel(
            col_status, text="Status",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            text_color=COLORS["text_secondary"]
        ).pack(anchor="w")
        self.status_var = ctk.StringVar(value="Pendente")
        self.status_menu = ctk.CTkOptionMenu(
            col_status, values=TaskStatus.list_values(), variable=self.status_var, height=36
        )
        self.status_menu.pack(fill="x", pady=(2, 0))

        # 5. Descrição / Observações Técnicas
        ctk.CTkLabel(
            form_frame, text="Observações Técnicas / Especificações",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            text_color=COLORS["text_secondary"]
        ).pack(anchor="w")
        self.desc_text = ctk.CTkTextbox(form_frame, height=80, corner_radius=8)
        self.desc_text.pack(fill="x", pady=(2, 10))

        # Banner de Erro Inline
        self.error_label = ctk.CTkLabel(
            form_frame, text="",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            text_color=COLORS["danger"]
        )
        self.error_label.pack(fill="x", pady=(0, 6))

        # Botão Salvar
        btn_text = "Salvar Alterações" if self.is_edit_mode else "Cadastrar Tarefa"
        self.save_btn = ctk.CTkButton(
            self,
            text=btn_text,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
            height=42,
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            command=self._handle_save
        )
        self.save_btn.pack(fill="x", padx=28, pady=(0, 20))

        # Preenchimento inicial
        if self.is_edit_mode and self.task_to_edit:
            self._fill_existing_data(self.task_to_edit)
        else:
            today_str = date.today().strftime("%d/%m/%Y")
            self.start_entry.insert(0, today_str)
            # Default término para +7 dias
            future_str = (date.today() + timedelta(days=7)).strftime("%d/%m/%Y")
            self.end_entry.insert(0, future_str)

    def _set_end_date_offset(self, days: int):
        s_text = self.start_entry.get().strip()
        base_d = date.today()
        if s_text:
            try:
                base_d = datetime.strptime(s_text, "%d/%m/%Y").date()
            except ValueError:
                pass
        target = base_d + timedelta(days=days)
        self.end_entry.delete(0, "end")
        self.end_entry.insert(0, target.strftime("%d/%m/%Y"))

    def _fill_existing_data(self, task: Task):
        self.name_entry.insert(0, task.name)
        self.obra_combo.set(task.obra)
        self.resp_combo.set(task.responsible)
        if task.start_date:
            self.start_entry.insert(0, task.start_date_br)
        if task.end_date:
            self.end_entry.insert(0, task.end_date_br)
        self.priority_var.set(task.priority.value)
        self.status_var.set(task.status.value)
        if task.description:
            self.desc_text.insert("1.0", task.description)

    def _handle_save(self):
        payload = {
            "name": self.name_entry.get().strip(),
            "obra": self.obra_combo.get().strip(),
            "responsible": self.resp_combo.get().strip(),
            "start_date": self.start_entry.get().strip(),
            "end_date": self.end_entry.get().strip(),
            "priority": self.priority_var.get(),
            "status": self.status_var.get(),
            "description": self.desc_text.get("1.0", "end").strip()
        }

        task_id = self.task_to_edit.id if self.is_edit_mode else None
        self.on_save_callback(payload, task_id, self)

    def show_error(self, message: str):
        self.error_label.configure(text=f"⚠️ {message}")
