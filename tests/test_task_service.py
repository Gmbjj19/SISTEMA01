import unittest
import tempfile
import os
from pathlib import Path
from datetime import date, timedelta
from database.connection import DatabaseManager
from database.migrator import init_database
from models.enums import TaskPriority, TaskStatus, DeadlineStatus
from models.task import Task
from repositories.task_repository import TaskRepository
from services.task_service import TaskService
from services.export_service import ExportService

class TestTaskService(unittest.TestCase):
    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_file.close()
        self.db_path = Path(self.temp_file.name)
        self.manager = DatabaseManager(self.db_path)
        init_database(self.manager)
        self.repo = TaskRepository(self.manager)
        self.service = TaskService(self.repo)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_validation_errors(self):
        # Nome vazio
        valid, err = self.service.validate_task_payload({"name": "", "obra": "O1", "responsible": "R1"})
        self.assertFalse(valid)
        self.assertIn("Nome da Tarefa", err)

        # Obra vazia
        valid, err = self.service.validate_task_payload({"name": "Fundações", "obra": "", "responsible": "R1"})
        self.assertFalse(valid)
        self.assertIn("Nome da Obra", err)

        # Data inválida
        valid, err = self.service.validate_task_payload({
            "name": "Fundações", "obra": "O1", "responsible": "R1",
            "start_date": "99/99/9999"
        })
        self.assertFalse(valid)
        self.assertIn("Data de Início inválida", err)

        # Término antes do início
        valid, err = self.service.validate_task_payload({
            "name": "Fundações", "obra": "O1", "responsible": "R1",
            "start_date": "10/11/2026", "end_date": "05/11/2026"
        })
        self.assertFalse(valid)
        self.assertIn("não pode ser anterior", err)

    def test_create_and_toggle_completion(self):
        task, err = self.service.create_task({
            "name": "Montagem de andaimes fachadeiros",
            "obra": "Torre Bela Vista",
            "responsible": "Encarregado Roberto",
            "start_date": "10/11/2026",
            "end_date": "20/11/2026",
            "priority": "Alta",
            "status": "Em Andamento"
        })
        self.assertIsNone(err)
        self.assertIsNotNone(task)
        self.assertEqual(task.status, TaskStatus.EM_ANDAMENTO)

        # Alternar para concluída
        toggled = self.service.toggle_completed(task.id)
        self.assertEqual(toggled.status, TaskStatus.CONCLUIDA)

        # Alternar de volta
        toggled_back = self.service.toggle_completed(task.id)
        self.assertEqual(toggled_back.status, TaskStatus.EM_ANDAMENTO)

    def test_deadline_calculations(self):
        today = date.today()
        task_overdue = Task(name="T1", end_date=today - timedelta(days=3))
        self.assertTrue(task_overdue.is_overdue)
        self.assertEqual(task_overdue.deadline_status, DeadlineStatus.ATRASADA)
        self.assertEqual(task_overdue.days_remaining(), -3)

        task_today = Task(name="T2", end_date=today)
        self.assertEqual(task_today.deadline_status, DeadlineStatus.VENCE_HOJE)
        self.assertEqual(task_today.days_remaining(), 0)

        task_future = Task(name="T3", end_date=today + timedelta(days=5))
        self.assertEqual(task_future.deadline_status, DeadlineStatus.NO_PRAZO)
        self.assertEqual(task_future.days_remaining(), 5)

    def test_export_to_excel(self):
        self.service.create_task({
            "name": "Instalação de esquadrias",
            "obra": "Residencial Park",
            "responsible": "Eng. Paulo",
            "start_date": "01/11/2026",
            "end_date": "15/11/2026",
            "priority": "Urgente",
            "status": "Em Andamento"
        })
        export_service = ExportService(self.repo)
        temp_xlsx = Path(tempfile.gettempdir()) / "test_relatorio.xlsx"
        result_path = export_service.export_tasks_to_excel(temp_xlsx)
        self.assertTrue(result_path.exists())
        self.assertGreater(result_path.stat().st_size, 1000)
        if result_path.exists():
            os.remove(result_path)

if __name__ == "__main__":
    unittest.main()

