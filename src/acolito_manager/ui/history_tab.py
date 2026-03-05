"""Aba de histórico de escalas e atividades finalizadas."""

import tkinter as tk
from tkinter import ttk, messagebox

from ..models import ScheduleSlot


class HistoryTab(ttk.Frame):
    """Aba de histórico de escalas geradas e atividades finalizadas."""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self._build()

    def _build(self):
        nb = ttk.Notebook(self)
        nb.pack(fill=tk.BOTH, expand=True)

        self._sched_frame = ttk.Frame(nb)
        self._event_frame = ttk.Frame(nb)
        nb.add(self._sched_frame, text="📅 Escalas Geradas")
        nb.add(self._event_frame, text="⛪ Atividades Finalizadas")

        self._build_schedule_history()
        self._build_event_history()

    # --------------------------------------------------------------------- #
    #  Schedule History
    # --------------------------------------------------------------------- #

    def _build_schedule_history(self):
        paned = tk.PanedWindow(
            self._sched_frame, orient=tk.HORIZONTAL, sashrelief=tk.RAISED, sashwidth=5
        )
        paned.pack(fill=tk.BOTH, expand=True)

        left = ttk.Frame(paned, padding=4)
        paned.add(left, minsize=260)

        ttk.Label(left, text="Escalas Geradas", font=("TkDefaultFont", 11, "bold")).pack(pady=4)

        list_frame = ttk.Frame(left)
        list_frame.pack(fill=tk.BOTH, expand=True)
        sb = ttk.Scrollbar(list_frame)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self._sched_listbox = tk.Listbox(list_frame, yscrollcommand=sb.set)
        self._sched_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.config(command=self._sched_listbox.yview)
        self._sched_listbox.bind("<<ListboxSelect>>", self._on_sched_select)

        ttk.Button(left, text="✏️ Editar Escala", command=self._edit_schedule).pack(
            fill=tk.X, pady=2
        )
        ttk.Button(left, text="🗑️ Excluir Escala", command=self._delete_schedule).pack(
            fill=tk.X, pady=4
        )

        right = ttk.Frame(paned, padding=4)
        paned.add(right, minsize=400)

        self._sched_detail_label = ttk.Label(
            right, text="Selecione uma escala para ver os detalhes.", foreground="gray"
        )
        self._sched_detail_label.pack(pady=20)

        self._sched_detail_frame = ttk.Frame(right)

        ttk.Label(
            self._sched_detail_frame, text="Texto da Escala:", font=("TkDefaultFont", 10, "bold")
        ).pack(anchor="w")

        txt_frame = ttk.Frame(self._sched_detail_frame)
        txt_frame.pack(fill=tk.BOTH, expand=True)
        sb2 = ttk.Scrollbar(txt_frame)
        sb2.pack(side=tk.RIGHT, fill=tk.Y)
        self._sched_text = tk.Text(
            txt_frame, width=50, height=16, yscrollcommand=sb2.set,
            state=tk.DISABLED, font=("Courier", 9)
        )
        self._sched_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb2.config(command=self._sched_text.yview)

        ttk.Label(
            self._sched_detail_frame, text="Slots:", font=("TkDefaultFont", 10, "bold")
        ).pack(anchor="w", pady=(6, 2))

        slot_frame = ttk.Frame(self._sched_detail_frame)
        slot_frame.pack(fill=tk.X)
        sb3 = ttk.Scrollbar(slot_frame, orient=tk.VERTICAL)
        sb3.pack(side=tk.RIGHT, fill=tk.Y)
        self._sched_tree = ttk.Treeview(
            slot_frame,
            columns=("Data", "Dia", "Hora", "Descrição", "Acólitos"),
            show="headings",
            height=6,
            yscrollcommand=sb3.set,
        )
        sb3.config(command=self._sched_tree.yview)
        for col, w in [("Data", 70), ("Dia", 100), ("Hora", 60), ("Descrição", 140), ("Acólitos", 180)]:
            self._sched_tree.heading(col, text=col)
            self._sched_tree.column(col, width=w, minwidth=40)
        self._sched_tree.pack(fill=tk.X, expand=False)

    # --------------------------------------------------------------------- #
    #  Event History
    # --------------------------------------------------------------------- #

    def _build_event_history(self):
        paned = tk.PanedWindow(
            self._event_frame, orient=tk.HORIZONTAL, sashrelief=tk.RAISED, sashwidth=5
        )
        paned.pack(fill=tk.BOTH, expand=True)

        left = ttk.Frame(paned, padding=4)
        paned.add(left, minsize=260)

        ttk.Label(
            left, text="Atividades Finalizadas", font=("TkDefaultFont", 11, "bold")
        ).pack(pady=4)

        list_frame = ttk.Frame(left)
        list_frame.pack(fill=tk.BOTH, expand=True)
        sb = ttk.Scrollbar(list_frame)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self._ev_listbox = tk.Listbox(list_frame, yscrollcommand=sb.set)
        self._ev_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.config(command=self._ev_listbox.yview)
        self._ev_listbox.bind("<<ListboxSelect>>", self._on_ev_select)

        ttk.Button(
            left, text="🗑️ Excluir Atividade", command=self._delete_event_batch
        ).pack(fill=tk.X, pady=4)

        right = ttk.Frame(paned, padding=4)
        paned.add(right, minsize=400)

        self._ev_detail_label = ttk.Label(
            right, text="Selecione um lote de atividades para ver os detalhes.", foreground="gray"
        )
        self._ev_detail_label.pack(pady=20)

        self._ev_detail_frame = ttk.Frame(right)
        ttk.Label(
            self._ev_detail_frame, text="Atividades:", font=("TkDefaultFont", 10, "bold")
        ).pack(anchor="w")

        ev_frame = ttk.Frame(self._ev_detail_frame)
        ev_frame.pack(fill=tk.BOTH, expand=True)
        sb2 = ttk.Scrollbar(ev_frame, orient=tk.VERTICAL)
        sb2.pack(side=tk.RIGHT, fill=tk.Y)
        self._ev_tree = ttk.Treeview(
            ev_frame,
            columns=("Nome", "Data", "Hora", "Participantes"),
            show="headings",
            yscrollcommand=sb2.set,
        )
        sb2.config(command=self._ev_tree.yview)
        for col, w in [("Nome", 160), ("Data", 70), ("Hora", 60), ("Participantes", 200)]:
            self._ev_tree.heading(col, text=col)
            self._ev_tree.column(col, width=w, minwidth=40)
        self._ev_tree.pack(fill=tk.BOTH, expand=True)

        # Buttons for event management
        ev_btn_frame = ttk.Frame(self._ev_detail_frame)
        ev_btn_frame.pack(fill=tk.X, pady=4)
        ttk.Button(ev_btn_frame, text="🗑️ Excluir Atividade Selecionada", command=self._delete_event_entry).pack(side=tk.LEFT, padx=2)

    # --------------------------------------------------------------------- #
    #  Refresh
    # --------------------------------------------------------------------- #

    def refresh(self):
        """Atualiza ambas as listas."""
        self._refresh_sched_list()
        self._refresh_ev_list()

    def _refresh_sched_list(self):
        self._sched_listbox.delete(0, tk.END)
        for gs in self.app.generated_schedules:
            slots_count = len(gs.slots)
            self._sched_listbox.insert(
                tk.END, f"{gs.generated_at} ({slots_count} horário(s))"
            )

    def _refresh_ev_list(self):
        self._ev_listbox.delete(0, tk.END)
        for fb in self.app.finalized_event_batches:
            count = len(fb.entries)
            self._ev_listbox.insert(tk.END, f"{fb.finalized_at} ({count} atividade(s))")

    # --------------------------------------------------------------------- #
    #  Selection Handlers
    # --------------------------------------------------------------------- #

    def _on_sched_select(self, event=None):
        sel = self._sched_listbox.curselection()
        if not sel:
            self._sched_detail_label.pack(pady=20)
            self._sched_detail_frame.pack_forget()
            return
        idx = sel[0]
        if idx >= len(self.app.generated_schedules):
            return
        gs = self.app.generated_schedules[idx]
        self._sched_detail_label.pack_forget()
        self._sched_detail_frame.pack(fill=tk.BOTH, expand=True)

        self._sched_text.config(state=tk.NORMAL)
        self._sched_text.delete("1.0", tk.END)
        self._sched_text.insert(tk.END, gs.schedule_text)
        self._sched_text.config(state=tk.DISABLED)

        self._sched_tree.delete(*self._sched_tree.get_children())
        for slot in gs.slots:
            names = []
            for aid in slot.acolyte_ids:
                ac = self.app.find_acolyte(aid)
                if ac:
                    names.append(ac.name)
            self._sched_tree.insert(
                "", tk.END,
                values=(slot.date, slot.day, slot.time, slot.description or "-", ", ".join(names) or "-")
            )

    def _on_ev_select(self, event=None):
        sel = self._ev_listbox.curselection()
        if not sel:
            self._ev_detail_label.pack(pady=20)
            self._ev_detail_frame.pack_forget()
            return
        idx = sel[0]
        if idx >= len(self.app.finalized_event_batches):
            return
        fb = self.app.finalized_event_batches[idx]
        self._ev_detail_label.pack_forget()
        self._ev_detail_frame.pack(fill=tk.BOTH, expand=True)

        self._ev_tree.delete(*self._ev_tree.get_children())
        for entry in fb.entries:
            names = []
            for aid in entry.participating_acolyte_ids:
                ac = self.app.find_acolyte(aid)
                if ac:
                    names.append(ac.name)
            self._ev_tree.insert(
                "", tk.END,
                values=(entry.name, entry.date, entry.time or "-", ", ".join(names) or "-")
            )

    # --------------------------------------------------------------------- #
    #  Edit / Delete Schedules
    # --------------------------------------------------------------------- #

    def _edit_schedule(self):
        """Load a generated schedule back into the schedule tab for editing."""
        sel = self._sched_listbox.curselection()
        if not sel:
            messagebox.showinfo("Aviso", "Selecione uma escala para editar.")
            return
        idx = sel[0]
        if idx >= len(self.app.generated_schedules):
            return
        gs = self.app.generated_schedules[idx]
        if not messagebox.askyesno(
            "Editar Escala",
            f"Deseja carregar a escala de {gs.generated_at} para edição?\n\n"
            "As contagens dos acólitos serão revertidas e a escala será movida para a aba de criação.\n"
            "Horários existentes na aba de criação serão mantidos.",
        ):
            return

        # Reverse acolyte changes
        slot_ids = {s.slot_id for s in gs.slots}
        for slot in gs.slots:
            for aid in slot.acolyte_ids:
                ac = self.app.find_acolyte(aid)
                if ac:
                    if ac.times_scheduled > 0:
                        ac.times_scheduled -= 1
                    ac.schedule_history = [
                        e for e in ac.schedule_history if e.schedule_id not in slot_ids
                    ]

        # Create schedule slots from the snapshot
        for snap in gs.slots:
            slot = ScheduleSlot(
                id=snap.slot_id,
                date=snap.date,
                day=snap.day,
                time=snap.time,
                description=snap.description,
                acolyte_ids=list(snap.acolyte_ids),
            )
            self.app.schedule_slots.append(slot)

        # Remove from generated schedules
        self.app.generated_schedules.pop(idx)
        self.app.save()

        # Refresh UI
        self._refresh_sched_list()
        self._sched_detail_label.pack(pady=20)
        self._sched_detail_frame.pack_forget()
        self.app.schedule_tab.load_slots_from_data()
        self.app.schedule_tab.refresh_acolyte_list()
        self.app.acolytes_tab.refresh_list()

        # Switch to schedule tab
        self.app.notebook.select(self.app.schedule_tab)
        messagebox.showinfo("Concluído", "Escala carregada para edição na aba 'Criar Escala'.")

    def _delete_schedule(self):
        sel = self._sched_listbox.curselection()
        if not sel:
            messagebox.showinfo("Aviso", "Selecione uma escala para excluir.")
            return
        idx = sel[0]
        if idx >= len(self.app.generated_schedules):
            return
        gs = self.app.generated_schedules[idx]
        if not messagebox.askyesno(
            "Confirmar",
            f"Excluir a escala de {gs.generated_at}?\n\n"
            "Isso reverterá as contagens de escalas dos acólitos envolvidos.",
        ):
            return
        # Reverse acolyte changes
        slot_ids = {s.slot_id for s in gs.slots}
        for slot in gs.slots:
            for aid in slot.acolyte_ids:
                ac = self.app.find_acolyte(aid)
                if ac:
                    if ac.times_scheduled > 0:
                        ac.times_scheduled -= 1
                    ac.schedule_history = [
                        e for e in ac.schedule_history if e.schedule_id not in slot_ids
                    ]
        self.app.generated_schedules.pop(idx)
        self.app.save()
        self._refresh_sched_list()
        self._sched_detail_label.pack(pady=20)
        self._sched_detail_frame.pack_forget()
        self.app.acolytes_tab.refresh_list()
        self.app.schedule_tab.refresh_acolyte_list()
        messagebox.showinfo("Concluído", "Escala excluída e contagens revertidas.")

    # --------------------------------------------------------------------- #
    #  Delete Event Batches
    # --------------------------------------------------------------------- #

    def _delete_event_batch(self):
        sel = self._ev_listbox.curselection()
        if not sel:
            messagebox.showinfo("Aviso", "Selecione um lote de atividades para excluir.")
            return
        idx = sel[0]
        if idx >= len(self.app.finalized_event_batches):
            return
        fb = self.app.finalized_event_batches[idx]
        if not messagebox.askyesno(
            "Confirmar",
            f"Excluir o lote de atividades de {fb.finalized_at}?\n\n"
            "Isso removerá os registros de atividades dos acólitos.",
        ):
            return
        event_ids = {e.event_id for e in fb.entries}
        for ac in self.app.acolytes:
            ac.event_history = [e for e in ac.event_history if e.event_id not in event_ids]
        self.app.finalized_event_batches.pop(idx)
        self.app.save()
        self._refresh_ev_list()
        self._ev_detail_label.pack(pady=20)
        self._ev_detail_frame.pack_forget()
        self.app.acolytes_tab.refresh_list()
        messagebox.showinfo("Concluído", "Lote de atividades excluído.")

    def _delete_event_entry(self):
        """Delete a single event entry from the selected batch."""
        # Get selected batch
        batch_sel = self._ev_listbox.curselection()
        if not batch_sel:
            messagebox.showinfo("Aviso", "Selecione um lote de atividades.")
            return
        batch_idx = batch_sel[0]
        if batch_idx >= len(self.app.finalized_event_batches):
            return
        fb = self.app.finalized_event_batches[batch_idx]

        # Get selected event entry in the tree
        tree_sel = self._ev_tree.selection()
        if not tree_sel:
            messagebox.showinfo("Aviso", "Selecione uma atividade para excluir.")
            return
        entry_idx = self._ev_tree.index(tree_sel[0])
        if entry_idx >= len(fb.entries):
            return

        entry = fb.entries[entry_idx]
        if not messagebox.askyesno(
            "Confirmar",
            f"Excluir a atividade '{entry.name}' de {entry.date}?\n\n"
            "Isso removerá o registro de atividade dos {0} acólito(s) que participaram.".format(len(entry.participating_acolyte_ids)),
        ):
            return

        # Remove from acolytes' event history
        for ac in self.app.acolytes:
            ac.event_history = [e for e in ac.event_history if e.event_id != entry.event_id]

        # Remove from batch
        fb.entries.pop(entry_idx)

        self.app.save()
        self._on_ev_select()  # Refresh the tree view
        self.app.acolytes_tab.refresh_list()
        messagebox.showinfo("Concluído", "Atividade excluída do lote.")
