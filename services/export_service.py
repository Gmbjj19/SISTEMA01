from pathlib import Path
from datetime import datetime, date
from typing import Optional, List, Any
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from config import LOGGER
from models.task import Task
from models.metrics import DashboardMetrics
from repositories.task_repository import TaskRepository

class ExportService:
    """Gera relatórios executivos em formato Excel (.xlsx) com estilização profissional."""
    def __init__(self, repository: Optional[TaskRepository] = None):
        self.repository = repository or TaskRepository()

    def export_tasks_to_excel(self, output_path: Path, tasks: Optional[List[Task]] = None) -> Path:
        """Gera arquivo Excel (.xlsx) completo com lista detalhada e aba de resumo executivo."""
        if tasks is None:
            tasks = self.repository.list_tasks(order_by="deadline")

        metrics = self.repository.get_dashboard_metrics()

        wb = openpyxl.Workbook()

        # Folha 1: Lista Detalhada
        ws_tasks = wb.active
        ws_tasks.title = "Controle de Tarefas"
        ws_tasks.views.sheetView[0].showGridLines = True

        # Paleta de Estilos
        font_title = Font(name="Segoe UI", size=15, bold=True, color="1E3A8A")
        font_sub = Font(name="Segoe UI", size=9, italic=True, color="475569")
        font_header = Font(name="Segoe UI", size=10, bold=True, color="FFFFFF")
        font_body = Font(name="Segoe UI", size=10, color="0F172A")
        font_bold = Font(name="Segoe UI", size=10, bold=True, color="0F172A")

        fill_header = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
        fill_zebra = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
        fill_white = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
        fill_overdue = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")
        fill_completed = PatternFill(start_color="DCFCE7", end_color="DCFCE7", fill_type="solid")

        border_thin = Border(
            left=Side(style='thin', color='E2E8F0'),
            right=Side(style='thin', color='E2E8F0'),
            top=Side(style='thin', color='E2E8F0'),
            bottom=Side(style='thin', color='E2E8F0')
        )

        align_center = Alignment(horizontal="center", vertical="center")
        align_left = Alignment(horizontal="left", vertical="center")

        # Título
        ws_tasks["A1"] = "RELATÓRIO EXECUTIVO DE OBRAS & TAREFAS"
        ws_tasks["A1"].font = font_title
        ws_tasks["A2"] = f"Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')} | Sistema Gestão Enterprise Senior"
        ws_tasks["A2"].font = font_sub

        # Cabeçalhos
        headers = [
            "ID", "Nome da Tarefa", "Obra", "Responsável", 
            "Data Início", "Data Término", "Prioridade", "Status", "Situação do Prazo", "Descrição"
        ]

        header_row = 4
        for col_idx, header_text in enumerate(headers, start=1):
            cell = ws_tasks.cell(row=header_row, column=col_idx, value=header_text)
            cell.font = font_header
            cell.fill = fill_header
            cell.alignment = align_center
            cell.border = border_thin
            ws_tasks.row_dimensions[header_row].height = 26

        # Inserção das Linhas de Tarefas
        for row_idx, t in enumerate(tasks, start=header_row + 1):
            is_zebra = (row_idx % 2 == 0)
            row_fill = fill_zebra if is_zebra else fill_white

            # Situação
            deadline_st = t.deadline_status.value
            if t.is_overdue:
                days = abs(t.days_remaining() or 0)
                deadline_st = f"Atrasada ({days}d)"

            values = [
                t.id,
                t.name,
                t.obra,
                t.responsible,
                t.start_date_br,
                t.end_date_br,
                t.priority.value,
                t.status.value,
                deadline_st,
                t.description
            ]

            for col_idx, val in enumerate(values, start=1):
                cell = ws_tasks.cell(row=row_idx, column=col_idx, value=val)
                cell.font = font_body
                cell.fill = row_fill
                cell.border = border_thin
                cell.alignment = align_center if col_idx in (1, 5, 6, 7, 8, 9) else align_left

                # Destaque de status
                if col_idx == 8 and t.is_completed:
                    cell.fill = fill_completed
                    cell.font = Font(name="Segoe UI", size=10, bold=True, color="166534")
                elif col_idx == 9 and t.is_overdue:
                    cell.fill = fill_overdue
                    cell.font = Font(name="Segoe UI", size=10, bold=True, color="991B1B")

            ws_tasks.row_dimensions[row_idx].height = 20

        # Ajuste Automático de Largura das Colunas
        for col in ws_tasks.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                if cell.row < 4:
                    continue
                if cell.value:
                    max_len = max(max_len, len(str(cell.value)))
            ws_tasks.column_dimensions[col_letter].width = max(max_len + 4, 12)

        ws_tasks.column_dimensions["A"].width = 8
        ws_tasks.column_dimensions["B"].width = 32
        ws_tasks.column_dimensions["J"].width = 30

        # Folha 2: Resumo Executivo e KPIs
        ws_summary = wb.create_sheet(title="Painel de Indicadores")
        ws_summary.views.sheetView[0].showGridLines = True

        ws_summary["A1"] = "PAINEL CONSOLIDADO DE INDICADORES (KPIs)"
        ws_summary["A1"].font = font_title
        ws_summary["A2"] = f"Posição das Obras em {date.today().strftime('%d/%m/%Y')}"
        ws_summary["A2"].font = font_sub

        kpis = [
            ("Total de Tarefas Registradas", metrics.total),
            ("Tarefas Concluídas", metrics.concluidas),
            ("Tarefas Em Andamento", metrics.em_andamento),
            ("Tarefas Atrasadas (Crítico)", metrics.atrasadas),
            ("Tarefas Vencendo Hoje", metrics.vencendo_hoje),
            ("Taxa Geral de Conclusão", f"{metrics.taxa_conclusao}%"),
            ("Obras com Tarefas Ativas", metrics.obras_ativas)
        ]

        ws_summary.row_dimensions[4].height = 24
        ws_summary.cell(row=4, column=1, value="Indicador").font = font_header
        ws_summary.cell(row=4, column=1).fill = fill_header
        ws_summary.cell(row=4, column=2, value="Valor").font = font_header
        ws_summary.cell(row=4, column=2).fill = fill_header

        for idx, (label, val) in enumerate(kpis, start=5):
            ws_summary.row_dimensions[idx].height = 20
            c1 = ws_summary.cell(row=idx, column=1, value=label)
            c2 = ws_summary.cell(row=idx, column=2, value=val)
            c1.font = font_body
            c2.font = font_bold
            c1.border = border_thin
            c2.border = border_thin
            c2.alignment = align_center

        # Tabela por Obra
        start_obra_row = 14
        ws_summary.cell(row=start_obra_row - 1, column=1, value="DISTRIBUIÇÃO POR OBRA").font = Font(name="Segoe UI", size=12, bold=True, color="1E3A8A")

        obra_headers = ["Obra", "Total", "Concluídas", "Em Andamento", "Atrasadas", "Progresso (%)"]
        for c_idx, h_text in enumerate(obra_headers, start=1):
            c = ws_summary.cell(row=start_obra_row, column=c_idx, value=h_text)
            c.font = font_header
            c.fill = fill_header
            c.alignment = align_center
            c.border = border_thin
        ws_summary.row_dimensions[start_obra_row].height = 24

        for r_idx, om in enumerate(metrics.obras_detalhes, start=start_obra_row + 1):
            row_vals = [om.obra, om.total, om.concluidas, om.em_andamento, om.atrasadas, f"{om.percentual}%"]
            for c_idx, val in enumerate(row_vals, start=1):
                c = ws_summary.cell(row=r_idx, column=c_idx, value=val)
                c.font = font_body
                c.border = border_thin
                c.alignment = align_left if c_idx == 1 else align_center
                if c_idx == 5 and om.atrasadas > 0:
                    c.fill = fill_overdue
                    c.font = Font(name="Segoe UI", size=10, bold=True, color="991B1B")
            ws_summary.row_dimensions[r_idx].height = 20

        for col in ws_summary.columns:
            col_letter = get_column_letter(col[0].column)
            ws_summary.column_dimensions[col_letter].width = 24

        output_path.parent.mkdir(parents=True, exist_ok=True)
        wb.save(output_path)
        LOGGER.info("Relatório Excel exportado com sucesso: %s", output_path)
        return output_path

    def export_quantitativo_to_excel(self, q: Any, output_path: Path) -> Path:
        """Gera planilha Excel (.xlsx) técnica com memorial de cálculo e cubagem de concreto e formas."""
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = f"Quantitativo {q.codigo}"
        ws.views.sheetView[0].showGridLines = True

        # Paleta Corporativa Verde Marcon
        PRIMARY = "064E3B"
        SECONDARY = "0F172A"
        ACCENT = "10B981"
        BG_LIGHT = "F8FAFC"
        BORDER_CLR = "CBD5E1"
        SUCCESS_BG = "DCFCE7"

        font_title = Font(name="Segoe UI", size=14, bold=True, color=PRIMARY)
        font_sub = Font(name="Segoe UI", size=9, italic=True, color="64748B")
        font_sec = Font(name="Segoe UI", size=10, bold=True, color=PRIMARY)
        font_header = Font(name="Segoe UI", size=10, bold=True, color="FFFFFF")
        font_body = Font(name="Segoe UI", size=9, color=SECONDARY)
        font_bold = Font(name="Segoe UI", size=9, bold=True, color=SECONDARY)

        fill_header = PatternFill(start_color=PRIMARY, end_color=PRIMARY, fill_type="solid")
        fill_zebra = PatternFill(start_color=BG_LIGHT, end_color=BG_LIGHT, fill_type="solid")
        fill_white = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
        fill_exec = PatternFill(start_color=SUCCESS_BG, end_color=SUCCESS_BG, fill_type="solid")

        border_thin = Border(
            left=Side(style='thin', color=BORDER_CLR),
            right=Side(style='thin', color=BORDER_CLR),
            top=Side(style='thin', color=BORDER_CLR),
            bottom=Side(style='thin', color=BORDER_CLR)
        )

        align_center = Alignment(horizontal="center", vertical="center")
        align_left = Alignment(horizontal="left", vertical="center")
        align_right = Alignment(horizontal="right", vertical="center")

        # Topo / Título
        ws["A1"] = "MARCON EMPREITEIRA • LEVANTAMENTO ESTRUTURAL & QUANTITATIVO"
        ws["A1"].font = font_title
        ws["A2"] = f"{q.disciplina.upper()} · {q.pavimento.upper()} | {q.obra.upper()} · {q.torre_setor.upper()} · Rev. {q.revisao}"
        ws["A2"].font = font_sub

        # Bloco de Metadados
        meta_data = [
            ("Código:", q.codigo, "Obra:", q.obra),
            ("Torre / Setor:", q.torre_setor, "Pavimento / Etapa:", q.pavimento),
            ("Disciplina:", q.disciplina, "Folha de Projeto:", q.folha_projeto),
            ("Revisão:", q.revisao, "Data do Levantamento:", q.data_levantamento_br),
            ("Responsável Técnico:", q.responsavel, "Status do Levantamento:", q.status.upper())
        ]

        curr_row = 4
        for row_items in meta_data:
            ws.cell(row=curr_row, column=1, value=row_items[0]).font = font_sec
            ws.cell(row=curr_row, column=2, value=row_items[1]).font = font_bold
            ws.cell(row=curr_row, column=5, value=row_items[2]).font = font_sec
            ws.cell(row=curr_row, column=6, value=row_items[3]).font = font_bold
            for col_i in range(1, 10):
                ws.cell(row=curr_row, column=col_i).border = border_thin
            curr_row += 1

        curr_row += 1
        # Resumo de Indicadores
        ws.cell(row=curr_row, column=1, value="CONCRETO TOTAL:").font = font_sec
        ws.cell(row=curr_row, column=2, value=f"{q.total_concreto_m3:.3f} m³".replace(".", ",")).font = font_bold
        ws.cell(row=curr_row, column=4, value="EXECUTADO:").font = font_sec
        ws.cell(row=curr_row, column=5, value=f"{q.concreto_executado_m3:.3f} m³ ({q.percentual_execucao}%)".replace(".", ",")).font = font_bold
        ws.cell(row=curr_row, column=7, value="FORMAS TOTAL:").font = font_sec
        ws.cell(row=curr_row, column=8, value=f"{q.total_formas_m2:.2f} m²".replace(".", ",")).font = font_bold

        curr_row += 2
        # Cabeçalho da Tabela de Lançamentos
        table_headers = [
            "Elemento", "Tipo", "Local / Região", "Peças",
            "Largura (m)", "Compr. (m)", "Altura (m)", "Qtd",
            "Concreto (m³)", "Formas (m²)", "Execução"
        ]

        for c_idx, h_text in enumerate(table_headers, start=1):
            cell = ws.cell(row=curr_row, column=c_idx, value=h_text)
            cell.font = font_header
            cell.fill = fill_header
            cell.alignment = align_center
            cell.border = border_thin
        ws.row_dimensions[curr_row].height = 24

        curr_row += 1
        lancamentos = q.lancamentos if hasattr(q, "lancamentos") and q.lancamentos else []
        for r_idx, item in enumerate(lancamentos, start=curr_row):
            row_fill = fill_exec if item.is_executado else (fill_zebra if r_idx % 2 == 0 else fill_white)
            vals = [
                item.elemento,
                item.tipo,
                item.local,
                item.pecas,
                item.largura,
                item.comprimento,
                item.altura,
                item.qtd,
                item.concreto_m3,
                item.formas_m2,
                item.execucao
            ]

            for c_idx, val in enumerate(vals, start=1):
                cell = ws.cell(row=r_idx, column=c_idx, value=val)
                cell.font = font_body
                cell.fill = row_fill
                cell.border = border_thin
                if c_idx in (1, 2, 3):
                    cell.alignment = align_left
                elif c_idx in (4, 11):
                    cell.alignment = align_center
                else:
                    cell.alignment = align_right
                    if isinstance(val, (int, float)):
                        cell.number_format = "#,##0.000" if c_idx in (5, 6, 7, 9) else "#,##0.00"

            ws.row_dimensions[r_idx].height = 20
            curr_row = r_idx

        # Ajuste de largura das colunas
        col_widths = {
            1: 15, 2: 12, 3: 26, 4: 8,
            5: 13, 6: 13, 7: 13, 8: 8,
            9: 16, 10: 14, 11: 16
        }
        for col_idx, width in col_widths.items():
            ws.column_dimensions[get_column_letter(col_idx)].width = width

        output_path.parent.mkdir(parents=True, exist_ok=True)
        wb.save(output_path)
        LOGGER.info("Quantitativo em Excel exportado com sucesso: %s", output_path)
        return output_path

