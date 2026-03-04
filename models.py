"""Modelos de dados da aplicação de gerenciamento de acólitos."""

from dataclasses import dataclass, field
from typing import List, Optional
import uuid


@dataclass
class Absence:
    id: str
    date: str
    description: str

    def to_dict(self) -> dict:
        return {"id": self.id, "date": self.date, "description": self.description}

    @classmethod
    def from_dict(cls, data: dict) -> "Absence":
        return cls(id=data["id"], date=data["date"], description=data.get("description", ""))


@dataclass
class Suspension:
    id: str
    reason: str
    start_date: str
    duration: str
    is_active: bool = True

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "reason": self.reason,
            "start_date": self.start_date,
            "duration": self.duration,
            "is_active": self.is_active,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Suspension":
        return cls(
            id=data["id"],
            reason=data["reason"],
            start_date=data["start_date"],
            duration=data["duration"],
            is_active=data.get("is_active", True),
        )


@dataclass
class BonusMovement:
    id: str
    type: str  # 'earn' ou 'use'
    amount: int
    description: str
    date: str

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type,
            "amount": self.amount,
            "description": self.description,
            "date": self.date,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BonusMovement":
        return cls(
            id=data["id"],
            type=data["type"],
            amount=data["amount"],
            description=data.get("description", ""),
            date=data["date"],
        )


@dataclass
class ScheduleHistoryEntry:
    schedule_id: str
    date: str
    day: str
    time: str
    description: str

    def to_dict(self) -> dict:
        return {
            "schedule_id": self.schedule_id,
            "date": self.date,
            "day": self.day,
            "time": self.time,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ScheduleHistoryEntry":
        return cls(
            schedule_id=data["schedule_id"],
            date=data["date"],
            day=data["day"],
            time=data["time"],
            description=data.get("description", ""),
        )


@dataclass
class EventHistoryEntry:
    event_id: str
    name: str
    date: str
    time: str

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "name": self.name,
            "date": self.date,
            "time": self.time,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "EventHistoryEntry":
        return cls(
            event_id=data["event_id"],
            name=data["name"],
            date=data["date"],
            time=data.get("time", ""),
        )


@dataclass
class Acolyte:
    id: str
    name: str
    times_scheduled: int = 0
    absences: List[Absence] = field(default_factory=list)
    suspensions: List[Suspension] = field(default_factory=list)
    is_suspended: bool = False
    bonus_count: int = 0
    bonus_movements: List[BonusMovement] = field(default_factory=list)
    schedule_history: List[ScheduleHistoryEntry] = field(default_factory=list)
    event_history: List[EventHistoryEntry] = field(default_factory=list)

    @property
    def absence_count(self) -> int:
        return len(self.absences)

    @property
    def suspension_count(self) -> int:
        return len(self.suspensions)

    @property
    def active_suspension(self) -> Optional[Suspension]:
        for s in self.suspensions:
            if s.is_active:
                return s
        return None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "times_scheduled": self.times_scheduled,
            "absences": [a.to_dict() for a in self.absences],
            "suspensions": [s.to_dict() for s in self.suspensions],
            "is_suspended": self.is_suspended,
            "bonus_count": self.bonus_count,
            "bonus_movements": [b.to_dict() for b in self.bonus_movements],
            "schedule_history": [sh.to_dict() for sh in self.schedule_history],
            "event_history": [eh.to_dict() for eh in self.event_history],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Acolyte":
        return cls(
            id=data["id"],
            name=data["name"],
            times_scheduled=data.get("times_scheduled", 0),
            absences=[Absence.from_dict(a) for a in data.get("absences", [])],
            suspensions=[Suspension.from_dict(s) for s in data.get("suspensions", [])],
            is_suspended=data.get("is_suspended", False),
            bonus_count=data.get("bonus_count", 0),
            bonus_movements=[BonusMovement.from_dict(b) for b in data.get("bonus_movements", [])],
            schedule_history=[ScheduleHistoryEntry.from_dict(sh) for sh in data.get("schedule_history", [])],
            event_history=[EventHistoryEntry.from_dict(eh) for eh in data.get("event_history", [])],
        )


@dataclass
class ScheduleSlot:
    id: str
    date: str
    day: str
    time: str
    description: str = ""
    acolyte_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "date": self.date,
            "day": self.day,
            "time": self.time,
            "description": self.description,
            "acolyte_ids": self.acolyte_ids,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ScheduleSlot":
        return cls(
            id=data["id"],
            date=data["date"],
            day=data["day"],
            time=data["time"],
            description=data.get("description", ""),
            acolyte_ids=data.get("acolyte_ids", []),
        )


@dataclass
class GeneralEvent:
    id: str
    name: str
    date: str
    time: str = ""
    excluded_acolyte_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "date": self.date,
            "time": self.time,
            "excluded_acolyte_ids": self.excluded_acolyte_ids,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GeneralEvent":
        return cls(
            id=data["id"],
            name=data["name"],
            date=data["date"],
            time=data.get("time", ""),
            excluded_acolyte_ids=data.get("excluded_acolyte_ids", []),
        )
