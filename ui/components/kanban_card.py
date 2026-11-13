import customtkinter as ctk
from typing import Callable, Optional
from ui.theme import FONT_FAMILY, COLORS, PRIORITY_COLORS, STATUS_COLORS, get_initials
from models.task import Task
from models.enums import TaskStatus, DeadlineStatus

class KanbanCard(ctk.CTkFrame):
    """Card compacto de alta densidade visual desenhado especificamente para colunas Kanban."""
    def __init__(
        self,
        master,
        task: Task,
        on_move_next: Optional[Callable[[Task], None]] = None,
        on_move_prev: Optional[Callable[[Task], None]] = None,
        on_edit: Optional[Callable[[Task], None]] = None,
        **kwargs
    ):
        super().__init__(
            master,
            corner_radius=10,
            border_width=1,
            fg_color=COLORS["card_bg"],
            border_color=COLORS["card_border"],
            **kwargs
        )

        self.task = task
        self.on_move_next = on_move_next
        self.on_move_prev = on_move_prev
        self.on_edit = on_edit

        # Destaque superior de prioridade
        prio_color = PRIORITY_COLORS.get(self.task.priority.value, "#3b82f6")
        top_accent = ctk.CTkFrame(self, height=3, corner_radius=1, fg_color=prio_color)
        top_accent.pack(fill="x", padx=8, pady=(3, 0))

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=10, pady=(6, 8))

        # Linha 1: Tag Obra + Prioridade
        meta_top = ctk.CTkFrame(content, fg_color="transparent")
        meta_top.pack(fill="x", pady=(0, 4))

        obra_label = ctk.CTkLabel(
            meta_top, text=f"🏗️ {self.task.obra}",
            font=ctk.CTkFont(family=FONT_FAMILY, size=10, weight="bold"),
            text_color=COLORS["primary"]
        )
        obra_label.pack(side="left")

        prio_label = ctk.CTkLabel(
            meta_top, text=f"⚡ {self.task.priority.value}",
            font=ctk.CTkFont(family=FONT_FAMILY, size=9, weight="bold"),
            text_color=prio_color
        )
        prio_label.pack(side="right")

        # Linha 2: Título da Tarefa
        title_lbl = ctk.CTkLabel(
            content, text=self.task.name,
            font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"),
            text_color=COLORS["text_primary"],
            anchor="w", justify="left", wraplength=210
        )
        title_lbl.pack(fill="x", pady=(0, 4))

        # Linha 3: Prazo / SLA
        if self.task.end_date:
            sla_text = f"📅 {self.task.end_date_br}"
            sla_color = COLORS["text_muted"]
            if self.task.is_overdue:
                sla_text = f"🚨 Atrasada ({abs(self.task.days_remaining() or 0)}d)"
                sla_color = COLORS["danger"]
            elif self.task.deadline_status == DeadlineStatus.VENCE_HOJE:
                sla_text = "⏰ Vence Hoje"
                sla_color = COLORS["warning"]

            date_lbl = ctk.CTkLabel(
                content, text=sla_text,
                font=ctk.CTkFont(family=FONT_FAMILY, size=10, weight="bold"),
                text_color=sla_color, anchor="w"
            )
            date_lbl.pack(fill="x", pady=(0, 6))

        # Linha 4: Responsável + Botões de Avanço de Status
        bot_row = ctk.CTkFrame(content, fg_color="transparent")
        bot_row.pack(fill="x")

        # Avatar
        initials = get_initials(self.task.responsible)
        avatar = ctk.CTkFrame(
            bot_row, width=20, height=20, corner_radius=4,
            fg_color=COLORS["card_inner_bg"],
            border_width=1, border_color=COLORS["card_border"]
        )
        avatar.pack(side="left", padx=(0, 4))
        avatar.pack_propagate(False)

        ctk.CTkLabel(
            avatar, text=initials,
            font=ctk.CTkFont(family=FONT_FAMILY, size=8, weight="bold"),
            text_color=COLORS["text_secondary"]
        ).pack(expand=True)

        ctk.CTkLabel(
            bot_row, text=self.task.responsible.split()[0],
            font=ctk.CTkFont(family=FONT_FAMILY, size=10),
            text_color=COLORS["text_secondary"]
        ).pack(side="left")

        # Ações de movimentação
        btn_box = ctk.CTkFrame(bot_row, fg_color="transparent")
        btn_box.pack(side="right")

        # Voltar
        if on_move_prev and self.task.status != TaskStatus.PENDENTE:
            prev_btn = ctk.CTkButton(
                btn_box, text="◀", width=22, height=22,
                font=ctk.CTkFont(family=FONT_FAMILY, size=9),
                fg_color="transparent", text_color=COLORS["text_secondary"],
                hover_color=COLORS["card_inner_bg"],
                command=lambda: self.on_move_prev(self.task)
            )
            prev_btn.pack(side="left", padx=1)

        # Editar
        if on_edit:
            edit_btn = ctk.CTkButton(
                btn_box, text="✏️", width=22, height=22,
                font=ctk.CTkFont(family=FONT_FAMILY, size=9),
                fg_color="transparent", text_color=COLORS["text_secondary"],
                hover_color=COLORS["card_inner_bg"],
                command=lambda: self.on_edit(self.task)
            )
            edit_btn.pack(side="left", padx=1)

        # Avançar
        if on_move_next and self.task.status != TaskStatus.CONCLUIDA:
            next_btn = ctk.CTkButton(
                btn_box, text="▶", width=22, height=22,
                font=ctk.CTkFont(family=FONT_FAMILY, size=9),
                fg_color="transparent", text_color=COLORS["primary"],
                hover_color=COLORS["primary_subtle"],
                command=lambda: self.on_move_next(self.task)
            )
            next_btn.pack(side="left", padx=1)

        # Hover Effect
        self.bind("<Enter>", lambda e: self.configure(border_color=COLORS["card_hover_border"]))
        self.bind("<Leave>", lambda e: self.configure(border_color=COLORS["card_border"]))

