"""Design System de Nível Sênior: Tipografia, paleta obsidian/zinc e tokens de elevação."""

FONT_FAMILY = "Segoe UI"
FONT_HEADING = "Segoe UI Variable Display" if "Segoe UI Variable Display" in () else "Segoe UI"

# Cores do Design System (compatível com Modo Escuro e Claro)
COLORS = {
    # Cores de Ação Principal (Electric Indigo / Sapphire)
    "primary": "#3b82f6",
    "primary_hover": "#2563eb",
    "primary_subtle": ("#eff6ff", "#172554"),
    "primary_border": ("#bfdbfe", "#1e3a8a"),

    # Sucesso (Emerald)
    "success": "#10b981",
    "success_hover": "#059669",
    "success_subtle": ("#ecfdf5", "#064e3b"),
    "success_border": ("#a7f3d0", "#065f46"),

    # Alerta / Atenção (Amber / Marigold)
    "warning": "#f59e0b",
    "warning_hover": "#d97706",
    "warning_subtle": ("#fffbeb", "#451a03"),
    "warning_border": ("#fde68a", "#78350f"),

    # Perigo / Atrasos Críticos (Rose / Crimson)
    "danger": "#f43f5e",
    "danger_hover": "#e11d48",
    "danger_subtle": ("#fff1f2", "#4c0519"),
    "danger_border": ("#fecdd3", "#881337"),

    # Em Andamento / Informativo (Sky Cyan)
    "info": "#0ea5e9",
    "info_hover": "#0284c7",
    "info_subtle": ("#f0f9ff", "#082f49"),
    "info_border": ("#bae6fd", "#075985"),

    # Bloqueada / Impedimento (Violet)
    "purple": "#8b5cf6",
    "purple_hover": "#7c3aed",
    "purple_subtle": ("#f5f3ff", "#2e1065"),

    # Superfícies e Elevação (Obsidian Dark / Crisp White Light)
    "sidebar_bg": ("#f8fafc", "#0b0f19"),
    "main_bg": ("#f1f5f9", "#080c14"),
    "card_bg": ("#ffffff", "#111827"),
    "card_inner_bg": ("#f8fafc", "#162032"),
    "card_border": ("#e2e8f0", "#1f293d"),
    "card_hover_border": ("#3b82f6", "#60a5fa"),

    # Tipografia de Alto Contraste
    "text_primary": ("#0f172a", "#f8fafc"),
    "text_secondary": ("#475569", "#94a3b8"),
    "text_muted": ("#94a3b8", "#64748b")
}

# Cores de Prioridade
PRIORITY_COLORS = {
    "Urgente": "#f43f5e",
    "Alta": "#f97316",
    "Média": "#f59e0b",
    "Baixa": "#3b82f6"
}

# Cores de Status
STATUS_COLORS = {
    "Pendente": "#64748b",
    "Em Andamento": "#0ea5e9",
    "Bloqueada": "#8b5cf6",
    "Concluída": "#10b981"
}

# Cores de SLA / Prazos
DEADLINE_COLORS = {
    "Concluída": "#10b981",
    "Atrasada": "#f43f5e",
    "Vence Hoje": "#f59e0b",
    "No Prazo": "#0ea5e9",
    "Sem Prazo": "#64748b"
}

def get_initials(name: str) -> str:
    """Extrai até 2 iniciais de um nome de responsável."""
    if not name or name == "Não Atribuído":
        return "NA"
    parts = [p for p in name.replace("Eng.", "").replace("Mestre", "").replace("Enc.", "").strip().split() if p]
    if len(parts) >= 2:
        return (parts[0][0] + parts[1][0]).upper()
    elif len(parts) == 1:
        return parts[0][:2].upper()
    return "OB"
