from dataclasses import dataclass
from typing import List

@dataclass
class ObraMetrics:
    obra: str
    total: int = 0
    concluidas: int = 0
    em_andamento: int = 0
    bloqueadas: int = 0
    pendentes: int = 0
    atrasadas: int = 0

    @property
    def percentual(self) -> float:
        if self.total == 0:
            return 0.0
        return round((self.concluidas / self.total) * 100, 1)


@dataclass
class DashboardMetrics:
    total: int = 0
    concluidas: int = 0
    em_andamento: int = 0
    bloqueadas: int = 0
    pendentes: int = 0
    atrasadas: int = 0
    vencendo_hoje: int = 0
    urgentes: int = 0
    obras_ativas: int = 0
    obras_detalhes: List[ObraMetrics] = None

    def __post_init__(self):
        if self.obras_detalhes is None:
            self.obras_detalhes = []

    @property
    def taxa_conclusao(self) -> float:
        if self.total == 0:
            return 0.0
        return round((self.concluidas / self.total) * 100, 1)

    @property
    def taxa_atraso(self) -> float:
        if self.total == 0:
            return 0.0
        return round((self.atrasadas / self.total) * 100, 1)

