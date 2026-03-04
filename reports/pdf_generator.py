from datetime import datetime
from typing import List

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)

from models.models import Acolyte


def generate_pdf(acolytes: List[Acolyte], filepath: str) -> None:
    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "AcolyteTitle",
        parent=styles["Heading1"],
        fontSize=16,
        spaceAfter=6,
        textColor=colors.darkblue,
    )
    section_style = ParagraphStyle(
        "SectionTitle",
        parent=styles["Heading2"],
        fontSize=12,
        spaceAfter=4,
        textColor=colors.darkslategray,
    )
    body_style = styles["Normal"]
    body_style.fontSize = 10

    story = []

    for idx, acolyte in enumerate(acolytes):
        if idx > 0:
            story.append(PageBreak())

        # Acolyte name heading
        suspended_label = " (SUSPENSO)" if acolyte.is_suspended else ""
        story.append(Paragraph(f"{acolyte.name}{suspended_label}", title_style))
        story.append(Spacer(1, 0.3 * cm))

        # Summary statistics
        story.append(Paragraph("Resumo", section_style))
        stats = [
            ["Vezes escalado:", str(acolyte.vezes_escalado)],
            ["Total de faltas:", str(len(acolyte.absences))],
            ["Suspenso:", "Sim" if acolyte.is_suspended else "Não"],
            ["Bônus disponível:", str(acolyte.bonus)],
        ]
        if acolyte.is_suspended and acolyte.suspension_duration:
            stats.append(["Tempo de suspensão:", acolyte.suspension_duration])

        stats_table = Table(stats, colWidths=[5 * cm, 10 * cm])
        stats_table.setStyle(TableStyle([
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("BACKGROUND", (0, 0), (-1, -1), colors.whitesmoke),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("PADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(stats_table)
        story.append(Spacer(1, 0.4 * cm))

        # History
        story.append(Paragraph("Histórico de Participações", section_style))
        if acolyte.history:
            hist_data = [["Data", "Hora", "Tipo", "Descrição"]]
            for h in acolyte.history:
                entry_type_label = "Escala" if h.entry_type == "escala" else "Evento"
                hist_data.append([h.date, h.time or "-", entry_type_label, h.description or "-"])
            hist_table = Table(hist_data, colWidths=[3 * cm, 2.5 * cm, 2.5 * cm, 9 * cm])
            hist_table.setStyle(TableStyle([
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightsteelblue),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.aliceblue]),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ("PADDING", (0, 0), (-1, -1), 4),
            ]))
            story.append(hist_table)
        else:
            story.append(Paragraph("Nenhuma participação registrada.", body_style))
        story.append(Spacer(1, 0.4 * cm))

        # Absences
        story.append(Paragraph("Faltas", section_style))
        if acolyte.absences:
            abs_data = [["Data", "Descrição"]]
            for a in acolyte.absences:
                abs_data.append([a.date, a.description or "-"])
            abs_table = Table(abs_data, colWidths=[4 * cm, 13 * cm])
            abs_table.setStyle(TableStyle([
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightyellow),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.lightyellow]),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ("PADDING", (0, 0), (-1, -1), 4),
            ]))
            story.append(abs_table)
        else:
            story.append(Paragraph("Nenhuma falta registrada.", body_style))
        story.append(Spacer(1, 0.4 * cm))

        # Suspensions
        story.append(Paragraph("Suspensões", section_style))
        if acolyte.suspensions:
            sus_data = [["Data", "Razão", "Duração", "Ativa"]]
            for s in acolyte.suspensions:
                sus_data.append([
                    s.date,
                    s.reason or "-",
                    s.duration or "-",
                    "Sim" if s.active else "Não",
                ])
            sus_table = Table(sus_data, colWidths=[3 * cm, 7 * cm, 4 * cm, 3 * cm])
            sus_table.setStyle(TableStyle([
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightcoral),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.mistyrose]),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ("PADDING", (0, 0), (-1, -1), 4),
            ]))
            story.append(sus_table)
        else:
            story.append(Paragraph("Nenhuma suspensão registrada.", body_style))
        story.append(Spacer(1, 0.4 * cm))

        # Bonus movements
        story.append(Paragraph(f"Bônus (Saldo atual: {acolyte.bonus})", section_style))
        if acolyte.bonus_movements:
            bon_data = [["Data", "Tipo", "Quantidade", "Descrição"]]
            for b in acolyte.bonus_movements:
                type_label = "Recebido" if b.type == "give" else "Utilizado"
                bon_data.append([b.date, type_label, str(b.amount), b.description or "-"])
            bon_table = Table(bon_data, colWidths=[3 * cm, 3.5 * cm, 3.5 * cm, 7 * cm])
            bon_table.setStyle(TableStyle([
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgreen),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.honeydew]),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ("PADDING", (0, 0), (-1, -1), 4),
            ]))
            story.append(bon_table)
        else:
            story.append(Paragraph("Nenhuma movimentação de bônus registrada.", body_style))

    if not story:
        story.append(Paragraph("Nenhum acólito cadastrado.", body_style))

    doc.build(story)
