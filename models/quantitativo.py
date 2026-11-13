from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional, List, Dict, Any
from .task import parse_date_str, format_date_br, format_date_iso

@dataclass
class LancamentoItem:
    """Item de lançamento geométrico de concreto e formas."""
    id: Optional[int] = None
    quantitativo_id: Optional[int] = None
    elemento: str = "B101"
    tipo: str = "Bloco"  # Bloco, Pilar, Viga, Laje, Sapata, Estaca, Escada
    local: str = ""
    pecas: int = 1
    largura: float = 0.0      # metros
    comprimento: float = 0.0  # metros
    altura: float = 0.0       # metros
    qtd: float = 1.0
    concreto_m3: float = 0.0
    formas_m2: float = 0.0
    execucao: str = "Não executado"  # Não executado, Executado

    @property
    def is_executado(self) -> bool:
        return self.execucao == "Executado"

    @property
    def dimensoes_display(self) -> str:
        def fmt(v):
            return f"{v:g}".replace(".", ",")
        return f"L {fmt(self.largura)} · C {fmt(self.comprimento)} · H {fmt(self.altura)}"

    def calculate_metrics(self) -> None:
        """Calcula volume de concreto (m³) e área de formas (m²) conforme geometria."""
        fator_qtd = self.pecas * self.qtd
        # Concreto (m³)
        self.concreto_m3 = round(self.comprimento * self.largura * self.altura * fator_qtd, 3)

        # Formas (m²)
        tipo_lower = self.tipo.lower()
        if "laje" in tipo_lower:
            # Área de fundo
            self.formas_m2 = round(self.comprimento * self.largura * fator_qtd, 2)
        elif "viga" in tipo_lower:
            # Fundo + 2 laterais
            self.formas_m2 = round((self.largura + 2 * self.altura) * self.comprimento * fator_qtd, 2)
        else:
            # Bloco, Pilar, Sapata: perímetro x altura
            perimetro = 2 * (self.largura + self.comprimento)
            self.formas_m2 = round(perimetro * self.altura * fator_qtd, 2)

    @classmethod
    def from_row(cls, row: Any) -> "LancamentoItem":
        d = dict(row)
        item = cls(
            id=d.get("id"),
            quantitativo_id=d.get("quantitativo_id"),
            elemento=d.get("elemento") or "Peça",
            tipo=d.get("tipo") or "Bloco",
            local=d.get("local") or "",
            pecas=int(d.get("pecas", 1)),
            largura=float(d.get("largura", 0.0)),
            comprimento=float(d.get("comprimento", 0.0)),
            altura=float(d.get("altura", 0.0)),
            qtd=float(d.get("qtd", 1.0)),
            concreto_m3=float(d.get("concreto_m3", 0.0)),
            formas_m2=float(d.get("formas_m2", 0.0)),
            execucao=d.get("execucao") or "Não executado"
        )
        if item.concreto_m3 == 0.0 and item.comprimento > 0:
            item.calculate_metrics()
        return item


@dataclass
class Quantitativo:
    """Quantitativo executivo de obra com controle de concreto, formas e avanço físico."""
    id: Optional[int] = None
    codigo: str = ""
    disciplina: str = "Estrutural"  # Estrutural (Concreto e formas) ou Alvenaria
    obra: str = "Chronos"
    torre_setor: str = "TORRE 01 E 02"
    pavimento: str = "FUNDAÇÃO"
    folha_projeto: str = "—"
    revisao: str = "R02"
    data_levantamento: Optional[date] = None
    responsavel: str = "Gil Márcio Bispo de Jesus Júnior"
    status: str = "finalizado"  # finalizado, em andamento, em revisão
    observacoes: str = ""
    lancamentos: List[LancamentoItem] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @property
    def titulo_completo(self) -> str:
        return f"{self.disciplina} · {self.pavimento.upper()}"

    @property
    def subtitulo_completo(self) -> str:
        folha_txt = f"Folha {self.folha_projeto} · " if self.folha_projeto and self.folha_projeto != "—" else ""
        return f"{self.obra.upper()} · {self.torre_setor.upper()} · Rev. {self.revisao} · {self.status}"

    @property
    def data_levantamento_br(self) -> str:
        return format_date_br(self.data_levantamento)

    @property
    def concreto_total(self) -> float:
        return round(sum(l.concreto_m3 for l in self.lancamentos), 3)

    @property
    def concreto_executado(self) -> float:
        return round(sum(l.concreto_m3 for l in self.lancamentos if l.is_executado), 3)

    @property
    def formas_total(self) -> float:
        return round(sum(l.formas_m2 for l in self.lancamentos), 2)

    @property
    def formas_executadas(self) -> float:
        return round(sum(l.formas_m2 for l in self.lancamentos if l.is_executado), 2)

    @property
    def percentual_execucao(self) -> float:
        total = self.concreto_total
        if total == 0:
            return 0.0
        return round((self.concreto_executado / total) * 100, 1)

    @property
    def total_lancamentos(self) -> int:
        return len(self.lancamentos)

    @classmethod
    def from_row(cls, row: Any, lancamentos: Optional[List[LancamentoItem]] = None) -> "Quantitativo":
        d = dict(row)
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
            codigo=d.get("codigo") or "",
            disciplina=d.get("disciplina") or "Estrutural",
            obra=d.get("obra") or "Geral",
            torre_setor=d.get("torre_setor") or "Torre A",
            pavimento=d.get("pavimento") or "Geral",
            folha_projeto=d.get("folha_projeto") or "—",
            revisao=d.get("revisao") or "R01",
            data_levantamento=parse_date_str(d.get("data_levantamento")),
            responsavel=d.get("responsavel") or "Engenheiro",
            status=d.get("status") or "finalizado",
            observacoes=d.get("observacoes") or "",
            lancamentos=lancamentos or [],
            created_at=parse_dt(d.get("created_at")),
            updated_at=parse_dt(d.get("updated_at"))
        )
