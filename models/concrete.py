from dataclasses import dataclass, field, asdict
from datetime import date, datetime
from typing import Optional, List, Dict, Any
import json
from .task import parse_date_str, format_date_br, format_date_iso

@dataclass
class ConcreteItem:
    """Item geométrico para cálculo de cubagem de concreto."""
    elemento: str
    tipo: str = "Pilar"  # Pilar, Viga, Laje, Sapata/Bloco, Estaca, Escada, Outro
    comprimento: float = 0.0  # metros
    largura: float = 0.0      # metros
    altura: float = 0.0       # metros (ou espessura)
    quantidade: int = 1
    volume_unitario: float = 0.0
    volume_total: float = 0.0

    def calculate_volume(self) -> float:
        self.volume_unitario = round(self.comprimento * self.largura * self.altura, 3)
        self.volume_total = round(self.volume_unitario * self.quantidade, 3)
        return self.volume_total

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConcreteItem":
        item = cls(
            elemento=data.get("elemento", "Elemento"),
            tipo=data.get("tipo", "Pilar"),
            comprimento=float(data.get("comprimento", 0.0)),
            largura=float(data.get("largura", 0.0)),
            altura=float(data.get("altura", 0.0)),
            quantidade=int(data.get("quantidade", 1)),
            volume_unitario=float(data.get("volume_unitario", 0.0)),
            volume_total=float(data.get("volume_total", 0.0))
        )
        if item.volume_total == 0.0 and item.comprimento > 0:
            item.calculate_volume()
        return item


@dataclass
class ConcreteMeasurement:
    """Boletim de Medição & Controle Tecnológico de Concreto Usinado."""
    id: Optional[int] = None
    boletim_code: str = ""
    obra: str = ""
    elemento: str = ""
    data_concretagem: Optional[date] = None
    fck_mpa: int = 30
    slump_cm: float = 12.0
    brita_tipo: str = "Brita 1"
    itens: List[ConcreteItem] = field(default_factory=list)
    volume_teorico: float = 0.0
    perda_percentual: float = 5.0
    volume_total: float = 0.0
    fornecedor: str = ""
    nota_fiscal: str = ""
    lacres: str = ""
    corpos_prova: int = 4
    responsavel: str = ""
    status: str = "Concluído"
    observacoes: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @property
    def data_concretagem_br(self) -> str:
        return format_date_br(self.data_concretagem)

    @property
    def data_concretagem_iso(self) -> str:
        return format_date_iso(self.data_concretagem)

    def calculate_totals(self) -> None:
        """Recalcula o volume teórico somando os itens e aplica a margem de perda."""
        teorico = sum(item.calculate_volume() for item in self.itens)
        self.volume_teorico = round(teorico, 3)
        fator = 1.0 + (self.perda_percentual / 100.0)
        self.volume_total = round(self.volume_teorico * fator, 2)

    def itens_to_json(self) -> str:
        return json.dumps([item.to_dict() for item in self.itens], ensure_ascii=False)

    @classmethod
    def from_row(cls, row: Any) -> "ConcreteMeasurement":
        d = dict(row)
        itens_raw = d.get("itens_json") or "[]"
        try:
            parsed_itens = json.loads(itens_raw)
            itens = [ConcreteItem.from_dict(it) for it in parsed_itens]
        except Exception:
            itens = []

        def parse_dt(ts):
            if not ts:
                return None
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
                try:
                    return datetime.strptime(str(ts)[:19], fmt)
                except ValueError:
                    pass
            return None

        return cls(
            id=d.get("id"),
            boletim_code=d.get("boletim_code") or "",
            obra=d.get("obra") or "Geral",
            elemento=d.get("elemento") or "",
            data_concretagem=parse_date_str(d.get("data_concretagem")),
            fck_mpa=int(d.get("fck_mpa", 30)),
            slump_cm=float(d.get("slump_cm", 12.0)),
            brita_tipo=d.get("brita_tipo", "Brita 1"),
            itens=itens,
            volume_teorico=float(d.get("volume_teorico", 0.0)),
            perda_percentual=float(d.get("perda_percentual", 5.0)),
            volume_total=float(d.get("volume_total", 0.0)),
            fornecedor=d.get("fornecedor") or "",
            nota_fiscal=d.get("nota_fiscal") or "",
            lacres=d.get("lacres") or "",
            corpos_prova=int(d.get("corpos_prova", 4)),
            responsavel=d.get("responsavel") or "",
            status=d.get("status") or "Concluído",
            observacoes=d.get("observacoes") or "",
            created_at=parse_dt(d.get("created_at")),
            updated_at=parse_dt(d.get("updated_at"))
        )

