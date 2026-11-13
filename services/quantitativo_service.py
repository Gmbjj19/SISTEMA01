from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any
from datetime import date

from config import LOGGER
from models.quantitativo import Quantitativo, LancamentoItem
from models.task import parse_date_str
from repositories.quantitativo_repository import QuantitativoRepository
from services.pdf_report_service import ConcretePDFService

class QuantitativoService:
    """Serviço para orquestração de quantitativos estruturais de concreto e formas."""
    def __init__(
        self,
        repository: Optional[QuantitativoRepository] = None,
        pdf_service: Optional[ConcretePDFService] = None
    ):
        self.repository = repository or QuantitativoRepository()
        self.pdf_service = pdf_service or ConcretePDFService()

    def create_quantitativo(self, data: Dict[str, Any]) -> Tuple[Optional[Quantitativo], Optional[str]]:
        obra = (data.get("obra") or "").strip()
        if not obra or obra == "Selecione a obra":
            return None, "Selecione a obra para o quantitativo."

        pavimento = (data.get("pavimento") or "").strip()
        if not pavimento:
            return None, "O pavimento / etapa é obrigatório (ex: Fundação, 3º pavimento)."

        torre_setor = (data.get("torre_setor") or "").strip() or "Geral"
        disciplina = data.get("disciplina") or "Estrutural"
        folha = (data.get("folha_projeto") or "—").strip()
        revisao = (data.get("revisao") or "R01").strip()
        responsavel = (data.get("responsavel") or "Gil Márcio Bispo de Jesus Júnior").strip()

        data_lev = data.get("data_levantamento")
        if isinstance(data_lev, str):
            data_lev = parse_date_str(data_lev) or date.today()
        elif not data_lev:
            data_lev = date.today()

        q = Quantitativo(
            disciplina=disciplina,
            obra=obra,
            torre_setor=torre_setor,
            pavimento=pavimento,
            folha_projeto=folha,
            revisao=revisao,
            data_levantamento=data_lev,
            responsavel=responsavel,
            status="finalizado",
            observacoes=(data.get("observacoes") or "").strip()
        )

        created = self.repository.create_quantitativo(q)
        return created, None

    def get_quantitativo(self, q_id: int) -> Optional[Quantitativo]:
        return self.repository.get_by_id(q_id)

    def list_quantitativos(self, search: str = "", obra: Optional[str] = None) -> List[Quantitativo]:
        return self.repository.list_all(search=search, obra=obra)

    def add_lancamento(self, q_id: int, data: Dict[str, Any]) -> Tuple[Optional[LancamentoItem], Optional[str]]:
        elemento = (data.get("elemento") or "").strip()
        if not elemento:
            return None, "O nome ou identificação do elemento é obrigatório."

        try:
            l = float(data.get("largura", 0.0))
            c = float(data.get("comprimento", 0.0))
            h = float(data.get("altura", 0.0))
            pecas = int(data.get("pecas", 1))
            qtd = float(data.get("qtd", 1.0))
        except ValueError:
            return None, "Dimensões e quantidades devem ser números válidos."

        item = LancamentoItem(
            quantitativo_id=q_id,
            elemento=elemento,
            tipo=data.get("tipo", "Bloco"),
            local=data.get("local", ""),
            pecas=pecas,
            largura=l,
            comprimento=c,
            altura=h,
            qtd=qtd,
            execucao=data.get("execucao", "Não executado")
        )
        saved = self.repository.add_lancamento(item)
        return saved, None

    def delete_lancamento(self, item_id: int) -> bool:
        return self.repository.delete_lancamento(item_id)

    def toggle_execucao(self, item_id: int) -> Optional[str]:
        return self.repository.toggle_execucao_lancamento(item_id)

    def reopen_for_correction(self, q_id: int) -> bool:
        return self.repository.reopen_for_correction(q_id)

    def create_revision(self, q_id: int) -> Optional[Quantitativo]:
        return self.repository.create_revision(q_id)

    def delete_quantitativo(self, q_id: int) -> bool:
        return self.repository.delete_quantitativo(q_id)

    def export_pdf(self, q_id: int, output_path: Path) -> Path:
        q = self.repository.get_by_id(q_id)
        if not q:
            raise ValueError(f"Quantitativo #{q_id} não encontrado.")
        return self.pdf_service.generate_quantitativo_pdf(q, output_path)

    def get_stats(self) -> Dict[str, Any]:
        return self.repository.get_stats()

