from typing import Optional, Tuple, List, Dict, Any
from datetime import date
from config import LOGGER
from models.task import Task, parse_date_str
from models.enums import TaskPriority, TaskStatus
from repositories.task_repository import TaskRepository

class TaskValidationError(Exception):
    pass

class TaskService:
    """Camada de serviço para orquestração de regras de negócio de tarefas e obras."""
    def __init__(self, repository: Optional[TaskRepository] = None):
        self.repository = repository or TaskRepository()

    def validate_task_payload(self, data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Valida integridade e regras de negócio dos dados da tarefa."""
        name = (data.get("name") or "").strip()
        if not name:
            return False, "O 'Nome da Tarefa' é obrigatório."
        if len(name) < 3:
            return False, "O nome da tarefa deve ter no mínimo 3 caracteres."

        obra = (data.get("obra") or "").strip()
        if not obra:
            return False, "O 'Nome da Obra' é obrigatório."

        responsible = (data.get("responsible") or "").strip()
        if not responsible:
            return False, "O 'Responsável' é obrigatório."

        # Validação das datas
        start_date_val = data.get("start_date")
        end_date_val = data.get("end_date")

        s_date: Optional[date] = None
        e_date: Optional[date] = None

        if isinstance(start_date_val, date):
            s_date = start_date_val
        elif start_date_val:
            s_date = parse_date_str(str(start_date_val))
            if not s_date:
                return False, "Data de Início inválida. Utilize o formato DD/MM/AAAA."

        if isinstance(end_date_val, date):
            e_date = end_date_val
        elif end_date_val:
            e_date = parse_date_str(str(end_date_val))
            if not e_date:
                return False, "Data de Término inválida. Utilize o formato DD/MM/AAAA."

        if s_date and e_date and e_date < s_date:
            return False, "A 'Data de Término' não pode ser anterior à 'Data de Início'."

        return True, None

    def create_task(self, data: Dict[str, Any]) -> Tuple[Optional[Task], Optional[str]]:
        """Cria e persiste uma nova tarefa após validação de regras de negócio."""
        is_valid, error_msg = self.validate_task_payload(data)
        if not is_valid:
            return None, error_msg

        # Conversão de Enums
        priority = data.get("priority", TaskPriority.MEDIA)
        if isinstance(priority, str):
            try:
                priority = TaskPriority(priority)
            except ValueError:
                priority = TaskPriority.MEDIA

        status = data.get("status", TaskStatus.PENDENTE)
        if isinstance(status, str):
            try:
                status = TaskStatus(status)
            except ValueError:
                status = TaskStatus.PENDENTE

        task = Task(
            name=data["name"].strip(),
            obra=data["obra"].strip(),
            responsible=data["responsible"].strip(),
            start_date=parse_date_str(data.get("start_date")) if isinstance(data.get("start_date"), str) else data.get("start_date"),
            end_date=parse_date_str(data.get("end_date")) if isinstance(data.get("end_date"), str) else data.get("end_date"),
            priority=priority,
            status=status,
            description=(data.get("description") or "").strip()
        )

        try:
            created_task = self.repository.create(task)
            return created_task, None
        except Exception as e:
            LOGGER.exception("Falha ao criar tarefa no repositório: %s", e)
            return None, f"Erro interno ao salvar no banco de dados: {e}"

    def update_task(self, task_id: int, data: Dict[str, Any]) -> Tuple[Optional[Task], Optional[str]]:
        """Atualiza os dados de uma tarefa existente."""
        existing = self.repository.get_by_id(task_id)
        if not existing:
            return None, f"Tarefa #{task_id} não encontrada."

        is_valid, error_msg = self.validate_task_payload(data)
        if not is_valid:
            return None, error_msg

        priority = data.get("priority", existing.priority)
        if isinstance(priority, str):
            try:
                priority = TaskPriority(priority)
            except ValueError:
                priority = existing.priority

        status = data.get("status", existing.status)
        if isinstance(status, str):
            try:
                status = TaskStatus(status)
            except ValueError:
                status = existing.status

        existing.name = data["name"].strip()
        existing.obra = data["obra"].strip()
        existing.responsible = data["responsible"].strip()
        existing.start_date = parse_date_str(data.get("start_date")) if isinstance(data.get("start_date"), str) else data.get("start_date")
        existing.end_date = parse_date_str(data.get("end_date")) if isinstance(data.get("end_date"), str) else data.get("end_date")
        existing.priority = priority
        existing.status = status
        existing.description = (data.get("description") or "").strip()

        try:
            success = self.repository.update(existing)
            if success:
                return existing, None
            return None, "Não foi possível atualizar a tarefa."
        except Exception as e:
            LOGGER.exception("Falha ao atualizar tarefa #%d: %s", task_id, e)
            return None, f"Erro interno ao atualizar: {e}"

    def toggle_completed(self, task_id: int) -> Optional[Task]:
        """Alterna o status entre Concluída e Em Andamento/Pendente."""
        task = self.repository.get_by_id(task_id)
        if not task:
            return None

        if task.status == TaskStatus.CONCLUIDA:
            new_status = TaskStatus.EM_ANDAMENTO
        else:
            new_status = TaskStatus.CONCLUIDA

        self.repository.update_status(task_id, new_status)
        task.status = new_status
        return task

    def change_status(self, task_id: int, new_status: TaskStatus) -> bool:
        return self.repository.update_status(task_id, new_status)

    def delete_task(self, task_id: int) -> bool:
        return self.repository.delete(task_id)

    def delete_completed(self) -> int:
        return self.repository.delete_completed()

    def get_task(self, task_id: int) -> Optional[Task]:
        return self.repository.get_by_id(task_id)

    def list_tasks(self, **kwargs) -> List[Task]:
        return self.repository.list_tasks(**kwargs)

    def get_obras(self) -> List[str]:
        return self.repository.get_unique_obras()

    def get_responsibles(self) -> List[str]:
        return self.repository.get_unique_responsibles()

