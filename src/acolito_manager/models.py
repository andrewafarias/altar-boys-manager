"""Modelos de dados da aplicação de gerenciamento de acólitos."""

from dataclasses import dataclass, field
from typing import List, Optional
import uuid


@dataclass
class Unavailability:
    """Indisponibilidade de um acólito para um determinado dia/horário da semana."""

    day: str  # e.g., "Segunda-feira"
    start_time: str  # HH:MM
    end_time: str  # HH:MM
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "day": self.day,
            "start_time": self.start_time,
            "end_time": self.end_time,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Unavailability":
        return cls(
            id=data["id"],
            day=data["day"],
            start_time=data["start_time"],
            end_time=data["end_time"],
        )



@dataclass
class Absence:
    date: str
    description: str
    linked_entry_type: str = ""
    linked_entry_id: str = ""
    is_symbolic: bool = False
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "date": self.date,
            "description": self.description,
            "linked_entry_type": self.linked_entry_type,
            "linked_entry_id": self.linked_entry_id,
            "is_symbolic": self.is_symbolic,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Absence":
        return cls(
            id=data["id"],
            date=data["date"],
            description=data.get("description", ""),
            linked_entry_type=data.get("linked_entry_type", ""),
            linked_entry_id=data.get("linked_entry_id", ""),
            is_symbolic=data.get("is_symbolic", False),
        )

@dataclass
class Suspension:
    reason: str
    start_date: str
    duration: str = ""
    is_active: bool = True
    end_date: str = ""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "reason": self.reason,
            "start_date": self.start_date,
            "duration": self.duration,
            "is_active": self.is_active,
            "end_date": self.end_date,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Suspension":
        return cls(
            id=data["id"],
            reason=data["reason"],
            start_date=data["start_date"],
            duration=data.get("duration", ""),
            is_active=data.get("is_active", True),
            end_date=data.get("end_date", ""),
        )


@dataclass
class BonusMovement:
    type: str  # 'earn' ou 'use'
    amount: int
    description: str
    date: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

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
    missed: bool = False

    def to_dict(self) -> dict:
        return {
            "schedule_id": self.schedule_id,
            "date": self.date,
            "day": self.day,
            "time": self.time,
            "description": self.description,
            "missed": self.missed,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ScheduleHistoryEntry":
        return cls(
            schedule_id=data["schedule_id"],
            date=data["date"],
            day=data["day"],
            time=data["time"],
            description=data.get("description", ""),
            missed=data.get("missed", False),
        )


@dataclass
class EventHistoryEntry:
    event_id: str
    name: str
    date: str
    time: str
    missed: bool = False

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "name": self.name,
            "date": self.date,
            "time": self.time,
            "missed": self.missed,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "EventHistoryEntry":
        return cls(
            event_id=data["event_id"],
            name=data["name"],
            date=data["date"],
            time=data.get("time", ""),
            missed=data.get("missed", False),
        )


@dataclass
class Acolyte:
    name: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    times_scheduled: int = 0
    absences: List[Absence] = field(default_factory=list)
    suspensions: List[Suspension] = field(default_factory=list)
    is_suspended: bool = False
    bonus_count: int = 0
    bonus_movements: List[BonusMovement] = field(default_factory=list)
    schedule_history: List[ScheduleHistoryEntry] = field(default_factory=list)
    event_history: List[EventHistoryEntry] = field(default_factory=list)
    unavailabilities: List[Unavailability] = field(default_factory=list)


    @property
    def absence_count(self) -> int:
        return len([a for a in self.absences if not a.is_symbolic])
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
            "unavailabilities": [u.to_dict() for u in self.unavailabilities],
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
            unavailabilities=[Unavailability.from_dict(u) for u in data.get("unavailabilities", [])],
        )


@dataclass
class ScheduleSlot:
    date: str
    day: str
    time: str
    description: str = ""
    acolyte_ids: List[str] = field(default_factory=list)
    is_general_event: bool = False
    general_event_name: str = ""
    include_as_activity: bool = True
    include_as_schedule: bool = True
    excluded_acolyte_ids: List[str] = field(default_factory=list)
    suspended_excluded_acolyte_ids: List[str] = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "date": self.date,
            "day": self.day,
            "time": self.time,
            "description": self.description,
            "acolyte_ids": self.acolyte_ids,
            "is_general_event": self.is_general_event,
            "general_event_name": self.general_event_name,
            "include_as_activity": self.include_as_activity,
            "include_as_schedule": self.include_as_schedule,
            "excluded_acolyte_ids": self.excluded_acolyte_ids,
            "suspended_excluded_acolyte_ids": self.suspended_excluded_acolyte_ids,
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
            is_general_event=data.get("is_general_event", False),
            general_event_name=data.get("general_event_name", ""),
            include_as_activity=data.get("include_as_activity", True),
            include_as_schedule=data.get("include_as_schedule", True),
            excluded_acolyte_ids=data.get("excluded_acolyte_ids", []),
            suspended_excluded_acolyte_ids=data.get("suspended_excluded_acolyte_ids", []),
        )


@dataclass
class GeneralEvent:
    name: str
    date: str
    time: str = ""
    excluded_acolyte_ids: List[str] = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

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


@dataclass
class GeneratedScheduleSlotSnapshot:
    slot_id: str
    date: str
    day: str
    time: str
    description: str
    acolyte_ids: List[str]
    is_general_event: bool = False

    def to_dict(self) -> dict:
        return {
            "slot_id": self.slot_id,
            "date": self.date,
            "day": self.day,
            "time": self.time,
            "description": self.description,
            "acolyte_ids": self.acolyte_ids,
            "is_general_event": self.is_general_event,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GeneratedScheduleSlotSnapshot":
        return cls(
            slot_id=data["slot_id"],
            date=data["date"],
            day=data["day"],
            time=data["time"],
            description=data.get("description", ""),
            acolyte_ids=data.get("acolyte_ids", []),
            is_general_event=data.get("is_general_event", False),
        )


@dataclass
class GeneratedSchedule:
    id: str
    generated_at: str
    schedule_text: str
    slots: List[GeneratedScheduleSlotSnapshot] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "generated_at": self.generated_at,
            "schedule_text": self.schedule_text,
            "slots": [s.to_dict() for s in self.slots],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GeneratedSchedule":
        return cls(
            id=data["id"],
            generated_at=data["generated_at"],
            schedule_text=data.get("schedule_text", ""),
            slots=[GeneratedScheduleSlotSnapshot.from_dict(s) for s in data.get("slots", [])],
        )


@dataclass
class FinalizedEventBatchEntry:
    event_id: str
    name: str
    date: str
    time: str
    participating_acolyte_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "name": self.name,
            "date": self.date,
            "time": self.time,
            "participating_acolyte_ids": self.participating_acolyte_ids,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "FinalizedEventBatchEntry":
        return cls(
            event_id=data["event_id"],
            name=data["name"],
            date=data["date"],
            time=data.get("time", ""),
            participating_acolyte_ids=data.get("participating_acolyte_ids", []),
        )


@dataclass
class FinalizedEventBatch:
    id: str
    finalized_at: str
    entries: List[FinalizedEventBatchEntry] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "finalized_at": self.finalized_at,
            "entries": [e.to_dict() for e in self.entries],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "FinalizedEventBatch":
        return cls(
            id=data["id"],
            finalized_at=data["finalized_at"],
            entries=[FinalizedEventBatchEntry.from_dict(e) for e in data.get("entries", [])],
        )


@dataclass
class StandardSlot:
    day: str
    time: str
    description: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "day": self.day,
            "time": self.time,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "StandardSlot":
        return cls(
            id=data["id"],
            day=data["day"],
            time=data["time"],
            description=data.get("description", ""),
        )


@dataclass
class CicloHistoryEntry:
    """Snapshot do estado do sistema ao fechar um ciclo."""

    id: str
    closed_at: str  # timestamp DD/MM/YYYY HH:MM
    label: str  # user-defined label for the cycle
    acolytes_snapshot: List[dict] = field(default_factory=list)
    schedule_slots_snapshot: List[dict] = field(default_factory=list)
    general_events_snapshot: List[dict] = field(default_factory=list)
    generated_schedules_snapshot: List[dict] = field(default_factory=list)
    finalized_event_batches_snapshot: List[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "closed_at": self.closed_at,
            "label": self.label,
            "acolytes_snapshot": self.acolytes_snapshot,
            "schedule_slots_snapshot": self.schedule_slots_snapshot,
            "general_events_snapshot": self.general_events_snapshot,
            "generated_schedules_snapshot": self.generated_schedules_snapshot,
            "finalized_event_batches_snapshot": self.finalized_event_batches_snapshot,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CicloHistoryEntry":
        return cls(
            id=data["id"],
            closed_at=data["closed_at"],
            label=data.get("label", ""),
            acolytes_snapshot=data.get("acolytes_snapshot", []),
            schedule_slots_snapshot=data.get("schedule_slots_snapshot", []),
            general_events_snapshot=data.get("general_events_snapshot", []),
            generated_schedules_snapshot=data.get("generated_schedules_snapshot", []),
            finalized_event_batches_snapshot=data.get("finalized_event_batches_snapshot", []),
        )
