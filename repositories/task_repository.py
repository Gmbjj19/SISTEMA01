import sqlite3
from typing import List, Optional, Dict, Any
from datetime import date
from config import LOGGER
from database.connection import DatabaseManager, db_manager
from models.task import Task, format_date_iso
from models.enums import TaskPriority, TaskStatus
from models.metrics import DashboardMetrics, ObraMetrics

class TaskRepository:
    """Repositório de acesso a dados para Tarefas utilizando SQLite parametrizado."""
    def __init__(self, manager: DatabaseManager = db_manager):
        self.manager = manager

    def create(self, task: Task) -> Task:
        sql = """
            INSERT INTO tasks (name, obra, responsible, start_date, end_date, priority, status, description, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
        """
        params = (
            task.name,
            task.obra,
            task.responsible,
            task.start_date_iso or None,
            task.end_date_iso or None,
            task.priority.value,
            task.status.value,
            task.description
        )
        with self.manager.get_connection() as conn:
            cursor = conn.execute(sql, params)
            task.id = cursor.lastrowid
        LOGGER.info("Tarefa cadastrada com sucesso: ID %d - '%s'", task.id, task.name)
        return task

    def update(self, task: Task) -> bool:
        if task.id is None:
            raise ValueError("Não é possível atualizar uma tarefa sem ID.")
        sql = """
            UPDATE tasks
            SET name = ?, obra = ?, responsible = ?, start_date = ?, end_date = ?,
                priority = ?, status = ?, description = ?, updated_at = datetime('now')
            WHERE id = ?
        """
        params = (
            task.name,
            task.obra,
            task.responsible,
            task.start_date_iso or None,
            task.end_date_iso or None,
            task.priority.value,
            task.status.value,
            task.description,
            task.id
        )
        with self.manager.get_connection() as conn:
            cursor = conn.execute(sql, params)
            updated = cursor.rowcount > 0
        LOGGER.info("Tarefa ID %d atualizada: %s", task.id, updated)
        return updated

    def update_status(self, task_id: int, status: TaskStatus) -> bool:
        sql = "UPDATE tasks SET status = ?, updated_at = datetime('now') WHERE id = ?"
        with self.manager.get_connection() as conn:
            cursor = conn.execute(sql, (status.value, task_id))
            return cursor.rowcount > 0

    def delete(self, task_id: int) -> bool:
        sql = "DELETE FROM tasks WHERE id = ?"
        with self.manager.get_connection() as conn:
            cursor = conn.execute(sql, (task_id,))
            deleted = cursor.rowcount > 0
        LOGGER.info("Tarefa ID %d removida: %s", task_id, deleted)
        return deleted

    def delete_completed(self) -> int:
        sql = "DELETE FROM tasks WHERE status = ?"
        with self.manager.get_connection() as conn:
            cursor = conn.execute(sql, (TaskStatus.CONCLUIDA.value,))
            deleted_count = cursor.rowcount
        LOGGER.info("Removidas %d tarefas concluídas.", deleted_count)
        return deleted_count

    def get_by_id(self, task_id: int) -> Optional[Task]:
        sql = "SELECT * FROM tasks WHERE id = ?"
        with self.manager.get_connection() as conn:
            row = conn.execute(sql, (task_id,)).fetchone()
            if row:
                return Task.from_row(row)
        return None

    def list_tasks(
        self,
        search: str = "",
        obra: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        order_by: str = "deadline"
    ) -> List[Task]:
        query = "SELECT * FROM tasks WHERE 1=1"
        params: List[Any] = []

        if search:
            query += " AND (name LIKE ? OR obra LIKE ? OR responsible LIKE ? OR description LIKE ?)"
            term = f"%{search.strip()}%"
            params.extend([term, term, term, term])

        if obra and obra != "Todas":
            query += " AND obra = ?"
            params.append(obra)

        if status and status != "Todos":
            if status == "Atrasadas":
                query += f" AND status != ? AND end_date IS NOT NULL AND end_date < date('now')"
                params.append(TaskStatus.CONCLUIDA.value)
            else:
                query += " AND status = ?"
                params.append(status)

        if priority and priority != "Todas":
            query += " AND priority = ?"
            params.append(priority)

        # Ordenações avançadas
        if order_by == "deadline":
            query += """
                ORDER BY 
                    CASE WHEN status = 'Concluída' THEN 1 ELSE 0 END,
                    CASE WHEN end_date IS NULL OR end_date = '' THEN '9999-99-99' ELSE end_date END ASC,
                    id DESC
            """
        elif order_by == "priority":
            query += """
                ORDER BY 
                    CASE WHEN status = 'Concluída' THEN 1 ELSE 0 END,
                    CASE priority 
                        WHEN 'Urgente' THEN 4 
                        WHEN 'Alta' THEN 3 
                        WHEN 'Média' THEN 2 
                        ELSE 1 
                    END DESC,
                    id DESC
            """
        elif order_by == "obra":
            query += " ORDER BY obra ASC, name ASC"
        else: # Mais recentes
            query += " ORDER BY id DESC"

        with self.manager.get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [Task.from_row(row) for row in rows]

    def get_unique_obras(self) -> List[str]:
        sql = "SELECT DISTINCT obra FROM tasks WHERE obra IS NOT NULL AND obra != '' ORDER BY obra ASC"
        with self.manager.get_connection() as conn:
            rows = conn.execute(sql).fetchall()
            return [r["obra"] for r in rows]

    def get_unique_responsibles(self) -> List[str]:
        sql = "SELECT DISTINCT responsible FROM tasks WHERE responsible IS NOT NULL AND responsible != '' ORDER BY responsible ASC"
        with self.manager.get_connection() as conn:
            rows = conn.execute(sql).fetchall()
            return [r["responsible"] for r in rows]

    def get_dashboard_metrics(self) -> DashboardMetrics:
        today_iso = date.today().strftime("%Y-%m-%d")
        with self.manager.get_connection() as conn:
            total = conn.execute("SELECT COUNT(*) as c FROM tasks").fetchone()["c"]
            concluidas = conn.execute("SELECT COUNT(*) as c FROM tasks WHERE status = ?", (TaskStatus.CONCLUIDA.value,)).fetchone()["c"]
            em_andamento = conn.execute("SELECT COUNT(*) as c FROM tasks WHERE status = ?", (TaskStatus.EM_ANDAMENTO.value,)).fetchone()["c"]
            bloqueadas = conn.execute("SELECT COUNT(*) as c FROM tasks WHERE status = ?", (TaskStatus.BLOQUEADA.value,)).fetchone()["c"]
            pendentes = conn.execute("SELECT COUNT(*) as c FROM tasks WHERE status = ?", (TaskStatus.PENDENTE.value,)).fetchone()["c"]
            
            # Atrasadas: não concluídas e end_date < hoje
            atrasadas = conn.execute("""
                SELECT COUNT(*) as c FROM tasks 
                WHERE status != ? AND end_date IS NOT NULL AND end_date != '' AND end_date < ?
            """, (TaskStatus.CONCLUIDA.value, today_iso)).fetchone()["c"]

            # Vencendo hoje
            vencendo_hoje = conn.execute("""
                SELECT COUNT(*) as c FROM tasks 
                WHERE status != ? AND end_date = ?
            """, (TaskStatus.CONCLUIDA.value, today_iso)).fetchone()["c"]

            # Urgentes
            urgentes = conn.execute("SELECT COUNT(*) as c FROM tasks WHERE priority = ? AND status != ?", (TaskPriority.URGENTE.value, TaskStatus.CONCLUIDA.value)).fetchone()["c"]

            # Obras e detalhes
            obra_rows = conn.execute("""
                SELECT 
                    obra,
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'Concluída' THEN 1 ELSE 0 END) as concluidas,
                    SUM(CASE WHEN status = 'Em Andamento' THEN 1 ELSE 0 END) as em_andamento,
                    SUM(CASE WHEN status = 'Bloqueada' THEN 1 ELSE 0 END) as bloqueadas,
                    SUM(CASE WHEN status = 'Pendente' THEN 1 ELSE 0 END) as pendentes,
                    SUM(CASE WHEN status != 'Concluída' AND end_date IS NOT NULL AND end_date != '' AND end_date < ? THEN 1 ELSE 0 END) as atrasadas
                FROM tasks
                GROUP BY obra
                ORDER BY total DESC, obra ASC
            """, (today_iso,)).fetchall()

            obras_detalhes = [
                ObraMetrics(
                    obra=r["obra"],
                    total=r["total"],
                    concluidas=r["concluidas"],
                    em_andamento=r["em_andamento"],
                    bloqueadas=r["bloqueadas"],
                    pendentes=r["pendentes"],
                    atrasadas=r["atrasadas"]
                )
                for r in obra_rows
            ]

        return DashboardMetrics(
            total=total,
            concluidas=concluidas,
            em_andamento=em_andamento,
            bloqueadas=bloqueadas,
            pendentes=pendentes,
            atrasadas=atrasadas,
            vencendo_hoje=vencendo_hoje,
            urgentes=urgentes,
            obras_ativas=len(obras_detalhes),
            obras_detalhes=obras_detalhes
        )

