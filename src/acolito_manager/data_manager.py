"""Gerenciamento de persistência de dados em JSON."""

import json
import os
from typing import List, Tuple
from pathlib import Path

from .models import Acolyte, ScheduleSlot, GeneralEvent, GeneratedSchedule, FinalizedEventBatch, StandardSlot

# Data directory is relative to the root of the project (one level up from src)
DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
DATA_FILE = DATA_DIR / "acolitos_data.json"


def save_data(
    acolytes: List[Acolyte],
    schedule_slots: List[ScheduleSlot],
    general_events: List[GeneralEvent],
    generated_schedules: List[GeneratedSchedule] = None,
    finalized_event_batches: List[FinalizedEventBatch] = None,
    standard_slots: List[StandardSlot] = None,
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
    }
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_data():
    """Carrega os dados do arquivo JSON. Retorna listas vazias se o arquivo não existir."""
    if not DATA_FILE.exists():
        return [], [], [], [], [], []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        acolytes = [Acolyte.from_dict(a) for a in data.get("acolytes", [])]
        schedule_slots = [ScheduleSlot.from_dict(s) for s in data.get("schedule_slots", [])]
        general_events = [GeneralEvent.from_dict(e) for e in data.get("general_events", [])]
        generated_schedules = [GeneratedSchedule.from_dict(gs) for gs in data.get("generated_schedules", [])]
        finalized_event_batches = [FinalizedEventBatch.from_dict(fb) for fb in data.get("finalized_event_batches", [])]
        standard_slots = [StandardSlot.from_dict(ss) for ss in data.get("standard_slots", [])]
        return acolytes, schedule_slots, general_events, generated_schedules, finalized_event_batches, standard_slots
    except (json.JSONDecodeError, KeyError, TypeError):
        return [], [], [], [], [], []


def export_to_file(
    acolytes: List[Acolyte],
    schedule_slots: List[ScheduleSlot],
    general_events: List[GeneralEvent],
    path: str,
    generated_schedules: List[GeneratedSchedule] = None,
    finalized_event_batches: List[FinalizedEventBatch] = None,
    standard_slots: List[StandardSlot] = None,
) -> None:
    """Exporta todos os dados para um arquivo JSON externo."""
    data = {
        "acolytes": [a.to_dict() for a in acolytes],
        "schedule_slots": [s.to_dict() for s in schedule_slots],
        "general_events": [e.to_dict() for e in general_events],
        "generated_schedules": [gs.to_dict() for gs in (generated_schedules or [])],
        "finalized_event_batches": [fb.to_dict() for fb in (finalized_event_batches or [])],
        "standard_slots": [ss.to_dict() for ss in (standard_slots or [])],
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
    return acolytes, schedule_slots, general_events, generated_schedules, finalized_event_batches, standard_slots
