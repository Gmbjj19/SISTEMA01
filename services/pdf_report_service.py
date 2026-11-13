from pathlib import Path
from datetime import datetime
from typing import Optional

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm

from config import LOGGER
from models.concrete import ConcreteMeasurement

class ConcretePDFService:
    """Gera Boletim de Medição e Controle de Concretagem em PDF de alta resolução com padrão ABNT/CREA."""

    def generate_pdf(self, bm: ConcreteMeasurement, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)

        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            leftMargin=1.5 * cm,
            rightMargin=1.5 * cm,
            topMargin=1.2 * cm,
            bottomMargin=1.2 * cm
        )

        # Paleta Corporativa de Cores
        PRIMARY = colors.HexColor("#1E3A8A")     # Azul Marinho Corporativo
        SECONDARY = colors.HexColor("#0F172A")   # Ardósia Escuro
        ACCENT = colors.HexColor("#2563EB")      # Azul Royal
        BG_LIGHT = colors.HexColor("#F8FAFC")    # Cinza Claro Suave
        BORDER = colors.HexColor("#CBD5E1")      # Bordas
        TEXT_MUTED = colors.HexColor("#64748B")

        # Estilos Tipográficos
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=15,
            leading=18,
            textColor=PRIMARY,
            alignment=1 # Centralizado
        )

        subtitle_style = ParagraphStyle(
            "DocSubtitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=11,
            textColor=TEXT_MUTED,
            alignment=1
        )

        section_title = ParagraphStyle(
            "SectionTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=13,
            textColor=PRIMARY
        )

        body_style = ParagraphStyle(
            "Body",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=11,
            textColor=SECONDARY
        )

        body_bold = ParagraphStyle(
            "BodyBold",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=11,
            textColor=SECONDARY
        )

        story = []

        # 1. CABEÇALHO CORPORATIVO
        header_data = [
            [
                Paragraph("<b>PRO ENGENHARIA & CONSTRUÇÕES LTDA.</b><br/><font color='#64748B' size='8'>SISTEMA INTEGRADO DE GESTÃO E CONTROLE TECNOLÓGICO</font>", body_style),
                Paragraph(f"<b>BOLETIM DE MEDIÇÃO:</b> <font color='#1E3A8A' size='11'><b>{bm.boletim_code}</b></font><br/><b>Emissão:</b> {datetime.now().strftime('%d/%m/%Y às %H:%M')}", body_style)
            ]
        ]
        t_header = Table(header_data, colWidths=[10 * cm, 8 * cm])
        t_header.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(t_header)

        story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceBefore=4, spaceAfter=8))

        # TÍTULO PRINCIPAL
        story.append(Paragraph("BOLETIM DE MEDIÇÃO & CONTROLE DE CONCRETAGEM", title_style))
        story.append(Paragraph("RELATÓRIO DE CUBAGEM, PARÂMETROS E RASTREABILIDADE TÉCNICA", subtitle_style))
        story.append(Spacer(1, 10))

        # 2. IDENTIFICAÇÃO DA OBRA E PEÇA
        story.append(Paragraph("1. IDENTIFICAÇÃO DA OBRA E ELEMENTO ESTRUTURAL", section_title))
        story.append(Spacer(1, 3))

        ident_data = [
            [
                Paragraph(f"<b>Canteiro / Obra:</b> {bm.obra}", body_style),
                Paragraph(f"<b>Data da Concretagem:</b> {bm.data_concretagem_br}", body_style)
            ],
            [
                Paragraph(f"<b>Elemento Concretado:</b> {bm.elemento}", body_style),
                Paragraph(f"<b>Responsável Técnico:</b> {bm.responsavel}", body_style)
            ]
        ]
        t_ident = Table(ident_data, colWidths=[10.5 * cm, 7.5 * cm])
        t_ident.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), BG_LIGHT),
            ('BOX', (0, 0), (-1, -1), 0.8, BORDER),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(t_ident)
        story.append(Spacer(1, 10))

        # 3. ESPECIFICAÇÕES TÉCNICAS DO CONCRETO
        story.append(Paragraph("2. ESPECIFICAÇÕES TÉCNICAS DO CONCRETO USINADO", section_title))
        story.append(Spacer(1, 3))

        specs_data = [
            [
                Paragraph(f"<b>Resistência (fck):</b> {bm.fck_mpa} MPa", body_style),
                Paragraph(f"<b>Slump Test:</b> {bm.slump_cm} ± 2 cm", body_style),
                Paragraph(f"<b>Brita:</b> {bm.brita_tipo}", body_style),
                Paragraph(f"<b>Corpos de Prova:</b> {bm.corpos_prova} CPs", body_style)
            ],
            [
                Paragraph(f"<b>Fornecedor:</b> {bm.fornecedor or 'Não informado'}", body_style),
                Paragraph(f"<b>Nota Fiscal:</b> {bm.nota_fiscal or 'Pendente'}", body_style),
                Paragraph(f"<b>Lacres:</b> {bm.lacres or 'Conforme'}", body_style),
                Paragraph(f"<b>Status:</b> <font color='#166534'><b>{bm.status}</b></font>", body_style)
            ]
        ]
        t_specs = Table(specs_data, colWidths=[4.5 * cm, 4.5 * cm, 4.5 * cm, 4.5 * cm])
        t_specs.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), BG_LIGHT),
            ('BOX', (0, 0), (-1, -1), 0.8, BORDER),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(t_specs)
        story.append(Spacer(1, 10))

        # 4. MEMÓRIA DE CÁLCULO E CUBAGEM GEOMÉTRICA
        story.append(Paragraph("3. LEVANTAMENTO GEOMÉTRICO DAS PEÇAS ESTRUTURAIS", section_title))
        story.append(Spacer(1, 3))

        calc_headers = ["Item", "Elemento", "Tipo", "Comp. (m)", "Larg. (m)", "Alt/Esp (m)", "Qtd", "Vol. Unit (m³)", "Subtotal (m³)"]
        calc_rows = [calc_headers]

        if not bm.itens:
            calc_rows.append(["1", bm.elemento or "Volume Global Informado", "-", "-", "-", "-", "1", f"{bm.volume_teorico:.2f}", f"{bm.volume_teorico:.2f}"])
        else:
            for idx, item in enumerate(bm.itens, start=1):
                calc_rows.append([
                    str(idx),
                    item.elemento,
                    item.tipo,
                    f"{item.comprimento:.2f}",
                    f"{item.largura:.2f}",
                    f"{item.altura:.2f}",
                    str(item.quantidade),
                    f"{item.volume_unitario:.3f}",
                    f"{item.volume_total:.3f}"
                ])

        t_calc = Table(calc_rows, colWidths=[1.0 * cm, 4.6 * cm, 2.2 * cm, 1.8 * cm, 1.8 * cm, 2.0 * cm, 1.2 * cm, 2.2 * cm, 2.2 * cm])
        t_calc.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
            ('GRID', (0, 0), (-1, -1), 0.5, BORDER),
        ]))
        story.append(t_calc)
        story.append(Spacer(1, 8))

        # 5. RESUMO DOS VOLUMES
        totals_data = [
            [
                Paragraph("<b>Volume Teórico Geométrico:</b>", body_style),
                Paragraph(f"<b>{bm.volume_teorico:.3f} m³</b>", body_bold),
                Paragraph("<b>Margem de Perda / Sobra Técnica:</b>", body_style),
                Paragraph(f"<b>{bm.perda_percentual:.1f}%</b>", body_bold),
                Paragraph("<b>VOLUME TOTAL APLICADO:</b>", ParagraphStyle("RedAlert", parent=body_bold, textColor=PRIMARY)),
                Paragraph(f"<b><font size='10'>{bm.volume_total:.2f} m³</font></b>", ParagraphStyle("RedAlertVal", parent=body_bold, textColor=PRIMARY))
            ]
        ]
        t_totals = Table(totals_data, colWidths=[4.2 * cm, 2.2 * cm, 4.2 * cm, 1.8 * cm, 3.8 * cm, 2.6 * cm])
        t_totals.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#EFF6FF")),
            ('BOX', (0, 0), (-1, -1), 1.0, ACCENT),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('ALIGN', (3, 0), (3, 0), 'RIGHT'),
            ('ALIGN', (5, 0), (5, 0), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(t_totals)
        story.append(Spacer(1, 10))

        # 6. OBSERVAÇÕES TÉCNICAS
        if bm.observacoes:
            story.append(Paragraph("4. OBSERVAÇÕES E NOTAS TÉCNICAS DE CAMPO", section_title))
            story.append(Spacer(1, 2))
            obs_data = [[Paragraph(bm.observacoes, body_style)]]
            t_obs = Table(obs_data, colWidths=[18 * cm])
            t_obs.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), BG_LIGHT),
                ('BOX', (0, 0), (-1, -1), 0.5, BORDER),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ]))
            story.append(t_obs)
            story.append(Spacer(1, 10))

        # 7. CAMPOS DE ASSINATURA FORMAL
        story.append(Spacer(1, 15))
        signatures_data = [
            [
                Paragraph("___________________________________<br/><b>Engenheiro Responsável</b><br/><font size='7' color='#64748B'>CREA / CAU</font>", body_style),
                Paragraph("___________________________________<br/><b>Fiscal de Obras / Qualidade</b><br/><font size='7' color='#64748B'>Assinatura e Carimbo</font>", body_style),
                Paragraph("___________________________________<br/><b>Fornecedor / Usina Concretera</b><br/><font size='7' color='#64748B'>Recebido e Conferido</font>", body_style)
            ]
        ]
        t_sign = Table(signatures_data, colWidths=[6.0 * cm, 6.0 * cm, 6.0 * cm])
        t_sign.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(KeepTogether(t_sign))

        # Compilar documento
        doc.build(story)
        LOGGER.info("Boletim de Medição em PDF gerado com sucesso: %s", output_path)
        return output_path
