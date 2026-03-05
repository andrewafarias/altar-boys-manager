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

from .models import Acolyte, FinalizedEventBatchEntry


def _sanitize_anchor(name: str) -> str:
    """Cria um identificador seguro para âncoras a partir do nome."""
    return name.replace(" ", "_").replace("/", "_")


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


def generate_report(
    acolytes: List[Acolyte],
    output_path: str,
    registered_events: List[FinalizedEventBatchEntry] = None,
) -> str:
    """
    Gera um relatório PDF com os dados de todos os acólitos.
    A primeira página contém um resumo com links para cada acólito.
    Retorna o caminho do arquivo gerado.
    """
    if registered_events is None:
        registered_events = []
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
    style_link = ParagraphStyle(
        "LinkStyle",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#1a0dab"),
    )

    page_width = A4[0] - 4 * cm  # largura útil

    story = []

    # =====================================================================
    # PRIMEIRA PÁGINA: Resumo Geral
    # =====================================================================
    story.append(Paragraph("Relatório de Acólitos", style_title))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph("Resumo Geral", style_section))
    story.append(Spacer(1, 0.2 * cm))

    # Tabela de resumo com hyperlinks nos nomes
    summary_header = [
        [
            Paragraph("<b>Nome</b>", style_body),
            Paragraph("<b>Escalas</b>", style_body),
            Paragraph("<b>Faltas</b>", style_body),
            Paragraph("<b>Suspensões</b>", style_body),
            Paragraph("<b>Suspenso</b>", style_body),
            Paragraph("<b>Bônus</b>", style_body),
        ]
    ]

    summary_rows = []
    for acolyte in acolytes:
        anchor = _sanitize_anchor(acolyte.name)
        name_link = Paragraph(
            f'<a href="#{anchor}" color="#1a0dab"><u>{acolyte.name}</u></a>',
            style_link,
        )
        suspended_text = "Sim" if acolyte.is_suspended else "Não"
        summary_rows.append([
            name_link,
            Paragraph(str(acolyte.times_scheduled), style_body),
            Paragraph(str(acolyte.absence_count), style_body),
            Paragraph(str(acolyte.suspension_count), style_body),
            Paragraph(suspended_text, style_body),
            Paragraph(str(acolyte.bonus_count), style_body),
        ])

    summary_table = Table(
        summary_header + summary_rows,
        colWidths=[
            page_width * 0.30,  # Nome
            page_width * 0.14,  # Escalas
            page_width * 0.14,  # Faltas
            page_width * 0.14,  # Suspensões
            page_width * 0.14,  # Suspenso
            page_width * 0.14,  # Bônus
        ],
    )
    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4a4a8a")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 9),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("ALIGN", (1, 1), (-1, -1), "CENTER"),
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
    story.append(summary_table)

    # =====================================================================
    # SEÇÃO DE ATIVIDADES: Tabela com todos os eventos registrados
    # =====================================================================
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph("Atividades Registradas", style_section))
    story.append(Spacer(1, 0.2 * cm))

    if registered_events:
        events_header = [
            [
                Paragraph("<b>Nome da Atividade</b>", style_body),
                Paragraph("<b>Data</b>", style_body),
                Paragraph("<b>Horário</b>", style_body),
            ]
        ]

        events_rows = []
        for event in registered_events:
            events_rows.append([
                Paragraph(event.name, style_body),
                Paragraph(event.date, style_body),
                Paragraph(event.time or "-", style_body),
            ])

        events_table = Table(
            events_header + events_rows,
            colWidths=[
                page_width * 0.50,  # Nome da Atividade
                page_width * 0.25,  # Data
                page_width * 0.25,  # Horário
            ],
        )
        events_table.setStyle(
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
        story.append(events_table)
    else:
        story.append(Paragraph("Nenhuma atividade registrada.", style_body))

    # =====================================================================
    # PÁGINAS INDIVIDUAIS: Detalhes de cada acólito
    # =====================================================================
    for acolyte in acolytes:
        story.append(PageBreak())

        anchor = _sanitize_anchor(acolyte.name)

        # Nome do acólito com âncora
        story.append(Paragraph(
            f'<a name="{anchor}"/>{acolyte.name}',
            style_acolyte_name,
        ))

        # --- Status ---
        story.append(Paragraph("Status", style_section))
        suspension_text = "Sim" if acolyte.is_suspended else "Não"
        active = acolyte.active_suspension
        if active:
            suspension_text += f" ({active.reason}, início: {active.start_date}, fim: {active.end_date})"
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

        # --- Atividades ---
        story.append(Paragraph("Atividades", style_section))
        if acolyte.event_history:
            header = [["Nome da Atividade", "Data", "Horário"]]
            rows = [[e.name, e.date, e.time or "-"] for e in acolyte.event_history]
            table = _build_table(
                header + rows,
                [page_width - 6 * cm, 3 * cm, 3 * cm],
            )
            story.append(table)
        else:
            story.append(Paragraph("Nenhuma atividade registrada.", style_body))

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
            header = [["Motivo", "Início", "Fim", "Ativa"]]
            rows = [
                [
                    s.reason,
                    s.start_date,
                    s.end_date,
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
