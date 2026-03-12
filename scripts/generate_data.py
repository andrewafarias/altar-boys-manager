"""Script to generate acolitos_data.json with clean acolyte records."""

import json
import os
import uuid
from pathlib import Path

# Get project root directory (two levels up from this script)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"

ACOLYTE_NAMES = [
    "Andrew",
    "Augusto",
    "Daniel",
    "Edmilson",
    "Flavio",
    "Gabriel Castro",
    "Gabriel Teixeira",
    "Guilherme",
    "Gustavo",
    "Igor",
    "João Ferreira",
    "Joaquim",
    "Jonas",
    "Jorge",
    "Júlio César",
    "Júnior",
    "Lucas Gonçalves",
    "Lucas Ribeiro",
    "Matheus Castro",
    "Matheus Magalhães",
    "Miguel",
    "Natalino",
    "Sandro",
]


def generate_acolyte_data(name: str):
    """Generate a clean acolyte record with all attributes reset."""
    return {
        "id": str(uuid.uuid4()),
        "name": name,
        "internal_notes": "",
        "times_scheduled": 0,
        "absences": [],
        "suspensions": [],
        "is_suspended": False,
        "bonus_count": 0,
        "bonus_movements": [],
        "schedule_history": [],
        "event_history": [],
        "unavailabilities": [],
        "birthdate": "",
    }


def main():
    """Generate the complete data file."""
    acolytes = []
    
    for name in ACOLYTE_NAMES:
        acolyte_data = generate_acolyte_data(name)
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
    print("ℹ️ All imported acolyte attributes were reset to default values.")


if __name__ == "__main__":
    main()
