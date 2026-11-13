import customtkinter as ctk
from typing import Callable, List
from ui.theme import FONT_FAMILY, COLORS
from models.enums import TaskPriority

class FilterBar(ctk.CTkFrame):
    """Barra multifuncional de filtros avançados, pesquisa e alternador de visualização (Lista / Kanban)."""
    def __init__(
        self,
        master,
        on_filter_changed: Callable[[], None],
        on_view_mode_changed: Callable[[str], None] = None,
        obras_list: List[str] = None,
        **kwargs
    ):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.on_filter_changed = on_filter_changed
        self.on_view_mode_changed = on_view_mode_changed
        self.obras_list = obras_list or []

        self.grid_columnconfigure(0, weight=1)

        # LINHA 1: Caixa de Busca Ampla + Alternador de Visualização (Lista vs Kanban)
        top_row = ctk.CTkFrame(self, fg_color="transparent")
        top_row.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        top_row.grid_columnconfigure(0, weight=1)

        # Caixa de Pesquisa
        self.search_entry = ctk.CTkEntry(
            top_row,
            placeholder_text="🔍 Pesquisar por tarefa, canteiro, responsável ou observação...",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            height=38,
            corner_radius=8
        )
        self.search_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.search_entry.bind("<KeyRelease>", lambda e: self.on_filter_changed())

        # Alternador de Modo de Visualização (Lista vs Kanban)
        if self.on_view_mode_changed:
            self.view_switcher = ctk.CTkSegmentedButton(
                top_row,
                values=["📋 Lista", "📌 Kanban"],
                height=36,
                font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
                command=self.on_view_mode_changed
            )
            self.view_switcher.set("📋 Lista")
            self.view_switcher.grid(row=0, column=1, sticky="e")

        # LINHA 2: Seletores de Filtros e Ordenação
        filters_row = ctk.CTkFrame(self, fg_color="transparent")
        filters_row.grid(row=1, column=0, sticky="ew")

        # 1. Filtro por Obra
        ctk.CTkLabel(
            filters_row, text="Obra:",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            text_color=COLORS["text_secondary"]
        ).pack(side="left", padx=(0, 4))

        self.obra_var = ctk.StringVar(value="Todas")
        self.obra_menu = ctk.CTkOptionMenu(
            filters_row,
            variable=self.obra_var,
            values=["Todas"] + self.obras_list,
            width=160,
            height=32,
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            command=lambda v: self.on_filter_changed()
        )
        self.obra_menu.pack(side="left", padx=(0, 12))

        # 2. Filtro por Status
        ctk.CTkLabel(
            filters_row, text="Status:",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            text_color=COLORS["text_secondary"]
        ).pack(side="left", padx=(0, 4))

        self.status_var = ctk.StringVar(value="Todos")
        status_options = ["Todos", "Pendentes", "Em Andamento", "Bloqueada", "Atrasadas", "Concluídas"]
        self.status_menu = ctk.CTkOptionMenu(
            filters_row,
            variable=self.status_var,
            values=status_options,
            width=135,
            height=32,
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            command=lambda v: self.on_filter_changed()
        )
        self.status_menu.pack(side="left", padx=(0, 12))

        # 3. Filtro por Prioridade
        ctk.CTkLabel(
            filters_row, text="Prioridade:",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            text_color=COLORS["text_secondary"]
        ).pack(side="left", padx=(0, 4))

        self.priority_var = ctk.StringVar(value="Todas")
        self.priority_menu = ctk.CTkOptionMenu(
            filters_row,
            variable=self.priority_var,
            values=["Todas"] + TaskPriority.list_values(),
            width=115,
            height=32,
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            command=lambda v: self.on_filter_changed()
        )
        self.priority_menu.pack(side="left", padx=(0, 12))

        # 4. Ordenação
        ctk.CTkLabel(
            filters_row, text="Ordenar por:",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            text_color=COLORS["text_secondary"]
        ).pack(side="left", padx=(0, 4))

        self.order_var = ctk.StringVar(value="Prazo (Mais próximo)")
        self.order_menu = ctk.CTkOptionMenu(
            filters_row,
            variable=self.order_var,
            values=["Prazo (Mais próximo)", "Prioridade (Maior)", "Obra (A-Z)", "Mais recentes"],
            width=165,
            height=32,
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            command=lambda v: self.on_filter_changed()
        )
        self.order_menu.pack(side="left", padx=(0, 10))

        # 5. Botão Reset Filtros
        self.clear_btn = ctk.CTkButton(
            filters_row,
            text="✕ Limpar",
            width=75,
            height=32,
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            fg_color="transparent",
            border_width=1,
            border_color=COLORS["card_border"],
            text_color=COLORS["text_secondary"],
            hover_color=COLORS["danger_subtle"],
            command=self.reset_filters
        )
        self.clear_btn.pack(side="left")

    def update_obras(self, obras: List[str]):
        current = self.obra_var.get()
        self.obras_list = obras
        values = ["Todas"] + obras
        self.obra_menu.configure(values=values)
        if current in values:
            self.obra_var.set(current)
        else:
            self.obra_var.set("Todas")

    def reset_filters(self):
        self.search_entry.delete(0, "end")
        self.obra_var.set("Todas")
        self.status_var.set("Todos")
        self.priority_var.set("Todas")
        self.order_var.set("Prazo (Mais próximo)")
        self.on_filter_changed()

    def get_filter_values(self):
        order_map = {
            "Prazo (Mais próximo)": "deadline",
            "Prioridade (Maior)": "priority",
            "Obra (A-Z)": "obra",
            "Mais recentes": "recent"
        }
        return {
            "search": self.search_entry.get().strip(),
            "obra": None if self.obra_var.get() == "Todas" else self.obra_var.get(),
            "status": None if self.status_var.get() == "Todos" else self.status_var.get(),
            "priority": None if self.priority_var.get() == "Todas" else self.priority_var.get(),
            "order_by": order_map.get(self.order_var.get(), "deadline")
        }
