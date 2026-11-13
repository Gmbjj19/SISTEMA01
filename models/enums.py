from enum import Enum

class TaskPriority(str, Enum):
    URGENTE = "Urgente"
    ALTA = "Alta"
    MEDIA = "Média"
    BAIXA = "Baixa"

    @classmethod
    def list_values(cls):
        return [cls.URGENTE.value, cls.ALTA.value, cls.MEDIA.value, cls.BAIXA.value]

    @property
    def rank(self) -> int:
        ranks = {
            TaskPriority.URGENTE: 4,
            TaskPriority.ALTA: 3,
            TaskPriority.MEDIA: 2,
            TaskPriority.BAIXA: 1
        }
        return ranks.get(self, 2)


class TaskStatus(str, Enum):
    PENDENTE = "Pendente"
    EM_ANDAMENTO = "Em Andamento"
    BLOQUEADA = "Bloqueada"
    CONCLUIDA = "Concluída"

    @classmethod
    def list_values(cls):
        return [cls.PENDENTE.value, cls.EM_ANDAMENTO.value, cls.BLOQUEADA.value, cls.CONCLUIDA.value]


class DeadlineStatus(str, Enum):
    CONCLUIDA = "Concluída"
    ATRASADA = "Atrasada"
    VENCE_HOJE = "Vence Hoje"
    NO_PRAZO = "No Prazo"
    SEM_PRAZO = "Sem Prazo"

