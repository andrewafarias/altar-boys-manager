import json
import os
from dataclasses import asdict
from typing import List, Tuple

from models.models import (
    Acolyte, Absence, Suspension, HistoryEntry, BonusMovement,
    ScheduleSlot, GeneralEvent
)

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "acolitos_data.json")


def _acolyte_from_dict(d: dict) -> Acolyte:
    return Acolyte(
        id=d.get("id", ""),
        name=d.get("name", ""),
        vezes_escalado=d.get("vezes_escalado", 0),
        absences=[Absence(**a) for a in d.get("absences", [])],
        suspensions=[Suspension(**s) for s in d.get("suspensions", [])],
        is_suspended=d.get("is_suspended", False),
        suspension_duration=d.get("suspension_duration", ""),
        bonus=d.get("bonus", 0),
        bonus_movements=[BonusMovement(**b) for b in d.get("bonus_movements", [])],
        history=[HistoryEntry(**h) for h in d.get("history", [])],
    )


def _slot_from_dict(d: dict) -> ScheduleSlot:
    return ScheduleSlot(
        id=d.get("id", ""),
        date=d.get("date", ""),
        time=d.get("time", ""),
        description=d.get("description", ""),
        acolyte_ids=d.get("acolyte_ids", []),
    )


def _event_from_dict(d: dict) -> GeneralEvent:
    return GeneralEvent(
        id=d.get("id", ""),
        date=d.get("date", ""),
        time=d.get("time", ""),
        description=d.get("description", ""),
        excluded_acolyte_ids=d.get("excluded_acolyte_ids", []),
        registered=d.get("registered", False),
    )


def save_data(acolytes: List[Acolyte], slots: List[ScheduleSlot], events: List[GeneralEvent]) -> None:
    data = {
        "acolytes": [asdict(a) for a in acolytes],
        "slots": [asdict(s) for s in slots],
        "events": [asdict(e) for e in events],
    }
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_data() -> Tuple[List[Acolyte], List[ScheduleSlot], List[GeneralEvent]]:
    if not os.path.exists(DATA_FILE):
        return [], [], []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    acolytes = [_acolyte_from_dict(a) for a in data.get("acolytes", [])]
    slots = [_slot_from_dict(s) for s in data.get("slots", [])]
    events = [_event_from_dict(e) for e in data.get("events", [])]
    return acolytes, slots, events
