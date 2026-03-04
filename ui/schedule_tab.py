import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from typing import List, Callable

from models.models import ScheduleSlot, Acolyte

WEEKDAYS_PT = [
    "Segunda-feira", "Terça-feira", "Quarta-feira",
    "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"
]


def _format_acolyte_list(names: List[str]) -> str:
    if not names:
        return "(nenhum)"
    if len(names) == 1:
        return names[0]
    return ", ".join(names[:-1]) + " e " + names[-1]


def _weekday_pt(date_str: str) -> str:
    """Return Portuguese weekday name from DD/MM/YYYY string."""
    try:
        dt = datetime.strptime(date_str, "%d/%m/%Y")
        return WEEKDAYS_PT[dt.weekday()]
    except ValueError:
        return date_str


def _generate_schedule_text(slots: List[ScheduleSlot], acolytes_by_id: dict) -> str:
    lines = ["ESCALA DA SEMANA"]
    for slot in slots:
        lines.append("")
        date_short = slot.date[:5] if len(slot.date) >= 5 else slot.date
        weekday = _weekday_pt(slot.date)
        header = f"{weekday}, {date_short} - {slot.time}:"
        lines.append(header)
        if slot.description:
            lines.append(slot.description)
        names = [acolytes_by_id[aid].name for aid in slot.acolyte_ids if aid in acolytes_by_id]
        lines.append(_format_acolyte_list(names))
    return "\n".join(lines)


class NewSlotDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Novo Horário")
        self.resizable(False, False)
        self.result = None
        self._build()
        self.grab_set()
        self.wait_window()

    def _build(self):
        pad = {"padx": 8, "pady": 4}
        ttk.Label(self, text="Data (DD/MM/AAAA):").grid(row=0, column=0, sticky="w", **pad)
        self._date = ttk.Entry(self, width=16)
        self._date.grid(row=0, column=1, **pad)

        ttk.Label(self, text="Hora (HH:MM):").grid(row=1, column=0, sticky="w", **pad)
        self._time = ttk.Entry(self, width=10)
        self._time.grid(row=1, column=1, **pad)

        ttk.Label(self, text="Descrição (opcional):").grid(row=2, column=0, sticky="w", **pad)
        self._desc = ttk.Entry(self, width=30)
        self._desc.grid(row=2, column=1, **pad)

        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=8)
        ttk.Button(btn_frame, text="OK", command=self._ok).pack(side="left", padx=4)
        ttk.Button(btn_frame, text="Cancelar", command=self.destroy).pack(side="left", padx=4)

    def _ok(self):
        date = self._date.get().strip()
        time = self._time.get().strip()
        desc = self._desc.get().strip()
        if not date or not time:
            messagebox.showerror("Erro", "Data e hora são obrigatórios.", parent=self)
            return
        try:
            datetime.strptime(date, "%d/%m/%Y")
        except ValueError:
            messagebox.showerror("Erro", "Data inválida. Use DD/MM/AAAA.", parent=self)
            return
        try:
            datetime.strptime(time, "%H:%M")
        except ValueError:
            messagebox.showerror("Erro", "Hora inválida. Use HH:MM.", parent=self)
            return
        self.result = (date, time, desc)
        self.destroy()


class FinalizeScheduleDialog(tk.Toplevel):
    def __init__(self, parent, text: str):
        super().__init__(parent)
        self.title("Finalizar Escala")
        self.geometry("600x500")
        self.confirmed = False
        self._build(text)
        self.grab_set()
        self.wait_window()

    def _build(self, text: str):
        ttk.Label(self, text="Texto gerado para a escala:").pack(anchor="w", padx=10, pady=(10, 2))

        frame = ttk.Frame(self)
        frame.pack(fill="both", expand=True, padx=10, pady=4)
        scrollbar = ttk.Scrollbar(frame, orient="vertical")
        self._text_widget = tk.Text(frame, wrap="word", yscrollcommand=scrollbar.set)
        scrollbar.config(command=self._text_widget.yview)
        scrollbar.pack(side="right", fill="y")
        self._text_widget.pack(side="left", fill="both", expand=True)
        self._text_widget.insert("1.0", text)
        self._text_widget.config(state="disabled")

        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=8)
        ttk.Button(btn_frame, text="Copiar", command=self._copy).pack(side="left", padx=6)
        ttk.Button(btn_frame, text="Confirmar e Salvar", command=self._confirm).pack(side="left", padx=6)
        ttk.Button(btn_frame, text="Fechar", command=self.destroy).pack(side="left", padx=6)

    def _copy(self):
        self._text_widget.config(state="normal")
        content = self._text_widget.get("1.0", "end-1c")
        self._text_widget.config(state="disabled")
        self.clipboard_clear()
        self.clipboard_append(content)
        messagebox.showinfo("Copiado", "Texto copiado para a área de transferência.", parent=self)

    def _confirm(self):
        self.confirmed = True
        self.destroy()


class ScheduleTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self._app = app
        self._slot_frames = {}
        self._build()

    def _build(self):
        self.columnconfigure(0, weight=2)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        # Left panel – slots
        left = ttk.Frame(self, relief="groove", borderwidth=1)
        left.grid(row=0, column=0, sticky="nsew", padx=(6, 3), pady=6)
        left.rowconfigure(1, weight=1)
        left.columnconfigure(0, weight=1)

        top_bar = ttk.Frame(left)
        top_bar.grid(row=0, column=0, sticky="ew", padx=6, pady=4)
        ttk.Label(top_bar, text="Horários da Escala", font=("", 11, "bold")).pack(side="left")
        ttk.Button(top_bar, text="+ Novo Horário", command=self._add_slot).pack(side="right")

        canvas_frame = ttk.Frame(left)
        canvas_frame.grid(row=1, column=0, sticky="nsew")
        canvas_frame.rowconfigure(0, weight=1)
        canvas_frame.columnconfigure(0, weight=1)

        self._canvas = tk.Canvas(canvas_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self._canvas.grid(row=0, column=0, sticky="nsew")

        self._slots_container = ttk.Frame(self._canvas)
        self._canvas_window = self._canvas.create_window((0, 0), window=self._slots_container, anchor="nw")
        self._slots_container.bind("<Configure>", self._on_frame_configure)
        self._canvas.bind("<Configure>", self._on_canvas_configure)
        self._canvas.bind("<MouseWheel>", self._on_mousewheel)
        self._canvas.bind("<Button-4>", self._on_mousewheel)
        self._canvas.bind("<Button-5>", self._on_mousewheel)

        # Right panel – acolyte list
        right = ttk.Frame(self, relief="groove", borderwidth=1)
        right.grid(row=0, column=1, sticky="nsew", padx=(3, 6), pady=6)
        right.rowconfigure(1, weight=1)
        right.columnconfigure(0, weight=1)

        ttk.Label(right, text="Acólitos (ordenados por escalas)", font=("", 10, "bold")).grid(
            row=0, column=0, padx=6, pady=4, sticky="w"
        )

        list_frame = ttk.Frame(right)
        list_frame.grid(row=1, column=0, sticky="nsew", padx=6, pady=2)
        list_frame.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)

        self._acolyte_listbox = tk.Listbox(list_frame, selectmode="single", font=("", 10))
        sb = ttk.Scrollbar(list_frame, orient="vertical", command=self._acolyte_listbox.yview)
        self._acolyte_listbox.configure(yscrollcommand=sb.set)
        sb.grid(row=0, column=1, sticky="ns")
        self._acolyte_listbox.grid(row=0, column=0, sticky="nsew")

        ttk.Button(right, text="Finalizar Escala", command=self._finalize).grid(
            row=2, column=0, pady=8, padx=6, sticky="ew"
        )

    def _on_frame_configure(self, _event=None):
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self._canvas.itemconfig(self._canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        if event.num == 4:
            self._canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self._canvas.yview_scroll(1, "units")
        else:
            self._canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # ── Public refresh methods ──────────────────────────────────────────────

    def refresh(self):
        self._refresh_acolyte_list()
        self._refresh_slots()

    def _refresh_acolyte_list(self):
        self._acolyte_listbox.delete(0, "end")
        sorted_acolytes = sorted(self._app.acolytes, key=lambda a: a.vezes_escalado)
        for acolyte in sorted_acolytes:
            label = f"{acolyte.name} ({acolyte.vezes_escalado})"
            if acolyte.is_suspended:
                label += " [SUSPENSO]"
            self._acolyte_listbox.insert("end", label)
        # Store sorted list for index lookup
        self._sorted_acolytes = sorted_acolytes

    def _refresh_slots(self):
        for widget in self._slots_container.winfo_children():
            widget.destroy()
        self._slot_frames = {}
        for slot in self._app.slots:
            self._build_slot_card(slot)
        self._on_frame_configure()

    def _build_slot_card(self, slot: ScheduleSlot):
        card = ttk.LabelFrame(self._slots_container, padding=6)
        card.pack(fill="x", padx=8, pady=4)

        header = ttk.Frame(card)
        header.pack(fill="x")

        date_short = slot.date[:5] if len(slot.date) >= 5 else slot.date
        weekday = _weekday_pt(slot.date)
        title = f"{weekday}, {date_short} - {slot.time}"
        ttk.Label(header, text=title, font=("", 10, "bold")).pack(side="left")
        ttk.Button(header, text="✕", width=3,
                   command=lambda s=slot: self._delete_slot(s)).pack(side="right")

        if slot.description:
            ttk.Label(card, text=slot.description, foreground="gray").pack(anchor="w")

        # Assigned acolytes
        assigned_frame = ttk.Frame(card)
        assigned_frame.pack(fill="x", pady=(4, 2))
        self._refresh_assigned(slot, assigned_frame)

        ttk.Button(card, text="Adicionar Acólito",
                   command=lambda s=slot, af=assigned_frame: self._add_acolyte_to_slot(s, af)
                   ).pack(anchor="w", pady=(2, 0))

        self._slot_frames[slot.id] = (card, assigned_frame)

    def _refresh_assigned(self, slot: ScheduleSlot, frame: ttk.Frame):
        for w in frame.winfo_children():
            w.destroy()
        acolytes_by_id = {a.id: a for a in self._app.acolytes}
        for aid in slot.acolyte_ids:
            acolyte = acolytes_by_id.get(aid)
            if not acolyte:
                continue
            row = ttk.Frame(frame)
            row.pack(anchor="w")
            ttk.Label(row, text=f"• {acolyte.name}").pack(side="left")
            ttk.Button(row, text="✕", width=3,
                       command=lambda s=slot, a_id=aid, f=frame: self._remove_acolyte(s, a_id, f)
                       ).pack(side="left", padx=2)

    # ── Actions ─────────────────────────────────────────────────────────────

    def _add_slot(self):
        dialog = NewSlotDialog(self)
        if dialog.result:
            date, time, desc = dialog.result
            slot = ScheduleSlot(date=date, time=time, description=desc)
            self._app.slots.append(slot)
            self._app.save()
            self._build_slot_card(slot)
            self._on_frame_configure()

    def _delete_slot(self, slot: ScheduleSlot):
        if not messagebox.askyesno("Confirmar", f"Excluir o horário {slot.date} - {slot.time}?"):
            return
        self._app.slots = [s for s in self._app.slots if s.id != slot.id]
        self._app.save()
        self._refresh_slots()

    def _add_acolyte_to_slot(self, slot: ScheduleSlot, assigned_frame: ttk.Frame):
        sel = self._acolyte_listbox.curselection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecione um acólito na lista.", parent=self)
            return
        acolyte = self._sorted_acolytes[sel[0]]
        if acolyte.id in slot.acolyte_ids:
            messagebox.showwarning("Aviso", f"{acolyte.name} já está neste horário.", parent=self)
            return
        slot.acolyte_ids.append(acolyte.id)
        self._app.save()
        self._refresh_assigned(slot, assigned_frame)

    def _remove_acolyte(self, slot: ScheduleSlot, acolyte_id: str, frame: ttk.Frame):
        slot.acolyte_ids = [aid for aid in slot.acolyte_ids if aid != acolyte_id]
        self._app.save()
        self._refresh_assigned(slot, frame)

    def _finalize(self):
        if not self._app.slots:
            messagebox.showinfo("Aviso", "Nenhum horário na escala.")
            return
        acolytes_by_id = {a.id: a for a in self._app.acolytes}
        text = _generate_schedule_text(self._app.slots, acolytes_by_id)
        dialog = FinalizeScheduleDialog(self, text)
        if dialog.confirmed:
            from models.models import HistoryEntry
            for slot in self._app.slots:
                for aid in slot.acolyte_ids:
                    acolyte = acolytes_by_id.get(aid)
                    if acolyte:
                        acolyte.vezes_escalado += 1
                        acolyte.history.append(HistoryEntry(
                            date=slot.date,
                            time=slot.time,
                            description=slot.description,
                            entry_type="escala",
                        ))
            self._app.slots.clear()
            self._app.save()
            self.refresh()
            messagebox.showinfo("Salvo", "Escala registrada com sucesso!")
