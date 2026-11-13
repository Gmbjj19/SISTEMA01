import sqlite3
from typing import List, Optional, Dict, Any
from datetime import date
from config import LOGGER
from database.connection import DatabaseManager, db_manager
from models.quantitativo import Quantitativo, LancamentoItem

class QuantitativoRepository:
    """Repositório de acesso a dados para Quantitativos de Concreto e Lançamentos."""
    def __init__(self, manager: DatabaseManager = db_manager):
        self.manager = manager

    def _get_next_code(self, obra: str) -> str:
        clean_obra = obra.upper().replace(" ", "")[:4] or "OBRA"
        prefix = f"QNT-{clean_obra}-"
        sql = "SELECT codigo FROM quantitativos WHERE codigo LIKE ? ORDER BY id DESC LIMIT 1"
        with self.manager.get_connection() as conn:
            row = conn.execute(sql, (f"{prefix}%",)).fetchone()
            if row:
                try:
                    num = int(row["codigo"].split("-")[-1]) + 1
                except ValueError:
                    num = 1
            else:
                num = 1
        return f"{prefix}{num:02d}"

    def create_quantitativo(self, q: Quantitativo) -> Quantitativo:
        if not q.codigo:
            q.codigo = self._get_next_code(q.obra)

        sql = """
            INSERT INTO quantitativos (
                codigo, disciplina, obra, torre_setor, pavimento, folha_projeto,
                revisao, data_levantamento, responsavel, status, observacoes,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
        """
        params = (
            q.codigo,
            q.disciplina,
            q.obra,
            q.torre_setor,
            q.pavimento,
            q.folha_projeto,
            q.revisao,
            q.data_levantamento_iso or date.today().strftime("%Y-%m-%d"),
            q.responsavel,
            q.status,
            q.observacoes
        )
        with self.manager.get_connection() as conn:
            cursor = conn.execute(sql, params)
            q.id = cursor.lastrowid

            # Inserir lançamentos se houver
            for item in q.lancamentos:
                item.quantitativo_id = q.id
                item.calculate_metrics()
                conn.execute("""
                    INSERT INTO lancamentos (
                        quantitativo_id, elemento, tipo, local, pecas, largura,
                        comprimento, altura, qtd, concreto_m3, formas_m2, execucao
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    q.id, item.elemento, item.tipo, item.local, item.pecas,
                    item.largura, item.comprimento, item.altura, item.qtd,
                    item.concreto_m3, item.formas_m2, item.execucao
                ))

        LOGGER.info("Quantitativo criado: ID %d - %s", q.id, q.codigo)
        return q

    def get_by_id(self, q_id: int) -> Optional[Quantitativo]:
        sql = "SELECT * FROM quantitativos WHERE id = ?"
        with self.manager.get_connection() as conn:
            row = conn.execute(sql, (q_id,)).fetchone()
            if not row:
                return None
            
            # Buscar lançamentos
            lanc_rows = conn.execute(
                "SELECT * FROM lancamentos WHERE quantitativo_id = ? ORDER BY id ASC", (q_id,)
            ).fetchall()
            lancamentos = [LancamentoItem.from_row(r) for r in lanc_rows]
            return Quantitativo.from_row(row, lancamentos=lancamentos)

    def list_all(self, search: str = "", obra: Optional[str] = None) -> List[Quantitativo]:
        query = "SELECT * FROM quantitativos WHERE 1=1"
        params: List[Any] = []

        if search:
            query += " AND (codigo LIKE ? OR obra LIKE ? OR torre_setor LIKE ? OR pavimento LIKE ? OR responsavel LIKE ?)"
            term = f"%{search.strip()}%"
            params.extend([term, term, term, term, term])

        if obra and obra != "Todas":
            query += " AND obra = ?"
            params.append(obra)

        query += " ORDER BY id DESC"

        result = []
        with self.manager.get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            for r in rows:
                q_id = r["id"]
                lanc_rows = conn.execute(
                    "SELECT * FROM lancamentos WHERE quantitativo_id = ? ORDER BY id ASC", (q_id,)
                ).fetchall()
                lancamentos = [LancamentoItem.from_row(lr) for lr in lanc_rows]
                result.append(Quantitativo.from_row(r, lancamentos=lancamentos))
        return result

    def add_lancamento(self, item: LancamentoItem) -> LancamentoItem:
        item.calculate_metrics()
        sql = """
            INSERT INTO lancamentos (
                quantitativo_id, elemento, tipo, local, pecas, largura,
                comprimento, altura, qtd, concreto_m3, formas_m2, execucao
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            item.quantitativo_id, item.elemento, item.tipo, item.local,
            item.pecas, item.largura, item.comprimento, item.altura, item.qtd,
            item.concreto_m3, item.formas_m2, item.execucao
        )
        with self.manager.get_connection() as conn:
            cursor = conn.execute(sql, params)
            item.id = cursor.lastrowid
        return item

    def delete_lancamento(self, item_id: int) -> bool:
        with self.manager.get_connection() as conn:
            cursor = conn.execute("DELETE FROM lancamentos WHERE id = ?", (item_id,))
            return cursor.rowcount > 0

    def toggle_execucao_lancamento(self, item_id: int) -> Optional[str]:
        with self.manager.get_connection() as conn:
            row = conn.execute("SELECT execucao FROM lancamentos WHERE id = ?", (item_id,)).fetchone()
            if not row:
                return None
            curr = row["execucao"]
            new_val = "Executado" if curr == "Não executado" else "Não executado"
            conn.execute("UPDATE lancamentos SET execucao = ? WHERE id = ?", (new_val, item_id))
            return new_val

    def reopen_for_correction(self, q_id: int) -> bool:
        with self.manager.get_connection() as conn:
            cursor = conn.execute(
                "UPDATE quantitativos SET status = 'em revisão', updated_at = datetime('now') WHERE id = ?",
                (q_id,)
            )
            return cursor.rowcount > 0

    def create_revision(self, q_id: int) -> Optional[Quantitativo]:
        """Clona o quantitativo criando uma nova revisão (ex: R02 -> R03)."""
        original = self.get_by_id(q_id)
        if not original:
            return None

        # Calcular próximo código de revisão
        rev_str = original.revisao
        try:
            num = int(rev_str.replace("R", "").replace("r", "")) + 1
            next_rev = f"R{num:02d}"
        except ValueError:
            next_rev = f"{rev_str}-REV"

        new_q = Quantitativo(
            codigo="",
            disciplina=original.disciplina,
            obra=original.obra,
            torre_setor=original.torre_setor,
            pavimento=original.pavimento,
            folha_projeto=original.folha_projeto,
            revisao=next_rev,
            data_levantamento=date.today(),
            responsavel=original.responsavel,
            status="em andamento",
            observacoes=f"Revisão criada a partir de {original.codigo} ({original.revisao}).",
            lancamentos=[
                LancamentoItem(
                    elemento=l.elemento,
                    tipo=l.tipo,
                    local=l.local,
                    pecas=l.pecas,
                    largura=l.largura,
                    comprimento=l.comprimento,
                    altura=l.altura,
                    qtd=l.qtd,
                    execucao="Não executado"
                )
                for l in original.lancamentos
            ]
        )
        return self.create_quantitativo(new_q)

    def delete_quantitativo(self, q_id: int) -> bool:
        with self.manager.get_connection() as conn:
            conn.execute("DELETE FROM lancamentos WHERE quantitativo_id = ?", (q_id,))
            cursor = conn.execute("DELETE FROM quantitativos WHERE id = ?", (q_id,))
            return cursor.rowcount > 0

    def get_stats(self) -> Dict[str, Any]:
        with self.manager.get_connection() as conn:
            total_q = conn.execute("SELECT COUNT(*) as c FROM quantitativos").fetchone()["c"]
            obras_q = conn.execute("SELECT COUNT(DISTINCT obra) as c FROM quantitativos").fetchone()["c"]
            
            # Totais dos lançamentos
            row_l = conn.execute("""
                SELECT 
                    COALESCE(SUM(concreto_m3), 0.0) as total_concreto,
                    COALESCE(SUM(CASE WHEN execucao = 'Executado' THEN concreto_m3 ELSE 0.0 END), 0.0) as exec_concreto,
                    COALESCE(SUM(formas_m2), 0.0) as total_formas,
                    COALESCE(SUM(CASE WHEN execucao = 'Executado' THEN formas_m2 ELSE 0.0 END), 0.0) as exec_formas,
                    COUNT(*) as total_lancamentos
                FROM lancamentos
            """).fetchone()

        total_conc = round(row_l["total_concreto"], 3)
        exec_conc = round(row_l["exec_concreto"], 3)
        perc = round((exec_conc / total_conc) * 100, 1) if total_conc > 0 else 0.0

        return {
            "total_quantitativos": total_q,
            "obras_ativas": obras_q,
            "concreto_total_m3": total_conc,
            "concreto_executado_m3": exec_conc,
            "formas_total_m2": round(row_l["total_formas"], 2),
            "formas_executadas_m2": round(row_l["exec_formas"], 2),
            "percentual_execucao": perc,
            "total_lancamentos": row_l["total_lancamentos"]
        }

