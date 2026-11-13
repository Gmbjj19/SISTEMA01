import unittest
import tempfile
import os
from pathlib import Path
from database.connection import DatabaseManager
from database.migrator import init_database, seed_sample_quantitativos_if_needed
from repositories.quantitativo_repository import QuantitativoRepository
from services.quantitativo_service import QuantitativoService
from services.pdf_report_service import ConcretePDFService

class TestQuantitativoService(unittest.TestCase):
    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_file.close()
        self.db_path = Path(self.temp_file.name)
        self.manager = DatabaseManager(self.db_path)
        init_database(self.manager)
        seed_sample_quantitativos_if_needed(self.manager)
        self.repo = QuantitativoRepository(self.manager)
        self.pdf_service = ConcretePDFService()
        self.service = QuantitativoService(self.repo, self.pdf_service)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_chronos_seeded_quantitativo(self):
        quantitativos = self.service.list_quantitativos()
        self.assertEqual(len(quantitativos), 1)
        q = quantitativos[0]
        self.assertEqual(q.obra, "CHRONOS")
        self.assertEqual(q.pavimento, "FUNDAÇÃO")
        self.assertEqual(q.revisao, "R02")
        self.assertEqual(q.total_lancamentos, 15)
        self.assertEqual(q.formas_total, 161.08)
        self.assertAlmostEqual(q.concreto_total, 64.746, places=2)

    def test_toggle_execucao(self):
        q = self.service.list_quantitativos()[0]
        item_id = q.lancamentos[0].id
        self.assertFalse(q.lancamentos[0].is_executado)

        # Alternar para executado
        new_status = self.service.toggle_execucao(item_id)
        self.assertEqual(new_status, "Executado")

        reloaded = self.service.get_quantitativo(q.id)
        self.assertTrue(reloaded.lancamentos[0].is_executado)
        self.assertGreater(reloaded.concreto_executado, 0.0)

    def test_generate_quantitativo_pdf(self):
        q = self.service.list_quantitativos()[0]
        temp_pdf = Path(tempfile.gettempdir()) / f"teste_quant_{q.codigo}.pdf"
        output_pdf = self.service.export_pdf(q.id, temp_pdf)
        self.assertTrue(output_pdf.exists())
        self.assertGreater(output_pdf.stat().st_size, 3000)
        if output_pdf.exists():
            os.remove(output_pdf)

if __name__ == "__main__":
    unittest.main()
