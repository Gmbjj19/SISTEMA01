import customtkinter as ctk
from tkinter import messagebox
from typing import Callable, Optional

from ui.theme import FONT_FAMILY, COLORS, PRIORITY_COLORS, STATUS_COLORS, DEADLINE_COLORS, get_initials
from models.task import Task
from models.enums import TaskStatus, TaskPriority, DeadlineStatus

class TaskCard(ctk.CTkFrame):
    """Card avançado com design obsidian, avatar de responsável, chips de SLA e ações rápidas."""
    def __init__(
        self,
        master,
        task: Task,
        on_toggle_complete: Optional[Callable[[Task], None]] = None,
        on_edit: Optional[Callable[[Task], None]] = None,
        on_delete: Optional[Callable[[Task], None]] = None,
        on_status_change: Optional[Callable[[Task, TaskStatus], None]] = None,
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

        self.task = task
        self.on_toggle_complete = on_toggle_complete
        self.on_edit = on_edit
        self.on_delete = on_delete
        self.on_status_change = on_status_change

        self.grid_columnconfigure(1, weight=1)

        # Barra lateral colorida indicativa
        bar_color = self._get_status_bar_color()
        self.status_bar = ctk.CTkFrame(self, width=5, corner_radius=3, fg_color=bar_color)
        self.status_bar.grid(row=0, column=0, rowspan=4, sticky="ns", padx=(4, 10), pady=6)

        # Container Central de Informações
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.grid(row=0, column=1, sticky="nsew", padx=(0, 10), pady=10)
        content_frame.grid_columnconfigure(0, weight=1)

        # LINHA 1: Checkbox + Tags Inteligentes
        top_row = ctk.CTkFrame(content_frame, fg_color="transparent")
        top_row.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        top_row.grid_columnconfigure(0, weight=1)

        title_color = COLORS["text_muted"] if self.task.is_completed else COLORS["text_primary"]
        self.checkbox = ctk.CTkCheckBox(
            top_row,
            text=self.task.name,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
            text_color=title_color,
            corner_radius=6,
            command=self._handle_toggle_complete
        )
        if self.task.is_completed:
            self.checkbox.select()
        self.checkbox.grid(row=0, column=0, sticky="w")

        # Tags à Direita
        tags_box = ctk.CTkFrame(top_row, fg_color="transparent")
        tags_box.grid(row=0, column=1, sticky="e")

        # Badge da Obra
        obra_badge = ctk.CTkFrame(
            tags_box, corner_radius=6,
            fg_color=COLORS["primary_subtle"],
            border_width=1, border_color=COLORS["primary_border"]
        )
        obra_badge.pack(side="left", padx=(0, 6))

        ctk.CTkLabel(
            obra_badge,
            text=f"🏗️ {self.task.obra}",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            text_color=COLORS["primary"]
        ).pack(padx=8, pady=2)

        # Badge de SLA / Prazos
        sla_text, sla_bg, sla_border, sla_color = self._get_sla_badge_info()
        sla_badge = ctk.CTkFrame(
            tags_box, corner_radius=6,
            fg_color=sla_bg,
            border_width=1, border_color=sla_border
        )
        sla_badge.pack(side="left")

        ctk.CTkLabel(
            sla_badge,
            text=sla_text,
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            text_color=sla_color
        ).pack(padx=8, pady=2)

        # LINHA 2: Descrição (se houver)
        if self.task.description:
            desc_label = ctk.CTkLabel(
                content_frame,
                text=self.task.description,
                font=ctk.CTkFont(family=FONT_FAMILY, size=11),
                text_color=COLORS["text_secondary"],
                anchor="w",
                justify="left",
                wraplength=660
            )
            desc_label.grid(row=1, column=0, sticky="w", pady=(2, 6))

        # LINHA 3: Metadados Inferiores com Avatar e Datas
        meta_row = ctk.CTkFrame(content_frame, fg_color="transparent")
        meta_row.grid(row=2, column=0, sticky="ew")

        # Avatar com Iniciais do Responsável
        initials = get_initials(self.task.responsible)
        avatar_box = ctk.CTkFrame(
            meta_row, width=22, height=22, corner_radius=5,
            fg_color=COLORS["card_inner_bg"],
            border_width=1, border_color=COLORS["card_border"]
        )
        avatar_box.pack(side="left", padx=(0, 6))
        avatar_box.pack_propagate(False)

        ctk.CTkLabel(
            avatar_box, text=initials,
            font=ctk.CTkFont(family=FONT_FAMILY, size=9, weight="bold"),
            text_color=COLORS["text_secondary"]
        ).pack(expand=True)

        resp_label = ctk.CTkLabel(
            meta_row, text=self.task.responsible,
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            text_color=COLORS["text_secondary"]
        )
        resp_label.pack(side="left", padx=(0, 12))

        # Datas
        dates_label = ctk.CTkLabel(
            meta_row,
            text=f"📅 {self.task.start_date_br} ➔ {self.task.end_date_br}",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=COLORS["text_muted"]
        )
        dates_label.pack(side="left", padx=(0, 12))

        # Chip de Prioridade
        prio_color = PRIORITY_COLORS.get(self.task.priority.value, "#3b82f6")
        prio_badge = ctk.CTkLabel(
            meta_row,
            text=f"⚡ {self.task.priority.value}",
            font=ctk.CTkFont(family=FONT_FAMILY, size=10, weight="bold"),
            text_color=prio_color
        )
        prio_badge.pack(side="left")

        # COLUNA DE AÇÕES À DIREITA
        actions_frame = ctk.CTkFrame(self, fg_color="transparent")
        actions_frame.grid(row=0, column=2, rowspan=4, sticky="e", padx=(0, 12), pady=8)

        # Seletor Moderno de Status
        self.status_menu = ctk.CTkOptionMenu(
            actions_frame,
            values=[s.value for s in TaskStatus],
            width=130,
            height=30,
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            command=self._handle_status_change
        )
        self.status_menu.set(self.task.status.value)
        self.status_menu.pack(side="left", padx=(0, 6))

        # Botão Editar
        edit_btn = ctk.CTkButton(
            actions_frame,
            text="✏️",
            width=32,
            height=30,
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            fg_color="transparent",
            text_color=COLORS["text_secondary"],
            hover_color=COLORS["primary_subtle"],
            command=self._handle_edit
        )
        edit_btn.pack(side="left", padx=(0, 4))

        # Botão Excluir
        del_btn = ctk.CTkButton(
            actions_frame,
            text="✕",
            width=32,
            height=30,
            font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"),
            fg_color="transparent",
            text_color=COLORS["text_muted"],
            hover_color=COLORS["danger_subtle"],
            command=self._handle_delete
        )
        del_btn.pack(side="left")

        # Hover Effect
        self.bind("<Enter>", lambda e: self.configure(border_color=COLORS["card_hover_border"]))
        self.bind("<Leave>", lambda e: self.configure(border_color=COLORS["card_border"]))

    def _get_status_bar_color(self) -> str:
        if self.task.is_completed:
            return COLORS["success"]
        if self.task.status == TaskStatus.BLOQUEADA:
            return COLORS["purple"]
        if self.task.is_overdue:
            return COLORS["danger"]
        if self.task.status == TaskStatus.EM_ANDAMENTO:
            return COLORS["info"]
        return PRIORITY_COLORS.get(self.task.priority.value, "#3b82f6")

    def _get_sla_badge_info(self):
        if self.task.is_completed:
            return "✅ Concluída", COLORS["success_subtle"], COLORS["success_border"], COLORS["success"]
        if self.task.status == TaskStatus.BLOQUEADA:
            return "⛔ Impedimento", COLORS["purple_subtle"], COLORS["purple"], COLORS["purple"]
        
        deadline_st = self.task.deadline_status
        if deadline_st == DeadlineStatus.ATRASADA:
            days = abs(self.task.days_remaining() or 0)
            return f"🚨 Atrasada ({days}d)", COLORS["danger_subtle"], COLORS["danger_border"], COLORS["danger"]
        elif deadline_st == DeadlineStatus.VENCE_HOJE:
            return "⏰ Vence Hoje", COLORS["warning_subtle"], COLORS["warning_border"], COLORS["warning"]
        elif deadline_st == DeadlineStatus.NO_PRAZO:
            days = self.task.days_remaining() or 0
            return f"⏳ Em dia ({days}d)", COLORS["info_subtle"], COLORS["info_border"], COLORS["info"]
        return "Sem Prazo", COLORS["card_inner_bg"], COLORS["card_border"], COLORS["text_muted"]

    def _handle_toggle_complete(self):
        if self.on_toggle_complete:
            self.on_toggle_complete(self.task)

    def _handle_status_change(self, new_status_str: str):
        if self.on_status_change:
            try:
                new_status = TaskStatus(new_status_str)
                self.on_status_change(self.task, new_status)
            except ValueError:
                pass

    def _handle_edit(self):
        if self.on_edit:
            self.on_edit(self.task)

    def _handle_delete(self):
        confirm = messagebox.askyesno(
            "Confirmar Exclusão",
            f"Deseja realmente excluir a tarefa:\n\n'{self.task.name}'?",
            parent=self.winfo_toplevel()
        )
        if confirm and self.on_delete:
            self.on_delete(self.task)
