"""Gerador de relatórios PDF para acólitos usando reportlab."""

import os
from typing import Dict, List, Optional, Tuple

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Flowable,
    HRFlowable,
    PageBreak,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from .models import Acolyte, FinalizedEventBatchEntry, GeneratedSchedule


def _sanitize_anchor(name: str) -> str:
    """Cria um identificador seguro para âncoras a partir do nome."""
    return name.replace(" ", "_").replace("/", "_")


def _build_table(data: list, col_widths: list) -> Table:
    """Cria uma tabela estilizada."""
    table = Table(data, colWidths=col_widths)
    table.hAlign = "LEFT"
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4a4a8a")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 7),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f0f8")]),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#ccccdd")),
                ("FONTSIZE", (0, 1), (-1, -1), 6.5),
                ("TOPPADDING", (0, 0), (-1, -1), 1),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    return table


class _StatusPanel(Flowable):
    """Painel compacto de status em uma linha com bordas arredondadas."""

    _HEIGHT = 0.55 * cm
    _FONT_SIZE = 7.5
    _RADIUS = 5

    def __init__(self, text: str, width: float):
        super().__init__()
        self._text = text
        self.width = width

    def wrap(self, aW, aH):
        return self.width, self._HEIGHT

    def draw(self):
        c = self.canv
        h = self._HEIGHT
        c.saveState()
        c.setFillColor(colors.HexColor("#ebebf5"))
        c.setStrokeColor(colors.HexColor("#7070b0"))
        c.setLineWidth(0.8)
        c.roundRect(0, 0, self.width, h, radius=self._RADIUS, fill=1, stroke=1)
        c.setFillColor(colors.HexColor("#1a1a3a"))
        c.setFont("Helvetica", self._FONT_SIZE)
        y = (h - self._FONT_SIZE) / 2 + 1
        c.drawString(7, y, self._text)
        c.restoreState()


def _first_name(full_name: str) -> str:
    """Retorna o primeiro nome de um nome completo."""
    cleaned = (full_name or "").strip()
    if not cleaned:
        return "-"
    return cleaned.split()[0]


def _compact_names(names: List[str], max_chars: int = 55) -> str:
    """Compacta lista de nomes para evitar overflow visual na tabela."""
    if not names:
        return "-"
    full_text = ", ".join(names)
    if len(full_text) <= max_chars:
        return full_text

    shown = []
    current_len = 0
    for name in names:
        add_len = len(name) + (2 if shown else 0)
        if current_len + add_len > max_chars - 10:
            break
        shown.append(name)
        current_len += add_len

    remaining = len(names) - len(shown)
    if not shown:
        return f"{names[0]}... (+{len(names) - 1})"
    if remaining > 0:
        return f"{', '.join(shown)}... (+{remaining})"
    return ", ".join(shown)


def _generated_schedule_general_map(generated_schedule: GeneratedSchedule) -> Dict[Tuple[str, str, str, str], bool]:
    """Infer which generated slots were general events from stored schedule text.

    This preserves compatibility with older snapshots created before
    `is_general_event` was added to `GeneratedScheduleSlotSnapshot`.
    """
    result: Dict[Tuple[str, str, str, str], bool] = {}
    lines = [line.strip() for line in (generated_schedule.schedule_text or "").splitlines()]

    current_key = None
    current_description = ""
    for line in lines:
        if not line or line == "*ESCALA DA SEMANA*":
            continue

        if line.startswith("*") and line.endswith(":*"):
            header = line.strip("*")[:-1]
            day_part, remainder = header.split(", ", 1) if ", " in header else ("", header)
            date_part, time_part = remainder.split(" - ", 1) if " - " in remainder else (remainder, "")
            current_key = (date_part.strip(), day_part.strip(), time_part.strip(), "")
            current_description = ""
            continue

        if line.startswith("_") and line.endswith("_") and current_key is not None:
            current_description = line.strip("_")
            continue

        if current_key is not None:
            key = (
                current_key[0],
                current_key[1],
                current_key[2],
                current_description,
            )
            result[key] = line == "*TODOS*"
            current_key = None
            current_description = ""

    return result


def generate_report(
    acolytes: List[Acolyte],
    output_path: str,
    registered_events: Optional[List[FinalizedEventBatchEntry]] = None,
    generated_schedules: Optional[List[GeneratedSchedule]] = None,
    include_activity_table_per_acolyte: bool = True,
    cycle_name: str = "",
) -> str:
    """
    Gera um relatório PDF com os dados de todos os acólitos.
    A primeira página contém um resumo com links para cada acólito.
    Retorna o caminho do arquivo gerado.
    """
    if registered_events is None:
        registered_events = []
    if generated_schedules is None:
        generated_schedules = []
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
        fontSize=18,
        textColor=colors.HexColor("#2c2c6c"),
        spaceAfter=10,
    )
    style_acolyte_name = ParagraphStyle(
        "AcolyteName",
        parent=styles["Heading1"],
        fontSize=12,
        textColor=colors.HexColor("#2c2c6c"),
        spaceAfter=3,
        spaceBefore=10,
    )
    style_section = ParagraphStyle(
        "SectionHeader",
        parent=styles["Heading2"],
        fontSize=8,
        leading=8.5,
        textColor=colors.HexColor("#4a4a8a"),
        spaceAfter=1,
        spaceBefore=10,
    )
    style_body = ParagraphStyle(
        "BodyText",
        parent=styles["Normal"],
        fontSize=8,
        spaceAfter=1,
    )
    style_link = ParagraphStyle(
        "LinkStyle",
        parent=styles["Normal"],
        fontSize=8,
        textColor=colors.HexColor("#1a0dab"),
    )

    page_width = A4[0] - 4 * cm  # largura útil
    acolyte_content_width = page_width - (0.2 * cm)

    story = []

    # =====================================================================
    # PRIMEIRA PÁGINA: Resumo Geral
    # =====================================================================
    story.append(Paragraph("Relatório de Acólitos", style_title))
    if cycle_name.strip():
        story.append(Paragraph(f"Ciclo: <b>{cycle_name.strip()}</b>", style_body))
    story.append(Spacer(1, 0.15 * cm))
    story.append(Paragraph('<a name="resumo_geral"/>Resumo Geral', style_section))
    story.append(Spacer(1, 0.1 * cm))

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
                ("FONTSIZE", (0, 0), (-1, 0), 8),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("ALIGN", (1, 1), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f0f8")]),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#ccccdd")),
                ("FONTSIZE", (0, 1), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(summary_table)

    # =====================================================================
    # TABELA DE ESCALAS GERADAS: cards de todos os lotes gerados
    # =====================================================================
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph("Escalas Geradas", style_section))
    story.append(Spacer(1, 0.1 * cm))

    if generated_schedules:
        acolyte_name_map: Dict[str, str] = {a.id: a.name for a in acolytes}

        schedule_header = [[
            Paragraph("<b>Data</b>", style_body),
            Paragraph("<b>Dia</b>", style_body),
            Paragraph("<b>Horário</b>", style_body),
            Paragraph("<b>Descrição</b>", style_body),
            Paragraph("<b>Participantes</b>", style_body),
        ]]

        schedule_rows = []
        for generated_schedule in generated_schedules:
            legacy_general_map = _generated_schedule_general_map(generated_schedule)
            for slot in generated_schedule.slots:
                key = (
                    (slot.date or "").strip(),
                    (slot.day or "").strip(),
                    (slot.time or "").strip(),
                    (slot.description or "").strip(),
                )
                is_general_event = getattr(slot, "is_general_event", False) or legacy_general_map.get(key, False)

                if is_general_event:
                    participants_text = "TODOS"
                else:
                    first_names = [
                        _first_name(acolyte_name_map.get(aid, ""))
                        for aid in slot.acolyte_ids
                        if aid in acolyte_name_map
                    ]
                    participants_text = _compact_names(first_names)

                desc = slot.description or ("Escala Geral" if is_general_event else "-")
                schedule_rows.append([
                    Paragraph(slot.date or "-", style_body),
                    Paragraph(slot.day or "-", style_body),
                    Paragraph(slot.time or "-", style_body),
                    Paragraph(desc, style_body),
                    Paragraph(participants_text, style_body),
                ])

        schedule_table = Table(
            schedule_header + schedule_rows,
            colWidths=[
                page_width * 0.14,
                page_width * 0.20,
                page_width * 0.12,
                page_width * 0.20,
                page_width * 0.34,
            ],
        )
        schedule_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4a4a8a")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 8),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f0f8")]),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#ccccdd")),
                    ("FONTSIZE", (0, 1), (-1, -1), 7),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        story.append(schedule_table)
    else:
        story.append(Paragraph("Nenhuma escala gerada encontrada.", style_body))

    # =====================================================================
    # SEÇÃO DE ATIVIDADES: Tabela com todos os eventos registrados
    # =====================================================================
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph("Atividades Registradas", style_section))
    story.append(Spacer(1, 0.1 * cm))

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
                    ("FONTSIZE", (0, 0), (-1, 0), 8),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f0f8")]),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#ccccdd")),
                    ("FONTSIZE", (0, 1), (-1, -1), 7),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        story.append(events_table)
    else:
        story.append(Paragraph("Nenhuma atividade registrada.", style_body))

    # =====================================================================
    # PÁGINAS INDIVIDUAIS: Detalhes de cada acólito
    # =====================================================================
    story.append(PageBreak())

    for idx, acolyte in enumerate(acolytes):
        if idx > 0:
            story.append(Spacer(1, 0.2 * cm))
            story.append(HRFlowable(
                width="100%",
                thickness=1,
                color=colors.HexColor("#4a4a8a"),
                spaceAfter=0.15 * cm,
            ))

        anchor = _sanitize_anchor(acolyte.name)

        # Nome do acólito com âncora
        story.append(Paragraph(
            f'<a name="{anchor}"/><a href="#resumo_geral" color="#1a0dab"><u>{acolyte.name}</u></a>',
            style_acolyte_name,
        ))

        # --- Status (painel compacto) ---
        suspension_text = "Sim" if acolyte.is_suspended else "Não"
        status_text = (
            f"Escalas: {acolyte.times_scheduled}     "
            f"Faltas: {acolyte.absence_count}     "
            f"Suspenso: {suspension_text}     "
            f"Bônus: {acolyte.bonus_count}"
        )
        story.append(_StatusPanel(status_text, acolyte_content_width))

        # --- Histórico de Escalas ---
        story.append(Paragraph("Escalas", style_section))
        if acolyte.schedule_history:
            header = [["Data", "Dia", "Horário", "Descrição", "Faltou"]]
            rows = [
                [e.date, e.day, e.time, e.description or "-", "Sim" if e.missed else "Não"]
                for e in acolyte.schedule_history
            ]
            table = _build_table(
                header + rows,
                [2.2 * cm, 3.0 * cm, 2.2 * cm, acolyte_content_width - 9.4 * cm, 2.0 * cm],
            )
            story.append(table)
        else:
            story.append(Paragraph("Nenhuma escala registrada.", style_body))

        # --- Atividades ---
        if include_activity_table_per_acolyte:
            story.append(Paragraph("Atividades", style_section))
            if acolyte.event_history:
                header = [["Nome da Atividade", "Data", "Horário", "Faltou"]]
                rows = [[e.name, e.date, e.time or "-", "Sim" if e.missed else "Não"] for e in acolyte.event_history]
                table = _build_table(
                    header + rows,
                    [acolyte_content_width - 8 * cm, 2.5 * cm, 2.5 * cm, 3.0 * cm],
                )
                story.append(table)
            else:
                story.append(Paragraph("Nenhuma atividade registrada.", style_body))


        # --- Faltas ---
        story.append(Paragraph("Faltas", style_section))
        if acolyte.absences:
            header = [["Data", "Descrição", "Contada"]]
            rows = [
                [a.date, a.description or "-", "Não" if a.is_symbolic else "Sim"]
                for a in acolyte.absences
            ]
            table = _build_table(
                header + rows,
                [2.5 * cm, acolyte_content_width - 5 * cm, 2.5 * cm],
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
                [acolyte_content_width - 8 * cm, 2.5 * cm, 3 * cm, 2.5 * cm],
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
                [2.5 * cm, 2.5 * cm, acolyte_content_width - 8 * cm, 3 * cm],
            )
            story.append(table)
        else:
            story.append(Paragraph("Nenhuma movimentação de bônus registrada.", style_body))

    doc.build(story)
    return output_path
