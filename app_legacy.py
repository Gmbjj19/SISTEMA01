import customtkinter as ctk
from tkinter import messagebox
import json
import os
from datetime import datetime

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

FILENAME = "tasks_enterprise.json"

class TaskCard(ctk.CTkFrame):
    """Card ultra-customizado exibindo todos os detalhes da tarefa e da obra."""
    def __init__(self, master, task_data, on_state_change=None, on_delete=None):
        super().__init__(
            master, 
            corner_radius=12, 
            border_width=1,
            fg_color=("#ffffff", "#1f242c"),
            border_color=("#e1e4e8", "#30363d")
        )
        
        self.on_state_change = on_state_change
        self.on_delete = on_delete
        self.task_data = task_data

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Cor da barra lateral baseada na prioridade e status
        completed = task_data.get("completed", False)
        priority = task_data.get("priority", "Média")
        self.bar_color = self.get_priority_color(priority, completed)

        # Barra lateral de status
        self.status_bar = ctk.CTkFrame(
            self, width=6, corner_radius=3, 
            fg_color=self.bar_color
        )
        self.status_bar.grid(row=0, column=0, sticky="ns", padx=(3, 10), pady=3)

        # Container central de informações
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.grid(row=0, column=1, sticky="ew", padx=5, pady=10)
        content_frame.grid_columnconfigure(0, weight=1)

        # Linha Superior: Checkbox com Nome da Tarefa + Tag de Obra
        top_row = ctk.CTkFrame(content_frame, fg_color="transparent")
        top_row.grid(row=0, column=0, sticky="ew", pady=(0, 2))
        top_row.grid_columnconfigure(0, weight=1)

        self.checkbox = ctk.CTkCheckBox(
            top_row, text=task_data["name"],
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            corner_radius=6,
            command=self.toggle_completion
        )
        if completed:
            self.checkbox.select()
        self.checkbox.grid(row=0, column=0, sticky="w")

        # Tag de Obra
        obra_tag = ctk.CTkLabel(
            top_row, text=f"🏗️ {task_data['obra']}",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=("#2563eb", "#58a6ff")
        )
        obra_tag.grid(row=0, column=1, sticky="e", padx=10)

        # Descrição (se houver)
        if task_data.get("description"):
            self.desc_label = ctk.CTkLabel(
                content_frame, text=task_data["description"],
                font=ctk.CTkFont(family="Segoe UI", size=11),
                text_color=("#57606a", "#8b949e"),
                anchor="w"
            )
            self.desc_label.grid(row=1, column=0, sticky="w", pady=(2, 4))

        # Metadados Inferiores (Datas, Responsável e Prioridade)
        meta_text = (
            f"👤 Resp: {task_data['responsible']}  •  "
            f"📅 Início: {task_data['start_date']} ➔ Fim: {task_data['end_date']}  •  "
            f"⚡ Prioridade: {priority}"
        )
        self.info_label = ctk.CTkLabel(
            content_frame, text=meta_text,
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=("#57606a", "#8b949e")
        )
        self.info_label.grid(row=2, column=0, sticky="w", pady=(2, 0))

        # Botão de Exclusão Individual (Lixeira)
        self.delete_btn = ctk.CTkButton(
            self, text="✕", width=30, height=30,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color="transparent", text_color=("#57606a", "#8b949e"),
            hover_color=("#fee2e2", "#450a0a"),
            command=self.trigger_delete
        )
        self.delete_btn.grid(row=0, column=2, padx=10)

        # Efeitos de Hover
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)

    def get_priority_color(self, priority, completed):
        if completed:
            return "#10b981" # Verde Sucesso
        colors = {
            "Urgente": "#ef4444",  # Vermelho
            "Média": "#f59e0b",    # Laranja
            "Baixa": "#3b82f6"     # Azul
        }
        return colors.get(priority, "#3b82f6")

    def on_enter(self, event):
        self.configure(border_color=("#2563eb", "#58a6ff"))

    def on_leave(self, event):
        self.configure(border_color=("#e1e4e8", "#30363d"))

    def toggle_completion(self):
        is_checked = self.checkbox.get() == 1
        self.task_data["completed"] = is_checked
        new_color = self.get_priority_color(self.task_data["priority"], is_checked)
        self.status_bar.configure(fg_color=new_color)
        
        if self.on_state_change:
            self.on_state_change()

    def trigger_delete(self):
        if self.on_delete:
            self.on_delete(self)

    def get_data(self):
        self.task_data["completed"] = self.checkbox.get() == 1
        return self.task_data


class TaskFormWindow(ctk.CTkToplevel):
    """Janela de formulário modal para cadastro detalhado de novas tarefas."""
    def __init__(self, master, on_save_callback):
        super().__init__(master)
        self.title("Nova Tarefa / Obra")
        self.geometry("450x620")
        self.resizable(False, False)
        self.on_save_callback = on_save_callback

        # Garante que a janela fique em foco
        self.grab_set()

        title = ctk.CTkLabel(
            self, text="📋 Cadastro de Tarefa",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold")
        )
        title.pack(pady=(20, 15))

        # Container do Formulário
        form_frame = ctk.CTkFrame(self, fg_color="transparent")
        form_frame.pack(padx=30, fill="both", expand=True)

        # 1. Nome da Tarefa
        ctk.CTkLabel(form_frame, text="Nome da Tarefa *", font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold")).pack(anchor="w")
        self.name_entry = ctk.CTkEntry(form_frame, placeholder_text="Ex: Concretagem da laje", height=36)
        self.name_entry.pack(fill="x", pady=(2, 10))

        # 2. Nome da Obra
        ctk.CTkLabel(form_frame, text="Nome da Obra *", font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold")).pack(anchor="w")
        self.obra_entry = ctk.CTkEntry(form_frame, placeholder_text="Ex: Edifício Vista Jardim", height=36)
        self.obra_entry.pack(fill="x", pady=(2, 10))

        # 3. Responsável
        ctk.CTkLabel(form_frame, text="Responsável *", font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold")).pack(anchor="w")
        self.resp_entry = ctk.CTkEntry(form_frame, placeholder_text="Ex: Eng. Gil Márcio", height=36)
        self.resp_entry.pack(fill="x", pady=(2, 10))

        # 4. Datas (Início e Término lado a lado)
        dates_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        dates_frame.pack(fill="x", pady=(2, 10))
        dates_frame.grid_columnconfigure(0, weight=1)
        dates_frame.grid_columnconfigure(1, weight=1)

        f_left = ctk.CTkFrame(dates_frame, fg_color="transparent")
        f_left.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        ctk.CTkLabel(f_left, text="Data de Início *", font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold")).pack(anchor="w")
        self.start_entry = ctk.CTkEntry(f_left, placeholder_text="DD/MM/AAAA", height=36)
        self.start_entry.insert(0, datetime.now().strftime("%d/%m/%Y"))
        self.start_entry.pack(fill="x", pady=(2, 0))

        f_right = ctk.CTkFrame(dates_frame, fg_color="transparent")
        f_right.grid(row=0, column=1, sticky="ew", padx=(5, 0))
        ctk.CTkLabel(f_right, text="Data de Término *", font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold")).pack(anchor="w")
        self.end_entry = ctk.CTkEntry(f_right, placeholder_text="DD/MM/AAAA", height=36)
        self.end_entry.pack(fill="x", pady=(2, 0))

        # 5. Prioridade
        ctk.CTkLabel(form_frame, text="Prioridade", font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold")).pack(anchor="w")
        self.priority_var = ctk.StringVar(value="Média")
        self.priority_menu = ctk.CTkOptionMenu(
            form_frame, values=["Baixa", "Média", "Urgente"],
            variable=self.priority_var, height=36
        )
        self.priority_menu.pack(fill="x", pady=(2, 10))

        # 6. Descrição
        ctk.CTkLabel(form_frame, text="Descrição / Observações", font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold")).pack(anchor="w")
        self.desc_text = ctk.CTkTextbox(form_frame, height=70, corner_radius=6)
        self.desc_text.pack(fill="x", pady=(2, 15))

        # Botão Salvar
        save_btn = ctk.CTkButton(
            self, text="Salvar Tarefa", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            height=40, fg_color="#2563eb", hover_color="#1d4ed8",
            command=self.save_task
        )
        save_btn.pack(padx=30, pady=(0, 20), fill="x")

    def save_task(self):
        name = self.name_entry.get().strip()
        obra = self.obra_entry.get().strip()
        responsible = self.resp_entry.get().strip()
        start_date = self.start_entry.get().strip()
        end_date = self.end_entry.get().strip()
        priority = self.priority_var.get()
        description = self.desc_text.get("1.0", "end").strip()

        if not name or not obra or not responsible or not start_date or not end_date:
            messagebox.showwarning("Campos Obrigatórios", "Preencha todos os campos obrigatórios (*)", parent=self)
            return

        task_data = {
            "name": name,
            "obra": obra,
            "responsible": responsible,
            "start_date": start_date,
            "end_date": end_date,
            "priority": priority,
            "description": description,
            "completed": False
        }

        self.on_save_callback(task_data)
        self.destroy()


class TodoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestão de Obras & Tarefas • Enterprise Pro")
        self.root.geometry("560x720")
        self.root.resizable(False, False)

        # Cabeçalho
        title_label = ctk.CTkLabel(
            root, text="🏗️ Painel de Controle de Obras", 
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold")
        )
        title_label.pack(pady=(15, 5))

        # Estatísticas
        self.stats_label = ctk.CTkLabel(
            root, text="Progresso geral: 0 de 0 concluídas (0%)",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=("#2563eb", "#58a6ff")
        )
        self.stats_label.pack(pady=(0, 10))

        # Barra de Pesquisa e Botão Nova Tarefa
        top_action_frame = ctk.CTkFrame(root, fg_color="transparent")
        top_action_frame.pack(pady=5, padx=25, fill="x")
        top_action_frame.grid_columnconfigure(0, weight=1)

        self.search_entry = ctk.CTkEntry(
            top_action_frame, placeholder_text="🔍 Pesquisar por tarefa ou obra...",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            height=40, corner_radius=8
        )
        self.search_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.search_entry.bind("<KeyRelease>", lambda event: self.filter_tasks())

        new_task_btn = ctk.CTkButton(
            top_action_frame, text="+ Nova Tarefa",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            height=40, width=130, corner_radius=8,
            command=self.open_task_form
        )
        new_task_btn.grid(row=0, column=1)

        # Filtros por Abas
        filter_frame = ctk.CTkFrame(root, fg_color="transparent")
        filter_frame.pack(pady=10, padx=25, fill="x")

        self.filter_var = ctk.StringVar(value="Todas")
        for f_name in ["Todas", "Pendentes", "Concluídas"]:
            btn = ctk.CTkRadioButton(
                filter_frame, text=f_name, value=f_name,
                variable=self.filter_var, command=self.filter_tasks,
                font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold")
            )
            btn.pack(side="left", expand=True)

        # Container com rolagem para os Cards
        self.scrollable_frame = ctk.CTkScrollableFrame(
            root, width=480, height=360, 
            corner_radius=12, border_width=1,
            fg_color=("#f6f8fa", "#161b22")
        )
        self.scrollable_frame.pack(pady=10, padx=25, fill="both", expand=True)

        self.task_cards = []

        # Botão de Ação Inferior
        clear_completed_btn = ctk.CTkButton(
            root, text="Remover Todas Concluídas", 
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color="#da3633", hover_color="#b62324",
            height=38, corner_radius=8,
            command=self.remove_completed_tasks
        )
        clear_completed_btn.pack(pady=(5, 20), padx=25, fill="x")

        self.load_tasks()
        self.update_stats()

    def open_task_form(self):
        TaskFormWindow(self.root, self.add_task_from_form)

    def add_task_from_form(self, task_data):
        card = TaskCard(
            self.scrollable_frame, 
            task_data=task_data,
            on_state_change=self.on_card_state_changed,
            on_delete=self.delete_specific_card
        )
        card.pack(fill="x", pady=6, padx=4)
        self.task_cards.append(card)
        
        self.save_tasks()
        self.update_stats()
        self.filter_tasks()

    def on_card_state_changed(self):
        self.save_tasks()
        self.update_stats()

    def delete_specific_card(self, card):
        card.destroy()
        if card in self.task_cards:
            self.task_cards.remove(card)
        self.save_tasks()
        self.update_stats()

    def remove_completed_tasks(self):
        remaining_cards = []
        for card in self.task_cards:
            if card.checkbox.get() == 1:
                card.destroy()
            else:
                remaining_cards.append(card)
        self.task_cards = remaining_cards
        self.save_tasks()
        self.update_stats()
        self.filter_tasks()

    def filter_tasks(self):
        search_query = self.search_entry.get().lower().strip()
        current_filter = self.filter_var.get()

        for card in self.task_cards:
            t_name = card.task_data["name"].lower()
            obra = card.task_data["obra"].lower()
            resp = card.task_data["responsible"].lower()
            is_completed = card.checkbox.get() == 1

            matches_search = search_query in t_name or search_query in obra or search_query in resp

            matches_tab = True
            if current_filter == "Pendentes":
                matches_tab = not is_completed
            elif current_filter == "Concluídas":
                matches_tab = is_completed

            if matches_search and matches_tab:
                card.pack(fill="x", pady=6, padx=4)
            else:
                card.pack_forget()

    def update_stats(self):
        total = len(self.task_cards)
        if total == 0:
            self.stats_label.configure(text="Nenhuma tarefa cadastrada no momento.")
            return

        completed_count = sum(1 for card in self.task_cards if card.checkbox.get() == 1)
        percentage = int((completed_count / total) * 100)
        self.stats_label.configure(text=f"Progresso geral: {completed_count} de {total} concluídas ({percentage}%)")

    def save_tasks(self):
        tasks = [card.get_data() for card in self.task_cards]
        with open(FILENAME, "w", encoding="utf-8") as f:
            json.dump(tasks, f, ensure_ascii=False, indent=4)

    def load_tasks(self):
        if os.path.exists(FILENAME):
            try:
                with open(FILENAME, "r", encoding="utf-8") as f:
                    tasks = json.load(f)
                    for t in tasks:
                        # Compatibilidade com formatos antigos caso existam
                        if isinstance(t, str):
                            t = {
                                "name": t, "obra": "Geral", "responsible": "Não definido",
                                "start_date": "--/--/----", "end_date": "--/--/----",
                                "priority": "Média", "description": "", "completed": False
                            }
                        
                        card = TaskCard(
                            self.scrollable_frame, 
                            task_data=t,
                            on_state_change=self.on_card_state_changed,
                            on_delete=self.delete_specific_card
                        )
                        card.pack(fill="x", pady=6, padx=4)
                        self.task_cards.append(card)
            except Exception:
                pass

if __name__ == "__main__":
    root = ctk.CTk()
    app = TodoApp(root)
    root.mainloop()