"""Gerenciamento de persistência de dados em JSON."""

import json
import os
from typing import List, Tuple
from pathlib import Path

from .models import (
    Acolyte,
    ScheduleSlot,
    GeneralEvent,
    GeneratedSchedule,
    FinalizedEventBatch,
    StandardSlot,
    CicloHistoryEntry,
)

# Data directory is relative to the root of the project (one level up from src)
DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
DATA_FILE = DATA_DIR / "acolitos_data.json"

DEFAULT_COMMON_TIMES = [
    "06:00", "07:00", "08:00", "09:00", "10:00",
    "11:00", "12:00", "14:00", "15:00", "16:00",
    "17:00", "18:00", "19:00", "19:30", "20:00",
]


def save_data(
    acolytes: List[Acolyte],
    schedule_slots: List[ScheduleSlot],
    general_events: List[GeneralEvent],
    generated_schedules: List[GeneratedSchedule] = None,
    finalized_event_batches: List[FinalizedEventBatch] = None,
    standard_slots: List[StandardSlot] = None,
    ciclo_history: List[CicloHistoryEntry] = None,
    custom_common_times: List[str] = None,
) -> None:
    """Salva todos os dados no arquivo JSON."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    data = {
        "acolytes": [a.to_dict() for a in acolytes],
        "schedule_slots": [s.to_dict() for s in schedule_slots],
        "general_events": [e.to_dict() for e in general_events],
        "generated_schedules": [gs.to_dict() for gs in (generated_schedules or [])],
        "finalized_event_batches": [fb.to_dict() for fb in (finalized_event_batches or [])],
        "standard_slots": [ss.to_dict() for ss in (standard_slots or [])],
        "ciclo_history": [ch.to_dict() for ch in (ciclo_history or [])],
        "custom_common_times": custom_common_times if custom_common_times is not None else DEFAULT_COMMON_TIMES,
    }
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_data():
    """Carrega os dados do arquivo JSON. Retorna listas vazias se o arquivo não existir."""
    if not DATA_FILE.exists():
        return [], [], [], [], [], [], [], list(DEFAULT_COMMON_TIMES)
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        acolytes = [Acolyte.from_dict(a) for a in data.get("acolytes", [])]
        schedule_slots = [ScheduleSlot.from_dict(s) for s in data.get("schedule_slots", [])]
        general_events = [GeneralEvent.from_dict(e) for e in data.get("general_events", [])]
        generated_schedules = [GeneratedSchedule.from_dict(gs) for gs in data.get("generated_schedules", [])]
        finalized_event_batches = [FinalizedEventBatch.from_dict(fb) for fb in data.get("finalized_event_batches", [])]
        standard_slots = [StandardSlot.from_dict(ss) for ss in data.get("standard_slots", [])]
        ciclo_history = [CicloHistoryEntry.from_dict(ch) for ch in data.get("ciclo_history", [])]
        custom_common_times = data.get("custom_common_times", list(DEFAULT_COMMON_TIMES))
        return acolytes, schedule_slots, general_events, generated_schedules, finalized_event_batches, standard_slots, ciclo_history, custom_common_times
    except (json.JSONDecodeError, KeyError, TypeError):
        return [], [], [], [], [], [], [], list(DEFAULT_COMMON_TIMES)


def export_to_file(
    acolytes: List[Acolyte],
    schedule_slots: List[ScheduleSlot],
    general_events: List[GeneralEvent],
    path: str,
    generated_schedules: List[GeneratedSchedule] = None,
    finalized_event_batches: List[FinalizedEventBatch] = None,
    standard_slots: List[StandardSlot] = None,
    ciclo_history: List[CicloHistoryEntry] = None,
    custom_common_times: List[str] = None,
) -> None:
    """Exporta todos os dados para um arquivo JSON externo."""
    data = {
        "acolytes": [a.to_dict() for a in acolytes],
        "schedule_slots": [s.to_dict() for s in schedule_slots],
        "general_events": [e.to_dict() for e in general_events],
        "generated_schedules": [gs.to_dict() for gs in (generated_schedules or [])],
        "finalized_event_batches": [fb.to_dict() for fb in (finalized_event_batches or [])],
        "standard_slots": [ss.to_dict() for ss in (standard_slots or [])],
        "ciclo_history": [ch.to_dict() for ch in (ciclo_history or [])],
        "custom_common_times": custom_common_times if custom_common_times is not None else DEFAULT_COMMON_TIMES,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def import_from_file(path: str):
    """Importa todos os dados de um arquivo JSON externo."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    acolytes = [Acolyte.from_dict(a) for a in data.get("acolytes", [])]
    schedule_slots = [ScheduleSlot.from_dict(s) for s in data.get("schedule_slots", [])]
    general_events = [GeneralEvent.from_dict(e) for e in data.get("general_events", [])]
    generated_schedules = [GeneratedSchedule.from_dict(gs) for gs in data.get("generated_schedules", [])]
    finalized_event_batches = [FinalizedEventBatch.from_dict(fb) for fb in data.get("finalized_event_batches", [])]
    standard_slots = [StandardSlot.from_dict(ss) for ss in data.get("standard_slots", [])]
    ciclo_history = [CicloHistoryEntry.from_dict(ch) for ch in data.get("ciclo_history", [])]
    custom_common_times = data.get("custom_common_times", list(DEFAULT_COMMON_TIMES))
    return acolytes, schedule_slots, general_events, generated_schedules, finalized_event_batches, standard_slots, ciclo_history, custom_common_times
