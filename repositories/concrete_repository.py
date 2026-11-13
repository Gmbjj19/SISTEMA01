import sqlite3
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from config import LOGGER
from database.connection import DatabaseManager, db_manager
from models.concrete import ConcreteMeasurement

class ConcreteRepository:
    """Repositório de acesso a dados para Boletins de Medição de Concreto."""
    def __init__(self, manager: DatabaseManager = db_manager):
        self.manager = manager

    def get_next_boletim_code(self) -> str:
        current_year = date.today().year
        prefix = f"BM-{current_year}-"
        sql = "SELECT boletim_code FROM concrete_measurements WHERE boletim_code LIKE ? ORDER BY id DESC LIMIT 1"
        with self.manager.get_connection() as conn:
            row = conn.execute(sql, (f"{prefix}%",)).fetchone()
            if row:
                last_code = row["boletim_code"]
                try:
                    seq = int(last_code.split("-")[-1]) + 1
                except ValueError:
                    seq = 1
            else:
                seq = 1
        return f"{prefix}{seq:03d}"

    def create(self, bm: ConcreteMeasurement) -> ConcreteMeasurement:
        if not bm.boletim_code:
            bm.boletim_code = self.get_next_boletim_code()

        sql = """
            INSERT INTO concrete_measurements (
                boletim_code, obra, elemento, data_concretagem,
                fck_mpa, slump_cm, brita_tipo, volume_teorico, perda_percentual, volume_total,
                fornecedor, nota_fiscal, lacres, corpos_prova, responsavel, status,
                observacoes, itens_json, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
        """
        params = (
            bm.boletim_code,
            bm.obra,
            bm.elemento,
            bm.data_concretagem_iso or date.today().strftime("%Y-%m-%d"),
            bm.fck_mpa,
            bm.slump_cm,
            bm.brita_tipo,
            bm.volume_teorico,
            bm.perda_percentual,
            bm.volume_total,
            bm.fornecedor,
            bm.nota_fiscal,
            bm.lacres,
            bm.corpos_prova,
            bm.responsavel,
            bm.status,
            bm.observacoes,
            bm.itens_to_json()
        )
        with self.manager.get_connection() as conn:
            cursor = conn.execute(sql, params)
            bm.id = cursor.lastrowid
        LOGGER.info("Boletim de Medição criado: %s (ID %d)", bm.boletim_code, bm.id)
        return bm

    def update(self, bm: ConcreteMeasurement) -> bool:
        if bm.id is None:
            raise ValueError("Não é possível atualizar boletim sem ID.")
        sql = """
            UPDATE concrete_measurements SET
                obra = ?, elemento = ?, data_concretagem = ?,
                fck_mpa = ?, slump_cm = ?, brita_tipo = ?,
                volume_teorico = ?, perda_percentual = ?, volume_total = ?,
                fornecedor = ?, nota_fiscal = ?, lacres = ?, corpos_prova = ?,
                responsavel = ?, status = ?, observacoes = ?, itens_json = ?,
                updated_at = datetime('now')
            WHERE id = ?
        """
        params = (
            bm.obra,
            bm.elemento,
            bm.data_concretagem_iso or date.today().strftime("%Y-%m-%d"),
            bm.fck_mpa,
            bm.slump_cm,
            bm.brita_tipo,
            bm.volume_teorico,
            bm.perda_percentual,
            bm.volume_total,
            bm.fornecedor,
            bm.nota_fiscal,
            bm.lacres,
            bm.corpos_prova,
            bm.responsavel,
            bm.status,
            bm.observacoes,
            bm.itens_to_json(),
            bm.id
        )
        with self.manager.get_connection() as conn:
            cursor = conn.execute(sql, params)
            return cursor.rowcount > 0

    def delete(self, bm_id: int) -> bool:
        sql = "DELETE FROM concrete_measurements WHERE id = ?"
        with self.manager.get_connection() as conn:
            cursor = conn.execute(sql, (bm_id,))
            return cursor.rowcount > 0

    def get_by_id(self, bm_id: int) -> Optional[ConcreteMeasurement]:
        sql = "SELECT * FROM concrete_measurements WHERE id = ?"
        with self.manager.get_connection() as conn:
            row = conn.execute(sql, (bm_id,)).fetchone()
            if row:
                return ConcreteMeasurement.from_row(row)
        return None

    def list_all(self, search: str = "", obra: Optional[str] = None) -> List[ConcreteMeasurement]:
        query = "SELECT * FROM concrete_measurements WHERE 1=1"
        params: List[Any] = []

        if search:
            query += " AND (boletim_code LIKE ? OR elemento LIKE ? OR obra LIKE ? OR responsavel LIKE ? OR fornecedor LIKE ?)"
            term = f"%{search.strip()}%"
            params.extend([term, term, term, term, term])

        if obra and obra != "Todas":
            query += " AND obra = ?"
            params.append(obra)

        query += " ORDER BY id DESC"

        with self.manager.get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [ConcreteMeasurement.from_row(r) for r in rows]

    def get_stats(self) -> Dict[str, Any]:
        with self.manager.get_connection() as conn:
            total_bms = conn.execute("SELECT COUNT(*) as c FROM concrete_measurements").fetchone()["c"]
            total_volume = conn.execute("SELECT COALESCE(SUM(volume_total), 0.0) as s FROM concrete_measurements").fetchone()["s"]
            obras_count = conn.execute("SELECT COUNT(DISTINCT obra) as c FROM concrete_measurements WHERE obra IS NOT NULL").fetchone()["c"]
            media_fck = conn.execute("SELECT COALESCE(AVG(fck_mpa), 30.0) as m FROM concrete_measurements").fetchone()["m"]

        return {
            "total_boletins": total_bms,
            "volume_total_m3": round(total_volume, 1),
            "obras_atendidas": obras_count,
            "fck_medio": round(media_fck, 0)
        }
