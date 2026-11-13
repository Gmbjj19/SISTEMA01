from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any
from datetime import date

from config import LOGGER
from models.concrete import ConcreteMeasurement, ConcreteItem
from models.task import parse_date_str
from repositories.concrete_repository import ConcreteRepository
from services.pdf_report_service import ConcretePDFService

class ConcreteService:
    """Serviço de negócio para gestão de medições, cubagem geométrica e emissão de PDFs."""
    def __init__(
        self,
        repository: Optional[ConcreteRepository] = None,
        pdf_service: Optional[ConcretePDFService] = None
    ):
        self.repository = repository or ConcreteRepository()
        self.pdf_service = pdf_service or ConcretePDFService()

    def validate_payload(self, data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        obra = (data.get("obra") or "").strip()
        if not obra:
            return False, "O nome do canteiro / obra é obrigatório."

        elemento = (data.get("elemento") or "").strip()
        if not elemento:
            return False, "A descrição do elemento / peça concretada é obrigatória."

        data_c = data.get("data_concretagem")
        if data_c and isinstance(data_c, str):
            parsed = parse_date_str(data_c)
            if not parsed:
                return False, "Data de concretagem inválida (utilize DD/MM/AAAA)."

        return True, None

    def create_measurement(self, data: Dict[str, Any]) -> Tuple[Optional[ConcreteMeasurement], Optional[str]]:
        valid, err = self.validate_payload(data)
        if not valid:
            return None, err

        itens_data = data.get("itens", [])
        itens = [
            it if isinstance(it, ConcreteItem) else ConcreteItem.from_dict(it)
            for it in itens_data
        ]

        bm = ConcreteMeasurement(
            obra=data["obra"].strip(),
            elemento=data["elemento"].strip(),
            data_concretagem=parse_date_str(data.get("data_concretagem")) if isinstance(data.get("data_concretagem"), str) else data.get("data_concretagem", date.today()),
            fck_mpa=int(data.get("fck_mpa", 30)),
            slump_cm=float(data.get("slump_cm", 12.0)),
            brita_tipo=data.get("brita_tipo", "Brita 1"),
            itens=itens,
            perda_percentual=float(data.get("perda_percentual", 5.0)),
            fornecedor=(data.get("fornecedor") or "").strip(),
            nota_fiscal=(data.get("nota_fiscal") or "").strip(),
            lacres=(data.get("lacres") or "").strip(),
            corpos_prova=int(data.get("corpos_prova", 4)),
            responsavel=(data.get("responsavel") or "Eng. Responsável").strip(),
            status=data.get("status", "Concluído"),
            observacoes=(data.get("observacoes") or "").strip()
        )

        bm.calculate_totals()
        if bm.volume_total == 0.0 and "volume_informado" in data:
            bm.volume_teorico = float(data["volume_informado"])
            bm.volume_total = round(bm.volume_teorico * (1.0 + (bm.perda_percentual / 100.0)), 2)

        created = self.repository.create(bm)
        return created, None

    def list_measurements(self, search: str = "", obra: Optional[str] = None) -> List[ConcreteMeasurement]:
        return self.repository.list_all(search=search, obra=obra)

    def delete_measurement(self, bm_id: int) -> bool:
        return self.repository.delete(bm_id)

    def get_stats(self) -> Dict[str, Any]:
        return self.repository.get_stats()

    def export_pdf(self, bm_id: int, output_path: Path) -> Path:
        bm = self.repository.get_by_id(bm_id)
        if not bm:
            raise ValueError(f"Boletim #{bm_id} não encontrado.")
        return self.pdf_service.generate_pdf(bm, output_path)

