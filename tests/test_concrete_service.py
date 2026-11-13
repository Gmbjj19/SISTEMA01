import unittest
import tempfile
import os
from pathlib import Path
from datetime import date
from database.connection import DatabaseManager
from database.migrator import init_database
from models.concrete import ConcreteMeasurement, ConcreteItem
from repositories.concrete_repository import ConcreteRepository
from services.concrete_service import ConcreteService
from services.pdf_report_service import ConcretePDFService

class TestConcreteService(unittest.TestCase):
    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_file.close()
        self.db_path = Path(self.temp_file.name)
        self.manager = DatabaseManager(self.db_path)
        init_database(self.manager)
        self.repo = ConcreteRepository(self.manager)
        self.pdf_service = ConcretePDFService()
        self.service = ConcreteService(self.repo, self.pdf_service)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_volume_calculation(self):
        item = ConcreteItem(elemento="Viga V1", tipo="Viga", comprimento=5.0, largura=0.20, altura=0.50, quantidade=4)
        vol = item.calculate_volume()
        # 5 * 0.20 * 0.50 = 0.50 m3 cada * 4 = 2.0 m3
        self.assertEqual(item.volume_unitario, 0.50)
        self.assertEqual(vol, 2.0)

    def test_create_and_calculate_measurement(self):
        data = {
            "obra": "Residencial Bela Vista",
            "elemento": "Vigas e Lajes do 2º Pavimento",
            "data_concretagem": "15/11/2026",
            "fck_mpa": 35,
            "slump_cm": 14.0,
            "brita_tipo": "Brita 1",
            "perda_percentual": 5.0,
            "fornecedor": "Polimix Concreto",
            "responsavel": "Eng. Roberto",
            "itens": [
                {"elemento": "Laje L1", "tipo": "Laje", "comprimento": 10.0, "largura": 8.0, "altura": 0.12, "quantidade": 1},
                {"elemento": "Vigas V1-V4", "tipo": "Viga", "comprimento": 8.0, "largura": 0.20, "altura": 0.60, "quantidade": 4}
            ]
        }
        # Laje: 10 * 8 * 0.12 = 9.6 m3
        # Vigas: 8 * 0.20 * 0.60 * 4 = 3.84 m3
        # Teórico: 9.6 + 3.84 = 13.44 m3
        # Total (+5%): 13.44 * 1.05 = 14.112 -> 14.11 m3
        bm, err = self.service.create_measurement(data)
        self.assertIsNone(err)
        self.assertIsNotNone(bm)
        self.assertTrue(bm.boletim_code.startswith("BM-"))
        self.assertEqual(bm.volume_teorico, 13.44)
        self.assertEqual(bm.volume_total, 14.11)

    def test_generate_pdf(self):
        data = {
            "obra": "Edifício Metropolitan",
            "elemento": "Concretagem dos Pilares P1 a P12",
            "data_concretagem": "18/11/2026",
            "fck_mpa": 40,
            "slump_cm": 12.0,
            "brita_tipo": "Brita 1",
            "perda_percentual": 6.0,
            "fornecedor": "Supermix Concreto",
            "responsavel": "Eng. Carlos Gil",
            "observacoes": "Concretagem com bomba lança de 36m. Moldados 4 CPs.",
            "itens": [
                {"elemento": "Pilares P1 a P6", "tipo": "Pilar", "comprimento": 0.25, "largura": 0.60, "altura": 3.0, "quantidade": 6},
                {"elemento": "Pilares P7 a P12", "tipo": "Pilar", "comprimento": 0.30, "largura": 0.80, "altura": 3.0, "quantidade": 6}
            ]
        }
        bm, _ = self.service.create_measurement(data)
        temp_pdf = Path(tempfile.gettempdir()) / f"teste_{bm.boletim_code}.pdf"
        output_pdf = self.service.export_pdf(bm.id, temp_pdf)
        self.assertTrue(output_pdf.exists())
        self.assertGreater(output_pdf.stat().st_size, 2000)
        if output_pdf.exists():
            os.remove(output_pdf)

if __name__ == "__main__":
    unittest.main()

