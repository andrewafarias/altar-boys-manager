# Acolito Manager

Church acolyte scheduling and management application built with Python and Tkinter.

## 📁 Project Structure

```
escala_acolitos/
├── src/                              # Source code
│   ├── __init__.py
│   └── acolito_manager/             # Main application package
│       ├── __init__.py
│       ├── main.py                  # Entry point
│       ├── models.py                # Data models (Acolyte, Schedule, Event, etc.)
│       ├── data_manager.py          # JSON persistence layer
│       ├── report_generator.py      # PDF report generation (reportlab)
│       ├── utils.py                 # Utility functions
│       └── ui/                      # User interface modules
│           ├── __init__.py
│           ├── app.py               # Main App class
│           ├── base.py              # BaseDialog base class
│           ├── widgets.py           # Calendar & time picker widgets
│           ├── dialogs.py           # Modal dialogs (12 dialog classes)
│           ├── schedule_tab.py      # Schedule creation tab
│           ├── events_tab.py        # Activities management tab
│           ├── acolytes_tab.py      # Acolyte management tab
│           └── history_tab.py       # Schedule/activity history tab
│
├── data/                             # Runtime data storage
│   └── acolitos_data.json           # App data (auto-generated)
│
├── scripts/                          # Utility scripts
│   ├── setup_and_run.py            # Cross-platform setup & launch
│   ├── generate_data.py            # Initial data generation
│   ├── run.sh                       # Linux/Mac launcher
│   └── run.bat                      # Windows launcher
│
├── config/                           # Configuration files
│   └── prompt_inicial.txt           # Initial prompt/template
│
├── main.py                           # Root entry point (launcher)
├── requirements.txt                  # Python dependencies
├── .gitignore
└── README.md                         # This file
```

## 🚀 Quick Start

### Prerequisites
- Python 3.7+
- pip (Python package manager)

### Option 1: Simple Launch
```bash
python3 main.py
```

### Option 2: Managed Setup (Linux/Mac)
```bash
bash scripts/run.sh
```

### Option 3: Managed Setup (Windows)
```bash
scripts\run.bat
```

## 📦 Dependencies

- **reportlab** >= 3.6.0 - PDF report generation

Install dependencies:
```bash
pip install -r requirements.txt
```

## 🛠️ Development

### Project Layout Philosophy

- **`src/acolito_manager/`** - All source code organized by function
  - Core logic: models, data persistence, reports
  - UI layer: completely separated into modular components
  
- **`data/`** - Runtime data (ignored in git)

- **`scripts/`** - Helper tools and automation

- **`config/`** - Configuration templates

- **`main.py`** - Minimal entry point that adds src/ to Python path

### Import Pattern

Files within `src/acolito_manager/` use relative imports:

```python
# Within ui/schedule_tab.py
from ..models import Acolyte          # Parent package
from ..utils import today_str          # Parent package
from .dialogs import AddEventDialog   # Same package
from .widgets import DateEntryFrame   # Same package
```

### Adding New Features

1. Create UI components in `src/acolito_manager/ui/`
2. Add data models to `src/acolito_manager/models.py`
3. Update `src/acolito_manager/ui/app.py` to wire components

## 📝 Key Features

- **Schedule Management**: Create and manage acolyte schedules
- **Activity Tracking**: Record church activities and participation
- **Acolyte Management**: Track absence, suspensions, and bonus points
- **PDF Reports**: Generate comprehensive reports with reportlab
- **Data Persistence**: All data saved to JSON
- **Cross-Platform**: Works on Windows, Linux, and macOS

## 📄 License

All rights reserved © Andrew Farias

## 🤝 Contributing

This is a church management tool. Contributions welcome for:
- UI improvements
- New features
- Bug fixes
- Documentation

---

**Last Updated:** March 2026
