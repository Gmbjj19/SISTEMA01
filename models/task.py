from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, Dict, Any
from .enums import TaskPriority, TaskStatus, DeadlineStatus

def parse_date_str(val: Optional[str]) -> Optional[date]:
    """Converte string de data (DD/MM/AAAA ou AAAA-MM-DD) para date object."""
    if not val or val.strip() in ("", "--/--/----"):
        return None
    val = val.strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(val, fmt).date()
        except ValueError:
            pass
    return None

def format_date_br(d: Optional[date]) -> str:
    """Retorna data no formato brasileiro DD/MM/AAAA."""
    if not d:
        return "--/--/----"
    return d.strftime("%d/%m/%Y")

def format_date_iso(d: Optional[date]) -> str:
    """Retorna data no formato ISO AAAA-MM-DD."""
    if not d:
        return ""
    return d.strftime("%Y-%m-%d")

@dataclass
class Task:
    id: Optional[int] = None
    name: str = ""
    obra: str = ""
    responsible: str = ""
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    priority: TaskPriority = TaskPriority.MEDIA
    status: TaskStatus = TaskStatus.PENDENTE
    description: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @property
    def is_completed(self) -> bool:
        return self.status == TaskStatus.CONCLUIDA

    @property
    def start_date_br(self) -> str:
        return format_date_br(self.start_date)

    @property
    def end_date_br(self) -> str:
        return format_date_br(self.end_date)

    @property
    def start_date_iso(self) -> str:
        return format_date_iso(self.start_date)

    @property
    def end_date_iso(self) -> str:
        return format_date_iso(self.end_date)

    def days_remaining(self, ref_date: Optional[date] = None) -> Optional[int]:
        """Calcula dias restantes até o vencimento. Negativo significa dias de atraso."""
        if not self.end_date:
            return None
        today = ref_date or date.today()
        return (self.end_date - today).days

    @property
    def deadline_status(self) -> DeadlineStatus:
        if self.is_completed:
            return DeadlineStatus.CONCLUIDA
        if not self.end_date:
            return DeadlineStatus.SEM_PRAZO
        
        diff = self.days_remaining()
        if diff is None:
            return DeadlineStatus.SEM_PRAZO
        if diff < 0:
            return DeadlineStatus.ATRASADA
        if diff == 0:
            return DeadlineStatus.VENCE_HOJE
        return DeadlineStatus.NO_PRAZO

    @property
    def is_overdue(self) -> bool:
        return self.deadline_status == DeadlineStatus.ATRASADA

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "obra": self.obra,
            "responsible": self.responsible,
            "start_date": self.start_date_iso,
            "end_date": self.end_date_iso,
            "start_date_br": self.start_date_br,
            "end_date_br": self.end_date_br,
            "priority": self.priority.value,
            "status": self.status.value,
            "description": self.description,
            "completed": self.is_completed,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "deadline_status": self.deadline_status.value
        }

    @classmethod
    def from_row(cls, row: Any) -> "Task":
        """Constrói uma Task a partir de um sqlite3.Row ou dicionário."""
        d = dict(row)
        
        # Converter prioridade
        p_val = d.get("priority", "Média")
        try:
            priority = TaskPriority(p_val)
        except ValueError:
            priority = TaskPriority.MEDIA

        # Converter status
        s_val = d.get("status")
        if not s_val:
            s_val = TaskStatus.CONCLUIDA.value if d.get("completed") else TaskStatus.PENDENTE.value
        try:
            status = TaskStatus(s_val)
        except ValueError:
            status = TaskStatus.PENDENTE

        start_d = parse_date_str(d.get("start_date"))
        end_d = parse_date_str(d.get("end_date"))

        def parse_dt(ts):
            if not ts:
                return None
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%d/%m/%Y %H:%M"):
                try:
                    return datetime.strptime(str(ts)[:19], fmt)
                except ValueError:
                    pass
            return None

        return cls(
            id=d.get("id"),
            name=d.get("name") or d.get("text") or "Sem Nome",
            obra=d.get("obra") or "Geral",
            responsible=d.get("responsible") or "Não Atribuído",
            start_date=start_d,
            end_date=end_d,
            priority=priority,
            status=status,
            description=d.get("description") or "",
            created_at=parse_dt(d.get("created_at")),
            updated_at=parse_dt(d.get("updated_at"))
        )

