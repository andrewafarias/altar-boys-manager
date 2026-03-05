"""Script to generate acolitos_data.json from table information."""

import json
import os
import uuid
from datetime import datetime
from pathlib import Path

# Get project root directory (two levels up from this script)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"

# Table data parsed from the spreadsheet
table_data = [
    {
        "name": "Andrew",
        "escala": "01/01 - 04/01",
        "reuniao": "04/01",
        "terco": "04/01",
        "total_semestre": 0,
        "faltas_data": "",
        "faltas_suspensao": "",
        "bonus_disponivel": 999,
        "bonus_utilizado": ""
    },
    {
        "name": "Augusto",
        "escala": "01/01 - 03/01 - 04/01",
        "reuniao": "04/01",
        "terco": "04/01",
        "total_semestre": 0,
        "faltas_data": "",
        "faltas_suspensao": "",
        "bonus_disponivel": 1,
        "bonus_utilizado": ""
    },
    {
        "name": "Daniel",
        "escala": "01/01 - 04/01",
        "reuniao": "04/01",
        "terco": "04/01",
        "total_semestre": 0,
        "faltas_data": "",
        "faltas_suspensao": "",
        "bonus_disponivel": 0,
        "bonus_utilizado": ""
    },
    {
        "name": "Edmilson",
        "escala": "01/01 - 04/01",
        "reuniao": "04/01",
        "terco": "04/01",
        "total_semestre": 0,
        "faltas_data": "",
        "faltas_suspensao": "",
        "bonus_disponivel": 0,
        "bonus_utilizado": ""
    },
    {
        "name": "Flavio",
        "escala": "01/01 - 04/01",
        "reuniao": "04/01",
        "terco": "04/01",
        "total_semestre": 0,
        "faltas_data": "",
        "faltas_suspensao": "",
        "bonus_disponivel": 1,
        "bonus_utilizado": ""
    },
    {
        "name": "Francisco",
        "escala": "01/01 - 04/01",
        "reuniao": "04/01",
        "terco": "04/01",
        "total_semestre": 1,
        "faltas_data": "04/01 (E/T)",
        "faltas_suspensao": "01/01 - 25/01",
        "bonus_disponivel": 0,
        "bonus_utilizado": ""
    },
    {
        "name": "Gabriel Castro",
        "escala": "01/01 - 02/01 - 04/01",
        "reuniao": "04/01",
        "terco": "04/01",
        "total_semestre": 0,
        "faltas_data": "",
        "faltas_suspensao": "",
        "bonus_disponivel": 2,
        "bonus_utilizado": ""
    },
    {
        "name": "Gabriel Teixeira",
        "escala": "01/01 - 04/01",
        "reuniao": "04/01",
        "terco": "04/01",
        "total_semestre": 0,
        "faltas_data": "",
        "faltas_suspensao": "",
        "bonus_disponivel": 1,
        "bonus_utilizado": ""
    },
    {
        "name": "Guilherme",
        "escala": "01/01 - 04/01",
        "reuniao": "04/01",
        "terco": "04/01",
        "total_semestre": 1,
        "faltas_data": "04/01 (E/T)",
        "faltas_suspensao": "",
        "bonus_disponivel": 0,
        "bonus_utilizado": ""
    },
    {
        "name": "Gustavo",
        "escala": "01/01 - 03/01 - 04/01",
        "reuniao": "04/01",
        "terco": "04/01",
        "total_semestre": 0,
        "faltas_data": "",
        "faltas_suspensao": "",
        "bonus_disponivel": 0,
        "bonus_utilizado": ""
    },
    {
        "name": "Igor",
        "escala": "01/01 - 03/01 - 04/01",
        "reuniao": "04/01",
        "terco": "04/01",
        "total_semestre": 0,
        "faltas_data": "",
        "faltas_suspensao": "",
        "bonus_disponivel": 3,
        "bonus_utilizado": ""
    },
    {
        "name": "João Ferreira",
        "escala": "01/01 - 04/01",
        "reuniao": "04/01",
        "terco": "04/01",
        "total_semestre": 0,
        "faltas_data": "",
        "faltas_suspensao": "",
        "bonus_disponivel": 0,
        "bonus_utilizado": ""
    },
    {
        "name": "Joaquim",
        "escala": "01/01 - 02/01 - 04/01",
        "reuniao": "04/01",
        "terco": "04/01",
        "total_semestre": 0,
        "faltas_data": "",
        "faltas_suspensao": "",
        "bonus_disponivel": 0,
        "bonus_utilizado": ""
    },
    {
        "name": "Jonas",
        "escala": "01/01 - 04/01",
        "reuniao": "04/01",
        "terco": "04/01",
        "total_semestre": 0,
        "faltas_data": "",
        "faltas_suspensao": "01/01 - 11/01",
        "bonus_disponivel": 1,
        "bonus_utilizado": ""
    },
    {
        "name": "Jorge",
        "escala": "01/01 - 04/01",
        "reuniao": "04/01",
        "terco": "04/01",
        "total_semestre": 1,
        "faltas_data": "04/01 (E/T)",
        "faltas_suspensao": "",
        "bonus_disponivel": 1,
        "bonus_utilizado": ""
    },
    {
        "name": "Júlio César",
        "escala": "01/01 - 04/01",
        "reuniao": "04/01",
        "terco": "04/01",
        "total_semestre": 0,
        "faltas_data": "",
        "faltas_suspensao": "",
        "bonus_disponivel": 0,
        "bonus_utilizado": ""
    },
    {
        "name": "Júnior",
        "escala": "01/01 - 04/01",
        "reuniao": "04/01",
        "terco": "04/01",
        "total_semestre": 0,
        "faltas_data": "",
        "faltas_suspensao": "",
        "bonus_disponivel": 0,
        "bonus_utilizado": ""
    },
    {
        "name": "Lucas Gonçalves",
        "escala": "01/01 - 04/01",
        "reuniao": "04/01",
        "terco": "04/01",
        "total_semestre": 0,
        "faltas_data": "",
        "faltas_suspensao": "",
        "bonus_disponivel": 3,
        "bonus_utilizado": ""
    },
    {
        "name": "Lucas Ribeiro",
        "escala": "01/01 - 04/01 (2x)",
        "reuniao": "04/01",
        "terco": "04/01",
        "total_semestre": 0,
        "faltas_data": "",
        "faltas_suspensao": "",
        "bonus_disponivel": 0,
        "bonus_utilizado": ""
    },
    {
        "name": "Matheus Castro",
        "escala": "01/01 - 04/01",
        "reuniao": "04/01",
        "terco": "04/01",
        "total_semestre": 0,
        "faltas_data": "",
        "faltas_suspensao": "",
        "bonus_disponivel": 0,
        "bonus_utilizado": ""
    },
    {
        "name": "Matheus Magalhães",
        "escala": "01/01 - 04/01",
        "reuniao": "04/01",
        "terco": "04/01",
        "total_semestre": 0,
        "faltas_data": "",
        "faltas_suspensao": "",
        "bonus_disponivel": 0,
        "bonus_utilizado": ""
    },
    {
        "name": "Miguel",
        "escala": "01/01 - 04/01",
        "reuniao": "04/01",
        "terco": "04/01",
        "total_semestre": 0,
        "faltas_data": "",
        "faltas_suspensao": "",
        "bonus_disponivel": 0,
        "bonus_utilizado": ""
    },
    {
        "name": "Natalino",
        "escala": "01/01 - 04/01 (2x)",
        "reuniao": "04/01",
        "terco": "04/01",
        "total_semestre": 0,
        "faltas_data": "",
        "faltas_suspensao": "",
        "bonus_disponivel": 0,
        "bonus_utilizado": "04/01 (E/T)"
    },
    {
        "name": "Sandro",
        "escala": "01/01 - 04/01",
        "reuniao": "04/01",
        "terco": "04/01",
        "total_semestre": 0,
        "faltas_data": "",
        "faltas_suspensao": "",
        "bonus_disponivel": 3,
        "bonus_utilizado": ""
    },
]


def parse_dates(date_str):
    """Parse date string like '01/01 - 03/01 - 04/01' into list of dates."""
    if not date_str:
        return []
    
    dates = []
    parts = date_str.split(" - ")
    for part in parts:
        # Handle (2x) notation
        if "(2x)" in part:
            date = part.replace("(2x)", "").strip()
            dates.append(date)
            dates.append(date)  # Add twice
        else:
            dates.append(part.strip())
    
    return dates


def create_schedule_entry(date, count=0):
    """Create a schedule history entry."""
    return {
        "schedule_id": f"historical-{date}" + (f"-{count}" if count > 0 else ""),
        "date": f"{date}/2026",
        "day": "Quarta-feira",  # Default day
        "time": "18:00",
        "description": "---"
    }


def create_event_entry(event_name, date):
    """Create an event history entry."""
    return {
        "event_id": f"event-{event_name.lower()}-{date}",
        "name": event_name,
        "date": f"{date}/2026",
        "time": "18:00"
    }


def create_absence(date, description):
    """Create an absence entry."""
    return {
        "id": str(uuid.uuid4()),
        "date": f"{date}/2026",
        "description": description
    }


def create_suspension(start_date, end_date):
    """Create a suspension entry."""
    return {
        "id": str(uuid.uuid4()),
        "reason": "Falta em evento obrigatório",
        "start_date": f"{start_date}/2026",
        "duration": "",
        "is_active": False,
        "end_date": f"{end_date}/2026"
    }


def create_bonus_movement(movement_type, amount, description, date):
    """Create a bonus movement entry."""
    return {
        "id": str(uuid.uuid4()),
        "type": movement_type,
        "amount": amount,
        "description": description,
        "date": f"{date}/2026"
    }


def generate_acolyte_data(acolyte_info):
    """Generate complete acolyte data structure."""
    # Calculate initial bonus count (available + used)
    initial_bonus = acolyte_info["bonus_disponivel"]
    if acolyte_info["bonus_utilizado"]:
        initial_bonus += 1  # They had at least 1 bonus to use
    
    acolyte = {
        "id": str(uuid.uuid4()),
        "name": acolyte_info["name"],
        "times_scheduled": 0,
        "absences": [],
        "suspensions": [],
        "is_suspended": False,
        "bonus_count": initial_bonus,
        "bonus_movements": [],
        "schedule_history": [],
        "event_history": []
    }
    
    # Parse and add schedule history (Escala)
    escala_dates = parse_dates(acolyte_info["escala"])
    date_counts = {}
    for date in escala_dates:
        count = date_counts.get(date, 0)
        acolyte["schedule_history"].append(create_schedule_entry(date, count))
        date_counts[date] = count + 1
        acolyte["times_scheduled"] += 1
    
    # Add event history (Reunião and Terço)
    if acolyte_info["reuniao"]:
        acolyte["event_history"].append(create_event_entry("Reunião", acolyte_info["reuniao"]))
    
    if acolyte_info["terco"]:
        # Only add if not absent (E/T in faltas_data OR bonus_utilizado)
        has_et_absence = "E/T" in acolyte_info["faltas_data"]
        used_bonus_for_et = "E/T" in acolyte_info["bonus_utilizado"]
        
        if not has_et_absence and not used_bonus_for_et:
            acolyte["event_history"].append(create_event_entry("Terço", acolyte_info["terco"]))
    
    # Process absences
    if acolyte_info["faltas_data"]:
        faltas_data = acolyte_info["faltas_data"]
        if "E/T" in faltas_data:
            # Extract date
            date = faltas_data.replace("(E/T)", "").strip()
            acolyte["absences"].append(create_absence(date, "Falta em Escala/Terço"))
    
    # Process suspensions
    if acolyte_info["faltas_suspensao"]:
        dates = acolyte_info["faltas_suspensao"].split(" - ")
        if len(dates) >= 2:
            start_date = dates[0].strip()
            end_date = dates[1].strip()
            acolyte["suspensions"].append(create_suspension(start_date, end_date))
    
    # Process bonus movements
    if initial_bonus > 0:
        # Add a single movement with the full initial bonus amount
        acolyte["bonus_movements"].append(
            create_bonus_movement("earn", initial_bonus, "Bônus disponível inicial", "01/01")
        )
    
    # Process bonus usage
    if acolyte_info["bonus_utilizado"]:
        bonus_usado = acolyte_info["bonus_utilizado"]
        if "E/T" in bonus_usado:
            date = bonus_usado.replace("(E/T)", "").strip()
            acolyte["bonus_movements"].append(
                create_bonus_movement("use", 1, "Usado para compensar falta E/T", date)
            )
            acolyte["bonus_count"] -= 1
    
    return acolyte


def main():
    """Generate the complete data file."""
    acolytes = []
    
    for acolyte_info in table_data:
        acolyte_data = generate_acolyte_data(acolyte_info)
        acolytes.append(acolyte_data)
    
    # Create the complete data structure
    output = {
        "acolytes": acolytes
    }
    
    # Create data directory if it doesn't exist
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # Write to file
    data_file = DATA_DIR / "acolitos_data.json"
    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Data file generated successfully with {len(acolytes)} acolytes!")
    print(f"📊 Total scheduled entries: {sum(a['times_scheduled'] for a in acolytes)}")
    print(f"📋 Total absences: {sum(len(a['absences']) for a in acolytes)}")
    print(f"🎁 Total bonus available: {sum(a['bonus_count'] for a in acolytes)}")


if __name__ == "__main__":
    main()
