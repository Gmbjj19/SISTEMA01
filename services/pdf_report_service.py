from pathlib import Path
from datetime import datetime
from typing import Optional, Any

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether, Image as RLImage
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm

from config import LOGGER, LOGO_PDF_PATH
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
        logo_item = RLImage(str(LOGO_PDF_PATH), width=3.0 * cm, height=2.2 * cm) if LOGO_PDF_PATH.exists() else Paragraph("<b>MARCON</b>", body_style)
        header_data = [
            [
                logo_item,
                Paragraph("<b>MARCON EMPREITEIRA</b><br/><font color='#64748B' size='8'>SISTEMA INTEGRADO DE ENGENHARIA & GESTÃO</font>", body_style),
                Paragraph(f"<b>BOLETIM DE MEDIÇÃO:</b> <font color='#1E3A8A' size='11'><b>{bm.boletim_code}</b></font><br/><b>Emissão:</b> {datetime.now().strftime('%d/%m/%Y às %H:%M')}", body_style)
            ]
        ]
        t_header = Table(header_data, colWidths=[3.2 * cm, 7.8 * cm, 7.0 * cm])
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

    def generate_quantitativo_pdf(self, q: Any, output_path: Path) -> Path:
        """Gera Laudo Oficial do Quantitativo Estrutural (Concreto e Formas) em PDF."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            leftMargin=1.5 * cm,
            rightMargin=1.5 * cm,
            topMargin=1.2 * cm,
            bottomMargin=1.2 * cm
        )

        PRIMARY = colors.HexColor("#064E3B")    # Verde Floresta Corporativo (igual ao print)
        SECONDARY = colors.HexColor("#0F172A")
        ACCENT = colors.HexColor("#10B981")
        BG_LIGHT = colors.HexColor("#F8FAFC")
        BORDER = colors.HexColor("#CBD5E1")
        TEXT_MUTED = colors.HexColor("#64748B")

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "QTitle", parent=styles["Normal"],
            fontName="Helvetica-Bold", fontSize=15, leading=18,
            textColor=PRIMARY, alignment=1
        )
        subtitle_style = ParagraphStyle(
            "QSub", parent=styles["Normal"],
            fontName="Helvetica", fontSize=9, leading=11,
            textColor=TEXT_MUTED, alignment=1
        )
        section_title = ParagraphStyle(
            "QSec", parent=styles["Normal"],
            fontName="Helvetica-Bold", fontSize=10, leading=13,
            textColor=PRIMARY
        )
        body_style = ParagraphStyle(
            "QBody", parent=styles["Normal"],
            fontName="Helvetica", fontSize=8.5, leading=10.5,
            textColor=SECONDARY
        )
        body_bold = ParagraphStyle(
            "QBold", parent=styles["Normal"],
            fontName="Helvetica-Bold", fontSize=8.5, leading=10.5,
            textColor=SECONDARY
        )

        story = []

        # Header
        logo_item = RLImage(str(LOGO_PDF_PATH), width=3.0 * cm, height=2.2 * cm) if LOGO_PDF_PATH.exists() else Paragraph("<b>MARCON</b>", body_style)
        h_data = [
            [
                logo_item,
                Paragraph("<b>MARCON EMPREITEIRA</b><br/><font color='#64748B' size='8'>SISTEMA DE CONTROLE DE CONCRETO & FORMAS</font>", body_style),
                Paragraph(f"<b>CÓDIGO:</b> <font color='#064E3B' size='11'><b>{q.codigo}</b></font><br/><b>Emissão:</b> {datetime.now().strftime('%d/%m/%Y às %H:%M')}", body_style)
            ]
        ]
        th = Table(h_data, colWidths=[3.2 * cm, 7.8 * cm, 7.0 * cm])
        th.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(th)
        story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceBefore=4, spaceAfter=8))

        # Título
        story.append(Paragraph(f"{q.disciplina.upper()} · {q.pavimento.upper()}", title_style))
        story.append(Paragraph(f"{q.obra.upper()} · {q.torre_setor.upper()} · Rev. {q.revisao} · {q.status.upper()}", subtitle_style))
        story.append(Spacer(1, 10))

        # Metadados
        ident_data = [
            [
                Paragraph(f"<b>Obra:</b> {q.obra}", body_style),
                Paragraph(f"<b>Torre / Setor:</b> {q.torre_setor}", body_style),
                Paragraph(f"<b>Pavimento:</b> {q.pavimento}", body_style)
            ],
            [
                Paragraph(f"<b>Folha do Projeto:</b> {q.folha_projeto}", body_style),
                Paragraph(f"<b>Revisão:</b> {q.revisao}", body_style),
                Paragraph(f"<b>Data:</b> {q.data_levantamento_br}", body_style)
            ],
            [
                Paragraph(f"<b>Responsável Técnico:</b> {q.responsavel}", body_style),
                Paragraph(f"<b>Status:</b> <font color='#064E3B'><b>{q.status.upper()}</b></font>", body_style),
                Paragraph(f"<b>Total Lançamentos:</b> {q.total_lancamentos}", body_style)
            ]
        ]
        ti = Table(ident_data, colWidths=[6.0 * cm, 6.0 * cm, 6.0 * cm])
        ti.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), BG_LIGHT),
            ('BOX', (0, 0), (-1, -1), 0.8, BORDER),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(ti)
        story.append(Spacer(1, 10))

        # Banner de Totais (Estilo Forest Green do Print)
        kpi_data = [
            [
                Paragraph("<font color='#A7F3D0' size='8'>CONCRETO TOTAL</font><br/><font color='#FFFFFF' size='13'><b>" + f"{q.concreto_total:.3f} m³".replace(".", ",") + "</b></font>", body_style),
                Paragraph("<font color='#A7F3D0' size='8'>CONCRETO EXECUTADO</font><br/><font color='#FFFFFF' size='13'><b>" + f"{q.concreto_executado:.3f} m³".replace(".", ",") + "</b></font>", body_style),
                Paragraph("<font color='#A7F3D0' size='8'>EXECUÇÃO FÍSICA</font><br/><font color='#FFFFFF' size='13'><b>" + f"{q.percentual_execucao:.1f}%".replace(".", ",") + "</b></font>", body_style),
                Paragraph("<font color='#A7F3D0' size='8'>ÁREA DE FORMAS</font><br/><font color='#FFFFFF' size='13'><b>" + f"{q.formas_total:.2f} m²".replace(".", ",") + "</b></font>", body_style)
            ]
        ]
        tkpi = Table(kpi_data, colWidths=[4.5 * cm, 4.5 * cm, 4.5 * cm, 4.5 * cm])
        tkpi.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), PRIMARY),
            ('BOX', (0, 0), (-1, -1), 1.0, colors.HexColor("#065F46")),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(tkpi)
        story.append(Spacer(1, 12))

        # Tabela de Lançamentos
        story.append(Paragraph("LANÇAMENTOS ESTRUTURAIS DE PEÇAS", section_title))
        story.append(Spacer(1, 3))

        l_headers = ["ELEMENTO", "LOCAL", "PÇS", "DIMENSÕES", "QTD", "CONCRETO (m³)", "FORMAS (m²)", "EXECUÇÃO"]
        l_rows = [l_headers]

        for item in q.lancamentos:
            l_rows.append([
                f"{item.elemento}\n({item.tipo})",
                item.local,
                str(item.pecas),
                item.dimensoes_display,
                f"{item.qtd:.2f}".replace(".", ","),
                f"{item.concreto_m3:.3f}".replace(".", ","),
                f"{item.formas_m2:.2f}".replace(".", ","),
                item.execucao
            ])

        tl = Table(l_rows, colWidths=[2.6 * cm, 4.4 * cm, 1.0 * cm, 3.4 * cm, 1.3 * cm, 2.2 * cm, 1.8 * cm, 1.3 * cm])
        tl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 7.5),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),
            ('ALIGN', (3, 1), (3, -1), 'LEFT'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
            ('GRID', (0, 0), (-1, -1), 0.5, BORDER),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        story.append(tl)

        # Assinaturas
        story.append(Spacer(1, 20))
        sign_data = [
            [
                Paragraph("___________________________________<br/><b>Responsável pelo Levantamento</b><br/><font size='7' color='#64748B'>" + q.responsavel + "</font>", body_style),
                Paragraph("___________________________________<br/><b>Fiscal de Obras / Estrutura</b><br/><font size='7' color='#64748B'>Aprovação Técnica</font>", body_style)
            ]
        ]
        ts = Table(sign_data, colWidths=[9.0 * cm, 9.0 * cm])
        ts.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(KeepTogether(ts))

        doc.build(story)
        LOGGER.info("Quantitativo em PDF gerado com sucesso: %s", output_path)
        return output_path

