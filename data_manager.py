"""Gerenciamento de persistência de dados em JSON."""

import json
import os
from typing import List, Tuple

from models import Acolyte, ScheduleSlot, GeneralEvent

DATA_DIR = "data"
DATA_FILE = os.path.join(DATA_DIR, "acolitos_data.json")


def save_data(acolytes: List[Acolyte], schedule_slots: List[ScheduleSlot], general_events: List[GeneralEvent]) -> None:
    """Salva todos os dados no arquivo JSON."""
    os.makedirs(DATA_DIR, exist_ok=True)
    data = {
        "acolytes": [a.to_dict() for a in acolytes],
        "schedule_slots": [s.to_dict() for s in schedule_slots],
        "general_events": [e.to_dict() for e in general_events],
    }
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_data() -> Tuple[List[Acolyte], List[ScheduleSlot], List[GeneralEvent]]:
    """Carrega os dados do arquivo JSON. Retorna listas vazias se o arquivo não existir."""
    if not os.path.exists(DATA_FILE):
        return [], [], []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        acolytes = [Acolyte.from_dict(a) for a in data.get("acolytes", [])]
        schedule_slots = [ScheduleSlot.from_dict(s) for s in data.get("schedule_slots", [])]
        general_events = [GeneralEvent.from_dict(e) for e in data.get("general_events", [])]
        return acolytes, schedule_slots, general_events
    except (json.JSONDecodeError, KeyError, TypeError):
        return [], [], []
