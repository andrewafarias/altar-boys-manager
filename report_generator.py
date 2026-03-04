"""Gerador de relatórios PDF para acólitos usando reportlab."""

import os
from typing import List

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)

from models import Acolyte


def _build_table(data: list, col_widths: list) -> Table:
    """Cria uma tabela estilizada."""
    table = Table(data, colWidths=col_widths)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4a4a8a")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 9),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f0f8")]),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#ccccdd")),
                ("FONTSIZE", (0, 1), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


def generate_report(acolytes: List[Acolyte], output_path: str) -> str:
    """
    Gera um relatório PDF com os dados de todos os acólitos.
    Retorna o caminho do arquivo gerado.
    """
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()

    style_title = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        fontSize=22,
        textColor=colors.HexColor("#2c2c6c"),
        spaceAfter=20,
    )
    style_acolyte_name = ParagraphStyle(
        "AcolyteName",
        parent=styles["Heading1"],
        fontSize=16,
        textColor=colors.HexColor("#2c2c6c"),
        spaceAfter=10,
        spaceBefore=6,
    )
    style_section = ParagraphStyle(
        "SectionHeader",
        parent=styles["Heading2"],
        fontSize=11,
        textColor=colors.HexColor("#4a4a8a"),
        spaceAfter=6,
        spaceBefore=10,
    )
    style_body = ParagraphStyle(
        "BodyText",
        parent=styles["Normal"],
        fontSize=9,
        spaceAfter=4,
    )

    page_width = A4[0] - 4 * cm  # largura útil

    story = []

    # Título do relatório
    story.append(Paragraph("Relatório de Acólitos", style_title))
    story.append(Spacer(1, 0.3 * cm))

    for idx, acolyte in enumerate(acolytes):
        if idx > 0:
            story.append(PageBreak())

        # Nome do acólito
        story.append(Paragraph(acolyte.name, style_acolyte_name))

        # --- Status ---
        story.append(Paragraph("Status", style_section))
        suspension_text = "Sim" if acolyte.is_suspended else "Não"
        active = acolyte.active_suspension
        if active:
            suspension_text += f" ({active.reason}, início: {active.start_date}, duração: {active.duration})"
        status_lines = [
            f"<b>Vezes escalado:</b> {acolyte.times_scheduled}",
            f"<b>Faltas:</b> {acolyte.absence_count}",
            f"<b>Suspenso:</b> {suspension_text}",
            f"<b>Bônus:</b> {acolyte.bonus_count}",
        ]
        for line in status_lines:
            story.append(Paragraph(line, style_body))

        # --- Histórico de Escalas ---
        story.append(Paragraph("Histórico de Escalas", style_section))
        if acolyte.schedule_history:
            header = [["Data", "Dia", "Horário", "Descrição"]]
            rows = [
                [e.date, e.day, e.time, e.description or "-"]
                for e in acolyte.schedule_history
            ]
            table = _build_table(
                header + rows,
                [2.5 * cm, 3.5 * cm, 2.5 * cm, page_width - 8.5 * cm],
            )
            story.append(table)
        else:
            story.append(Paragraph("Nenhuma escala registrada.", style_body))

        # --- Eventos ---
        story.append(Paragraph("Eventos", style_section))
        if acolyte.event_history:
            header = [["Nome do Evento", "Data", "Horário"]]
            rows = [[e.name, e.date, e.time or "-"] for e in acolyte.event_history]
            table = _build_table(
                header + rows,
                [page_width - 6 * cm, 3 * cm, 3 * cm],
            )
            story.append(table)
        else:
            story.append(Paragraph("Nenhum evento registrado.", style_body))

        # --- Faltas ---
        story.append(Paragraph("Faltas", style_section))
        if acolyte.absences:
            header = [["Data", "Descrição"]]
            rows = [[a.date, a.description or "-"] for a in acolyte.absences]
            table = _build_table(
                header + rows,
                [3 * cm, page_width - 3 * cm],
            )
            story.append(table)
        else:
            story.append(Paragraph("Nenhuma falta registrada.", style_body))

        # --- Suspensões ---
        story.append(Paragraph("Suspensões", style_section))
        if acolyte.suspensions:
            header = [["Motivo", "Início", "Duração", "Ativa"]]
            rows = [
                [
                    s.reason,
                    s.start_date,
                    s.duration,
                    "Sim" if s.is_active else "Não",
                ]
                for s in acolyte.suspensions
            ]
            table = _build_table(
                header + rows,
                [page_width - 8 * cm, 2.5 * cm, 3 * cm, 2.5 * cm],
            )
            story.append(table)
        else:
            story.append(Paragraph("Nenhuma suspensão registrada.", style_body))

        # --- Movimentação de Bônus ---
        story.append(Paragraph("Movimentação de Bônus", style_section))
        if acolyte.bonus_movements:
            header = [["Tipo", "Quantidade", "Descrição", "Data"]]
            rows = [
                [
                    "Ganho" if b.type == "earn" else "Usado",
                    str(b.amount),
                    b.description or "-",
                    b.date,
                ]
                for b in acolyte.bonus_movements
            ]
            table = _build_table(
                header + rows,
                [2.5 * cm, 2.5 * cm, page_width - 8 * cm, 3 * cm],
            )
            story.append(table)
        else:
            story.append(Paragraph("Nenhuma movimentação de bônus registrada.", style_body))

    doc.build(story)
    return output_path
