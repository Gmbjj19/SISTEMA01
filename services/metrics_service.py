from typing import Optional
from repositories.task_repository import TaskRepository
from models.metrics import DashboardMetrics

class MetricsService:
    """Serviço responsável por agregar indicadores executivos de desempenho de obras."""
    def __init__(self, repository: Optional[TaskRepository] = None):
        self.repository = repository or TaskRepository()

    def get_dashboard_metrics(self) -> DashboardMetrics:
        return self.repository.get_dashboard_metrics()

