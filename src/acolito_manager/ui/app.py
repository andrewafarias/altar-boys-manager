"""Classe principal da aplicação."""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import List, Optional
from datetime import datetime, timedelta

from ..data_manager import save_data, load_data, export_to_file, import_from_file
from ..utils import get_birthday_acolytes_this_week, detect_weekday
from ..models import (
    Acolyte,
    ScheduleSlot,
    GeneralEvent,
    GeneratedSchedule,
    FinalizedEventBatch,
    StandardSlot,
    CicloHistoryEntry,
)
from .schedule_tab import ScheduleTab
from .acolytes_tab import AcolytesTab
from .history_tab import HistoryTab
from .calendar_tab import CalendarTab


class App:
    """Aplicação principal de gerenciamento de escala de acólitos."""

    def __init__(self):
        self.acolytes: List[Acolyte] = []
        self.schedule_slots: List[ScheduleSlot] = []
        self.general_events: List[GeneralEvent] = []
        self.generated_schedules: List[GeneratedSchedule] = []
        self.finalized_event_batches: List[FinalizedEventBatch] = []
        self.standard_slots: List[StandardSlot] = []
        self.ciclo_history: List[CicloHistoryEntry] = []
        self.custom_common_times: List[str] = []
        self.include_suspended_in_general_event: bool = True
        self.include_activity_table_per_acolyte: bool = True
        self.auto_lift_suspensions_on_end_date: bool = False
        self.current_cycle_name: str = ""
        self.birthday_settings: dict = {
            "enabled": False,
            "whatsapp_group": "",
            "message_template": "Feliz aniversário, {nome}! 🎂🎉",
            "send_time": "08:00",
            "muted_birthdate_notifications": [],
        }

        self.root = tk.Tk()
        self.root.title("Gerenciador de Acólitos")
        self.root.geometry("1200x800")
        self.root.minsize(900, 600)

        self._apply_theme()
        self._build_menu()
        self._build_notebook()
        self._load_data()

        # Make custom_common_times accessible to time picker
        from .widgets import TimePickerDialog
        TimePickerDialog._app = self

        # Show birthday warning after startup
        self.root.after(500, self._check_birthdays_this_week)

    def _apply_theme(self):
        style = ttk.Style(self.root)
        available = style.theme_names()
        if "clam" in available:
            style.theme_use("clam")
        style.configure("TNotebook.Tab", padding=[10, 4])
        style.configure("Accent.TButton", font=("TkDefaultFont", 10, "bold"))

    def _build_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Arquivo", menu=file_menu)
        file_menu.add_command(label="Salvar", command=self.save, accelerator="Ctrl+S")
        file_menu.add_command(label="Carregar", command=self._load_data)
        file_menu.add_separator()
        file_menu.add_command(label="Exportar Dados...", command=self._export_data)
        file_menu.add_command(label="Importar Dados...", command=self._import_data)
        file_menu.add_separator()
        file_menu.add_command(label="Sair", command=self.root.quit)

        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Configurações", menu=settings_menu)
        self._include_suspended_general_event_var = tk.BooleanVar(
            value=self.include_suspended_in_general_event
        )
        settings_menu.add_checkbutton(
            label="Incluir acólitos suspensos na Escala Geral",
            variable=self._include_suspended_general_event_var,
            command=self._on_toggle_include_suspended_general_event,
        )
        self._include_activity_table_per_acolyte_var = tk.BooleanVar(
            value=self.include_activity_table_per_acolyte
        )
        settings_menu.add_checkbutton(
            label="Incluir tabela de atividades para cada acólito",
            variable=self._include_activity_table_per_acolyte_var,
            command=self._on_toggle_include_activity_table_per_acolyte,
        )
        self._auto_lift_suspensions_var = tk.BooleanVar(
            value=self.auto_lift_suspensions_on_end_date
        )
        settings_menu.add_checkbutton(
            label="Levantar suspensões automaticamente ao atingir data final",
            variable=self._auto_lift_suspensions_var,
            command=self._on_toggle_auto_lift_suspensions,
        )

        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Ajuda", menu=help_menu)
        help_menu.add_command(label="Sobre", command=self._show_about)

        self.root.bind("<Control-s>", lambda e: self.save())

    def _build_notebook(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        self.schedule_tab = ScheduleTab(self.notebook, self)
        self.events_tab = self.schedule_tab.events_tab
        self.acolytes_tab = AcolytesTab(self.notebook, self)
        self.history_tab = HistoryTab(self.notebook, self)
        self.calendar_tab = CalendarTab(self.notebook, self)

        self.notebook.add(self.schedule_tab, text="🛠️ Criar Escala")
        self.notebook.add(self.acolytes_tab, text="👥 Acólitos")
        self.notebook.add(self.calendar_tab, text="📆 Calendário")
        self.notebook.add(self.history_tab, text="📜 Histórico")

        # Auto-refresh calendar when its tab is selected
        self.notebook.bind("<<NotebookTabChanged>>", self._on_main_tab_changed)

    def _on_main_tab_changed(self, _event=None):
        selected = self.notebook.select()
        if selected == str(self.calendar_tab):
            self.calendar_tab.refresh()

    def _load_data(self):
        result = load_data()
        (
            self.acolytes,
            self.schedule_slots,
            self.general_events,
            self.generated_schedules,
            self.finalized_event_batches,
            self.standard_slots,
            self.ciclo_history,
            self.custom_common_times,
            self.include_suspended_in_general_event,
            self.include_activity_table_per_acolyte,
            self.auto_lift_suspensions_on_end_date,
            self.current_cycle_name,
            self.birthday_settings,
        ) = result
        self.birthday_settings.setdefault("muted_birthdate_notifications", [])
        if hasattr(self, "_include_suspended_general_event_var"):
            self._include_suspended_general_event_var.set(
                self.include_suspended_in_general_event
            )
        if hasattr(self, "_include_activity_table_per_acolyte_var"):
            self._include_activity_table_per_acolyte_var.set(
                self.include_activity_table_per_acolyte
            )
        if hasattr(self, "_auto_lift_suspensions_var"):
            self._auto_lift_suspensions_var.set(
                self.auto_lift_suspensions_on_end_date
            )
        self.schedule_tab.refresh_acolyte_list()
        self.schedule_tab.load_slots_from_data(adapt_dates=True)
        self.events_tab.refresh_list()
        self.acolytes_tab.sync_current_cycle_name()
        self.acolytes_tab.refresh_list()
        self.history_tab.refresh()
        self.calendar_tab.refresh()
        self._prune_expired_unavailabilities()

    def _prune_expired_unavailabilities(self):
        """Remove indisponibilidades temporárias cuja data de fim já passou."""
        today = datetime.now().date()
        changed = False
        for ac in self.acolytes:
            temp_unavs = getattr(ac, 'temporary_unavailabilities', None)
            if not temp_unavs:
                continue
            before = len(temp_unavs)
            ac.temporary_unavailabilities = [
                t for t in temp_unavs
                if datetime.strptime(t.end_date, "%d/%m/%Y").date() >= today
            ]
            if len(ac.temporary_unavailabilities) < before:
                changed = True
        if changed:
            self.save()

    def save(self):
        save_data(
            self.acolytes,
            self.schedule_slots,
            self.general_events,
            self.generated_schedules,
            self.finalized_event_batches,
            self.standard_slots,
            self.ciclo_history,
            self.custom_common_times,
            self.include_suspended_in_general_event,
            self.include_activity_table_per_acolyte,
            self.auto_lift_suspensions_on_end_date,
            self.current_cycle_name,
            self.birthday_settings,
        )

    def _on_toggle_include_suspended_general_event(self):
        self.include_suspended_in_general_event = bool(
            self._include_suspended_general_event_var.get()
        )
        self.save()

    def _on_toggle_include_activity_table_per_acolyte(self):
        self.include_activity_table_per_acolyte = bool(
            self._include_activity_table_per_acolyte_var.get()
        )
        self.save()

    def _on_toggle_auto_lift_suspensions(self):
        self.auto_lift_suspensions_on_end_date = bool(
            self._auto_lift_suspensions_var.get()
        )
        self.save()

    def find_acolyte(self, acolyte_id: str) -> Optional[Acolyte]:
        for ac in self.acolytes:
            if ac.id == acolyte_id:
                return ac
        return None

    def build_current_cycle_history_entry(self, label: str) -> CicloHistoryEntry:
        import uuid as _uuid

        return CicloHistoryEntry(
            id=str(_uuid.uuid4()),
            closed_at=datetime.now().strftime("%d/%m/%Y %H:%M"),
            label=label,
            acolytes_snapshot=[a.to_dict() for a in self.acolytes],
            schedule_slots_snapshot=[s.to_dict() for s in self.schedule_slots],
            general_events_snapshot=[e.to_dict() for e in self.general_events],
            generated_schedules_snapshot=[gs.to_dict() for gs in self.generated_schedules],
            finalized_event_batches_snapshot=[fb.to_dict() for fb in self.finalized_event_batches],
        )

    def get_selected_acolyte_for_schedule(self) -> Optional[Acolyte]:
        """Retorna o acólito selecionado na aba de escalas."""
        return self.schedule_tab.get_selected_acolyte()

    def get_selected_acolytes_for_schedule(self) -> List[Acolyte]:
        """Retorna todos os acólitos selecionados na aba de escalas."""
        return self.schedule_tab.get_selected_acolytes()

    def _export_data(self):
        """Exporta todos os dados para um arquivo JSON."""
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON", "*.json")],
            title="Exportar dados como",
            initialfile="acolitos_backup.json",
        )
        if not path:
            return
        try:
            export_to_file(
                self.acolytes,
                self.schedule_slots,
                self.general_events,
                path,
                self.generated_schedules,
                self.finalized_event_batches,
                self.standard_slots,
                self.ciclo_history,
                self.custom_common_times,
                self.include_suspended_in_general_event,
                self.include_activity_table_per_acolyte,
                self.auto_lift_suspensions_on_end_date,
                self.current_cycle_name,
                self.birthday_settings,
            )
            messagebox.showinfo("Sucesso", f"Dados exportados com sucesso para:\n{path}")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao exportar dados:\n{e}")

    def _import_data(self):
        """Importa todos os dados de um arquivo JSON."""
        path = filedialog.askopenfilename(
            filetypes=[("JSON", "*.json")],
            title="Importar dados de",
        )
        if not path:
            return
        if not messagebox.askyesno(
            "Confirmar Importação",
            "Atenção: isso substituirá TODOS os dados atuais pelos dados do arquivo importado.\n\n"
            "Deseja continuar?",
        ):
            return
        try:
            (
                acolytes,
                schedule_slots,
                general_events,
                generated_schedules,
                finalized_event_batches,
                standard_slots,
                ciclo_history,
                custom_common_times,
                include_suspended_in_general_event,
                include_activity_table_per_acolyte,
                auto_lift_suspensions_on_end_date,
                current_cycle_name,
                birthday_settings,
            ) = import_from_file(path)
            self.acolytes = acolytes
            self.schedule_slots = schedule_slots
            self.general_events = general_events
            self.generated_schedules = generated_schedules
            self.finalized_event_batches = finalized_event_batches
            self.standard_slots = standard_slots
            self.ciclo_history = ciclo_history
            self.custom_common_times = custom_common_times
            self.include_suspended_in_general_event = include_suspended_in_general_event
            self.include_activity_table_per_acolyte = include_activity_table_per_acolyte
            self.auto_lift_suspensions_on_end_date = auto_lift_suspensions_on_end_date
            self.current_cycle_name = current_cycle_name
            self.birthday_settings = birthday_settings
            self.save()
            self._load_data()
            messagebox.showinfo(
                "Sucesso",
                f"Dados importados com sucesso!\n\n"
                f"{len(acolytes)} acólitos, {len(schedule_slots)} escalas, "
                f"{len(general_events)} atividades.",
            )
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao importar dados:\n{e}")

    def _show_about(self):
        messagebox.showinfo(
            "Sobre",
            "Gerenciador de Acólitos\n\n"
            "Ferramenta para gerenciar a escala de acólitos de uma igreja.\n\n"
            "Funcionalidades:\n"
            "- Criar e gerenciar escalas semanais\n"
            "- Registrar atividades\n"
            "- Gerenciar acólitos (faltas, bônus, suspensões)\n"
            "- Gerar relatórios em PDF",
        )

    def _open_birthday_settings(self):
        from .dialogs import BirthdaySettingsDialog
        dialog = BirthdaySettingsDialog(self.root, self.birthday_settings)
        if dialog.result is not None:
            # Preserva os aniversários específicos ocultados no popup semanal.
            dialog.result.setdefault(
                "muted_birthdate_notifications",
                list(self.birthday_settings.get("muted_birthdate_notifications", [])),
            )
            self.birthday_settings = dialog.result
            self.save()

    def _birthday_occurrence_in_notify_window(self, acolyte: Acolyte) -> Optional[datetime.date]:
        """Retorna a data de ocorrência no intervalo de hoje -8 até hoje +8 dias."""
        if not acolyte.birthdate:
            return None

        today = datetime.now().date()
        start_window = today - timedelta(days=8)
        end_window = today + timedelta(days=8)

        try:
            bd = datetime.strptime(acolyte.birthdate, "%d/%m/%Y").date()
        except ValueError:
            return None

        for year in (today.year - 1, today.year, today.year + 1):
            try:
                occurrence = bd.replace(year=year)
            except ValueError:
                # Ignora 29/02 em anos não bissextos.
                continue
            if start_window <= occurrence <= end_window:
                return occurrence
        return None

    def _check_birthdays_this_week(self):
        birthday_acolytes = get_birthday_acolytes_this_week(self.acolytes)
        if not birthday_acolytes:
            return

        muted_notifications = set(
            self.birthday_settings.get("muted_birthdate_notifications", [])
        )

        birthday_items = []
        for ac in birthday_acolytes:
            occurrence = self._birthday_occurrence_in_notify_window(ac)
            if occurrence is None:
                continue

            notification_key = f"{ac.id}|{occurrence.strftime('%d/%m/%Y')}"
            if notification_key in muted_notifications:
                continue

            try:
                bd = datetime.strptime(ac.birthdate, "%d/%m/%Y")
                date_str = bd.strftime('%d/%m')
                weekday = detect_weekday(ac.birthdate)
                if weekday:
                    label = f"🎂 {ac.name} — {date_str} ({weekday})"
                else:
                    label = f"🎂 {ac.name} — {date_str}"
            except ValueError:
                label = f"🎂 {ac.name}"

            birthday_items.append({"id": notification_key, "label": label})

        if not birthday_items:
            return

        from .dialogs import BirthdayWeekDialog
        dialog = BirthdayWeekDialog(self.root, birthday_items)
        muted_selected = set(dialog.result or [])
        if muted_selected:
            updated_muted = sorted(muted_notifications.union(muted_selected))
            self.birthday_settings["muted_birthdate_notifications"] = updated_muted
            self.save()

    def run(self):
        self.root.mainloop()
