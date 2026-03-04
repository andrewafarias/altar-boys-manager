import uuid
from dataclasses import dataclass, field
from typing import List


@dataclass
class BonusMovement:
    date: str
    type: str  # 'give' or 'use'
    amount: int
    description: str


@dataclass
class Absence:
    date: str
    description: str


@dataclass
class Suspension:
    date: str
    reason: str
    duration: str
    active: bool = True


@dataclass
class HistoryEntry:
    date: str
    time: str
    description: str
    entry_type: str  # 'escala' or 'evento'


@dataclass
class Acolyte:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    vezes_escalado: int = 0
    absences: List[Absence] = field(default_factory=list)
    suspensions: List[Suspension] = field(default_factory=list)
    is_suspended: bool = False
    suspension_duration: str = ""
    bonus: int = 0
    bonus_movements: List[BonusMovement] = field(default_factory=list)
    history: List[HistoryEntry] = field(default_factory=list)


@dataclass
class ScheduleSlot:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    date: str = ""   # DD/MM/YYYY
    time: str = ""   # HH:MM
    description: str = ""
    acolyte_ids: List[str] = field(default_factory=list)


@dataclass
class GeneralEvent:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    date: str = ""
    time: str = ""   # optional
    description: str = ""
    excluded_acolyte_ids: List[str] = field(default_factory=list)
    registered: bool = False
