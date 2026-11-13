import unittest
import tempfile
import os
from pathlib import Path
from datetime import date, timedelta
from database.connection import DatabaseManager
from database.migrator import init_database
from models.task import Task
from models.enums import TaskPriority, TaskStatus
from repositories.task_repository import TaskRepository

class TestTaskRepository(unittest.TestCase):
    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_file.close()
        self.db_path = Path(self.temp_file.name)
        self.manager = DatabaseManager(self.db_path)
        init_database(self.manager)
        self.repo = TaskRepository(self.manager)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_create_and_get_task(self):
        task = Task(
            name="Concretagem da viga V102",
            obra="Residencial Alpha",
            responsible="Eng. Carlos",
            start_date=date(2026, 11, 10),
            end_date=date(2026, 11, 15),
            priority=TaskPriority.URGENTE,
            status=TaskStatus.EM_ANDAMENTO,
            description="Utilizar concreto FCK 30"
        )
        saved = self.repo.create(task)
        self.assertIsNotNone(saved.id)

        fetched = self.repo.get_by_id(saved.id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.name, "Concretagem da viga V102")
        self.assertEqual(fetched.obra, "Residencial Alpha")
        self.assertEqual(fetched.priority, TaskPriority.URGENTE)
        self.assertEqual(fetched.status, TaskStatus.EM_ANDAMENTO)
        self.assertEqual(fetched.start_date, date(2026, 11, 10))
        self.assertEqual(fetched.end_date, date(2026, 11, 15))

    def test_update_task(self):
        task = Task(name="Instalação elétrica", obra="Torre Sul", responsible="Eletricista João")
        saved = self.repo.create(task)

        saved.name = "Instalação elétrica e automação"
        saved.status = TaskStatus.CONCLUIDA
        updated = self.repo.update(saved)
        self.assertTrue(updated)

        fetched = self.repo.get_by_id(saved.id)
        self.assertEqual(fetched.name, "Instalação elétrica e automação")
        self.assertEqual(fetched.status, TaskStatus.CONCLUIDA)

    def test_delete_task(self):
        task = Task(name="Pintura externa", obra="Torre Sul", responsible="Pintor Marcos")
        saved = self.repo.create(task)
        self.assertTrue(self.repo.delete(saved.id))
        self.assertIsNone(self.repo.get_by_id(saved.id))

    def test_filtering_and_search(self):
        self.repo.create(Task(name="Alvenaria 1º Pav", obra="Obra A", responsible="Marcos", priority=TaskPriority.ALTA))
        self.repo.create(Task(name="Alvenaria 2º Pav", obra="Obra A", responsible="Lucas", priority=TaskPriority.URGENTE))
        self.repo.create(Task(name="Impermeabilização", obra="Obra B", responsible="Marcos", priority=TaskPriority.BAIXA))

        results_a = self.repo.list_tasks(obra="Obra A")
        self.assertEqual(len(results_a), 2)

        results_search = self.repo.list_tasks(search="Impermeab")
        self.assertEqual(len(results_search), 1)
        self.assertEqual(results_search[0].name, "Impermeabilização")

    def test_metrics_calculation(self):
        today = date.today()
        yesterday = today - timedelta(days=1)
        tomorrow = today + timedelta(days=2)

        # 1 concluída
        self.repo.create(Task(name="T1", obra="Obra 1", status=TaskStatus.CONCLUIDA))
        # 1 atrasada
        self.repo.create(Task(name="T2", obra="Obra 1", end_date=yesterday, status=TaskStatus.EM_ANDAMENTO))
        # 1 no prazo
        self.repo.create(Task(name="T3", obra="Obra 2", end_date=tomorrow, status=TaskStatus.PENDENTE))

        metrics = self.repo.get_dashboard_metrics()
        self.assertEqual(metrics.total, 3)
        self.assertEqual(metrics.concluidas, 1)
        self.assertEqual(metrics.atrasadas, 1)
        self.assertEqual(metrics.em_andamento, 1)
        self.assertEqual(metrics.pendentes, 1)
        self.assertEqual(metrics.taxa_conclusao, 33.3)
        self.assertEqual(metrics.obras_ativas, 2)

if __name__ == "__main__":
    unittest.main()

