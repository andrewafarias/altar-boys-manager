"""Funções utilitárias compartilhadas pelo projeto."""

import calendar
from datetime import datetime, timedelta
from typing import List

WEEKDAYS_PT = [
    "Segunda-feira",
    "Terça-feira",
    "Quarta-feira",
    "Quinta-feira",
    "Sexta-feira",
    "Sábado",
    "Domingo",
]


def detect_weekday(date_str: str) -> str:
    """Detecta o dia da semana a partir de uma data no formato DD/MM ou DD/MM/YYYY."""
    try:
        parts = date_str.strip().split("/")
        if len(parts) >= 2:
            day, month = int(parts[0]), int(parts[1])
            year = int(parts[2]) if len(parts) == 3 else datetime.now().year
            dt = datetime(year, month, day)
            return WEEKDAYS_PT[dt.weekday()]
    except (ValueError, IndexError):
        pass
    return ""


def today_str() -> str:
    """Retorna a data de hoje no formato DD/MM/YYYY."""
    return datetime.now().strftime("%d/%m/%Y")


def next_occurrence_of_day(day_name: str) -> str:
    """Retorna a data (DD/MM) da próxima ocorrência do dia da semana indicado."""
    try:
        target_idx = WEEKDAYS_PT.index(day_name)
    except ValueError:
        return ""
    today = datetime.now()
    current_idx = today.weekday()
    days_ahead = target_idx - current_idx
    if days_ahead < 0:
        days_ahead += 7
    target_date = today + timedelta(days=days_ahead)
    return target_date.strftime("%d/%m")


def names_list_to_text(names: List[str]) -> str:
    """Formata uma lista de nomes separando o último com 'e'."""
    if not names:
        return ""
    if len(names) == 1:
        return names[0]
    return ", ".join(names[:-1]) + " e " + names[-1]


def is_currently_suspended(acolyte) -> bool:
    """Verifica se o acólito está suspenso no momento atual."""
    today = datetime.now().date()
    for s in acolyte.suspensions:
        if not s.is_active:
            continue
        try:
            start_dt = datetime.strptime(s.start_date, "%d/%m/%Y").date()
            if start_dt > today:
                continue
            if s.end_date:
                end_dt = datetime.strptime(s.end_date, "%d/%m/%Y").date()
                if end_dt < today:
                    continue
            return True
        except ValueError:
            continue
    return False


def normalize_date(date_str: str) -> str:
    """Normaliza uma data para o formato DD/MM/YYYY, assumindo o ano atual se não especificado."""
    if not date_str:
        return date_str
    try:
        parts = date_str.strip().split("/")
        if len(parts) == 2:
            day, month = parts[0], parts[1]
            year = datetime.now().year
            return f"{day}/{month}/{year}"
        elif len(parts) == 3:
            return date_str
        else:
            return date_str
    except (ValueError, IndexError):
        return date_str
