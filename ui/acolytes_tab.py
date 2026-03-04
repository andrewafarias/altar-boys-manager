import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from typing import Optional

from models.models import Acolyte, Absence, Suspension, BonusMovement


# ── Small dialog helpers ────────────────────────────────────────────────────

class _SimpleDialog(tk.Toplevel):
    """Generic dialog base that sets up grab and wait."""
    def __init__(self, parent, title: str):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.result = None
        self._build()
        self.grab_set()
        self.wait_window()

    def _build(self):
        raise NotImplementedError


class AbsenceDialog(_SimpleDialog):
    def __init__(self, parent):
        super().__init__(parent, "Registrar Falta")

    def _build(self):
        pad = {"padx": 8, "pady": 4}
        ttk.Label(self, text="Data (DD/MM/AAAA):").grid(row=0, column=0, sticky="w", **pad)
        self._date = ttk.Entry(self, width=16)
        self._date.grid(row=0, column=1, **pad)

        ttk.Label(self, text="Descrição:").grid(row=1, column=0, sticky="w", **pad)
        self._desc = ttk.Entry(self, width=30)
        self._desc.grid(row=1, column=1, **pad)

        btn = ttk.Frame(self)
        btn.grid(row=2, column=0, columnspan=2, pady=8)
        ttk.Button(btn, text="OK", command=self._ok).pack(side="left", padx=4)
        ttk.Button(btn, text="Cancelar", command=self.destroy).pack(side="left", padx=4)

    def _ok(self):
        date = self._date.get().strip()
        desc = self._desc.get().strip()
        if not date:
            messagebox.showerror("Erro", "A data é obrigatória.", parent=self)
            return
        try:
            datetime.strptime(date, "%d/%m/%Y")
        except ValueError:
            messagebox.showerror("Erro", "Data inválida. Use DD/MM/AAAA.", parent=self)
            return
        self.result = (date, desc)
        self.destroy()


class SuspendDialog(_SimpleDialog):
    def __init__(self, parent):
        super().__init__(parent, "Suspender Acólito")

    def _build(self):
        pad = {"padx": 8, "pady": 4}
        ttk.Label(self, text="Razão:").grid(row=0, column=0, sticky="w", **pad)
        self._reason = ttk.Entry(self, width=30)
        self._reason.grid(row=0, column=1, **pad)

        ttk.Label(self, text="Duração:").grid(row=1, column=0, sticky="w", **pad)
        self._duration = ttk.Entry(self, width=20)
        self._duration.grid(row=1, column=1, **pad)

        btn = ttk.Frame(self)
        btn.grid(row=2, column=0, columnspan=2, pady=8)
        ttk.Button(btn, text="OK", command=self._ok).pack(side="left", padx=4)
        ttk.Button(btn, text="Cancelar", command=self.destroy).pack(side="left", padx=4)

    def _ok(self):
        reason = self._reason.get().strip()
        duration = self._duration.get().strip()
        if not reason:
            messagebox.showerror("Erro", "A razão é obrigatória.", parent=self)
            return
        self.result = (reason, duration)
        self.destroy()


class BonusDialog(_SimpleDialog):
    def __init__(self, parent, title: str):
        self._title = title
        super().__init__(parent, title)

    def _build(self):
        pad = {"padx": 8, "pady": 4}
        ttk.Label(self, text="Quantidade:").grid(row=0, column=0, sticky="w", **pad)
        self._amount = ttk.Entry(self, width=10)
        self._amount.grid(row=0, column=1, **pad)

        ttk.Label(self, text="Descrição:").grid(row=1, column=0, sticky="w", **pad)
        self._desc = ttk.Entry(self, width=30)
        self._desc.grid(row=1, column=1, **pad)

        btn = ttk.Frame(self)
        btn.grid(row=2, column=0, columnspan=2, pady=8)
        ttk.Button(btn, text="OK", command=self._ok).pack(side="left", padx=4)
        ttk.Button(btn, text="Cancelar", command=self.destroy).pack(side="left", padx=4)

    def _ok(self):
        try:
            amount = int(self._amount.get().strip())
            if amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Erro", "Informe uma quantidade inteira positiva.", parent=self)
            return
        desc = self._desc.get().strip()
        self.result = (amount, desc)
        self.destroy()


class DirectBonusDialog(_SimpleDialog):
    def __init__(self, parent, current: int):
        self._current = current
        super().__init__(parent, "Editar Bônus Diretamente")

    def _build(self):
        pad = {"padx": 8, "pady": 4}
        ttk.Label(self, text=f"Valor atual: {self._current}").grid(
            row=0, column=0, columnspan=2, **pad
        )
        ttk.Label(self, text="Novo valor:").grid(row=1, column=0, sticky="w", **pad)
        self._value = ttk.Entry(self, width=10)
        self._value.insert(0, str(self._current))
        self._value.grid(row=1, column=1, **pad)

        btn = ttk.Frame(self)
        btn.grid(row=2, column=0, columnspan=2, pady=8)
        ttk.Button(btn, text="OK", command=self._ok).pack(side="left", padx=4)
        ttk.Button(btn, text="Cancelar", command=self.destroy).pack(side="left", padx=4)

    def _ok(self):
        try:
            value = int(self._value.get().strip())
        except ValueError:
            messagebox.showerror("Erro", "Informe um número inteiro.", parent=self)
            return
        self.result = value
        self.destroy()


class NameDialog(_SimpleDialog):
    def __init__(self, parent, title: str, initial: str = ""):
        self._initial = initial
        super().__init__(parent, title)

    def _build(self):
        pad = {"padx": 8, "pady": 4}
        ttk.Label(self, text="Nome:").grid(row=0, column=0, sticky="w", **pad)
        self._name = ttk.Entry(self, width=28)
        self._name.insert(0, self._initial)
        self._name.grid(row=0, column=1, **pad)

        btn = ttk.Frame(self)
        btn.grid(row=1, column=0, columnspan=2, pady=8)
        ttk.Button(btn, text="OK", command=self._ok).pack(side="left", padx=4)
        ttk.Button(btn, text="Cancelar", command=self.destroy).pack(side="left", padx=4)

    def _ok(self):
        name = self._name.get().strip()
        if not name:
            messagebox.showerror("Erro", "O nome não pode ser vazio.", parent=self)
            return
        self.result = name
        self.destroy()


# ── Main AcolytesTab ────────────────────────────────────────────────────────

class AcolytesTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self._app = app
        self._selected_acolyte: Optional[Acolyte] = None
        self._build()

    def _build(self):
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=2)
        self.rowconfigure(0, weight=1)

        # ── Left panel ──────────────────────────────────────────────────────
        left = ttk.Frame(self, relief="groove", borderwidth=1)
        left.grid(row=0, column=0, sticky="nsew", padx=(6, 3), pady=6)
        left.rowconfigure(1, weight=1)
        left.columnconfigure(0, weight=1)

        top_btn = ttk.Frame(left)
        top_btn.grid(row=0, column=0, sticky="ew", padx=4, pady=4)
        ttk.Button(top_btn, text="+ Novo Acólito", command=self._new_acolyte).pack(
            side="left", padx=2
        )
        ttk.Button(top_btn, text="Editar Nome", command=self._edit_name).pack(side="left", padx=2)
        ttk.Button(top_btn, text="Excluir", command=self._delete_acolyte).pack(side="left", padx=2)

        list_frame = ttk.Frame(left)
        list_frame.grid(row=1, column=0, sticky="nsew", padx=4, pady=2)
        list_frame.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)

        self._listbox = tk.Listbox(list_frame, selectmode="single", font=("", 10), width=28)
        sb = ttk.Scrollbar(list_frame, orient="vertical", command=self._listbox.yview)
        self._listbox.configure(yscrollcommand=sb.set)
        sb.grid(row=0, column=1, sticky="ns")
        self._listbox.grid(row=0, column=0, sticky="nsew")
        self._listbox.bind("<<ListboxSelect>>", self._on_select)

        bottom_btn = ttk.Frame(left)
        bottom_btn.grid(row=2, column=0, sticky="ew", padx=4, pady=6)
        ttk.Button(bottom_btn, text="Fechar Semestre", command=self._close_semester).pack(
            fill="x", pady=2
        )
        ttk.Button(bottom_btn, text="Gerar Relatório PDF", command=self._generate_pdf).pack(
            fill="x", pady=2
        )

        # ── Right panel ─────────────────────────────────────────────────────
        right = ttk.Frame(self, relief="groove", borderwidth=1)
        right.grid(row=0, column=1, sticky="nsew", padx=(3, 6), pady=6)
        right.rowconfigure(1, weight=1)
        right.columnconfigure(0, weight=1)

        ttk.Label(right, text="Detalhes do Acólito", font=("", 11, "bold")).grid(
            row=0, column=0, sticky="w", padx=8, pady=4
        )

        # Detail scrollable area
        canvas = tk.Canvas(right, highlightthickness=0)
        sb2 = ttk.Scrollbar(right, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb2.set)
        sb2.grid(row=1, column=1, sticky="ns")
        canvas.grid(row=1, column=0, sticky="nsew")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)

        self._detail_frame = ttk.Frame(canvas)
        self._detail_window = canvas.create_window((0, 0), window=self._detail_frame, anchor="nw")
        self._detail_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.bind(
            "<Configure>", lambda e: canvas.itemconfig(self._detail_window, width=e.width)
        )

        # Action buttons
        action_frame = ttk.LabelFrame(right, text="Ações", padding=6)
        action_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=6, pady=4)
        for i in range(3):
            action_frame.columnconfigure(i, weight=1)

        actions = [
            ("Registrar Falta", self._register_absence),
            ("Suspender", self._suspend),
            ("Levantar Suspensão", self._lift_suspension),
            ("Dar Bônus", self._give_bonus),
            ("Usar Bônus", self._use_bonus),
            ("Editar Bônus Diretamente", self._edit_bonus_direct),
        ]
        for i, (label, cmd) in enumerate(actions):
            ttk.Button(action_frame, text=label, command=cmd).grid(
                row=i // 3, column=i % 3, padx=3, pady=3, sticky="ew"
            )

    # ── Refresh ─────────────────────────────────────────────────────────────

    def refresh(self):
        sel_id = self._selected_acolyte.id if self._selected_acolyte else None
        self._listbox.delete(0, "end")
        self._sorted = sorted(self._app.acolytes, key=lambda a: a.name.lower())
        for acolyte in self._sorted:
            label = acolyte.name
            if acolyte.is_suspended:
                label += " (SUSPENSO)"
            self._listbox.insert("end", label)
        # Restore selection
        if sel_id:
            for i, a in enumerate(self._sorted):
                if a.id == sel_id:
                    self._listbox.selection_set(i)
                    self._selected_acolyte = a
                    break
            else:
                self._selected_acolyte = None
        self._render_detail()

    def _on_select(self, _event=None):
        sel = self._listbox.curselection()
        if sel:
            self._selected_acolyte = self._sorted[sel[0]]
        else:
            self._selected_acolyte = None
        self._render_detail()

    def _render_detail(self):
        for w in self._detail_frame.winfo_children():
            w.destroy()

        a = self._selected_acolyte
        if not a:
            ttk.Label(self._detail_frame, text="Selecione um acólito na lista.").pack(
                padx=10, pady=20
            )
            return

        pad = {"padx": 10, "pady": 2}

        def section(title):
            ttk.Separator(self._detail_frame, orient="horizontal").pack(fill="x", padx=8, pady=4)
            ttk.Label(self._detail_frame, text=title, font=("", 10, "bold")).pack(anchor="w", **pad)

        # Header
        suspended = " (SUSPENSO)" if a.is_suspended else ""
        ttk.Label(self._detail_frame, text=f"{a.name}{suspended}", font=("", 13, "bold")).pack(
            anchor="w", **pad
        )

        # Summary
        section("Resumo")
        ttk.Label(self._detail_frame, text=f"Vezes escalado: {a.vezes_escalado}").pack(
            anchor="w", **pad
        )
        ttk.Label(self._detail_frame, text=f"Faltas: {len(a.absences)}").pack(anchor="w", **pad)
        ttk.Label(self._detail_frame, text=f"Bônus: {a.bonus}").pack(anchor="w", **pad)
        if a.is_suspended and a.suspension_duration:
            ttk.Label(
                self._detail_frame,
                text=f"Tempo de suspensão: {a.suspension_duration}",
                foreground="red",
            ).pack(anchor="w", **pad)

        # History
        section(f"Histórico ({len(a.history)} participações)")
        if a.history:
            for h in a.history[-10:]:
                type_label = "Escala" if h.entry_type == "escala" else "Evento"
                desc = f" — {h.description}" if h.description else ""
                time_str = f" {h.time}" if h.time else ""
                ttk.Label(
                    self._detail_frame,
                    text=f"• [{type_label}] {h.date}{time_str}{desc}",
                ).pack(anchor="w", padx=14, pady=1)
            if len(a.history) > 10:
                ttk.Label(
                    self._detail_frame,
                    text=f"... e mais {len(a.history) - 10} entradas (ver PDF para detalhes)",
                    foreground="gray",
                ).pack(anchor="w", padx=14, pady=1)
        else:
            ttk.Label(self._detail_frame, text="Nenhuma participação.").pack(anchor="w", **pad)

        # Absences
        section(f"Faltas ({len(a.absences)})")
        if a.absences:
            for ab in a.absences:
                ttk.Label(
                    self._detail_frame, text=f"• {ab.date}: {ab.description or '-'}"
                ).pack(anchor="w", padx=14, pady=1)
        else:
            ttk.Label(self._detail_frame, text="Nenhuma falta.").pack(anchor="w", **pad)

        # Suspensions
        section(f"Suspensões ({len(a.suspensions)})")
        if a.suspensions:
            for s in a.suspensions:
                active_str = " [ATIVA]" if s.active else ""
                ttk.Label(
                    self._detail_frame,
                    text=f"• {s.date}{active_str}: {s.reason} (duração: {s.duration or '-'})",
                ).pack(anchor="w", padx=14, pady=1)
        else:
            ttk.Label(self._detail_frame, text="Nenhuma suspensão.").pack(anchor="w", **pad)

        # Bonus movements
        section(f"Movimentações de Bônus (saldo: {a.bonus})")
        if a.bonus_movements:
            for bm in a.bonus_movements:
                type_label = "➕ Recebido" if bm.type == "give" else "➖ Utilizado"
                ttk.Label(
                    self._detail_frame,
                    text=f"• {bm.date} {type_label} {bm.amount}: {bm.description or '-'}",
                ).pack(anchor="w", padx=14, pady=1)
        else:
            ttk.Label(self._detail_frame, text="Nenhuma movimentação.").pack(anchor="w", **pad)

    # ── Actions ─────────────────────────────────────────────────────────────

    def _require_selection(self) -> Optional[Acolyte]:
        if not self._selected_acolyte:
            messagebox.showwarning("Aviso", "Selecione um acólito primeiro.")
        return self._selected_acolyte

    def _new_acolyte(self):
        dialog = NameDialog(self, "Novo Acólito")
        if dialog.result:
            acolyte = Acolyte(name=dialog.result)
            self._app.acolytes.append(acolyte)
            self._app.save()
            self.refresh()
            self._app.on_acolytes_changed()

    def _edit_name(self):
        a = self._require_selection()
        if not a:
            return
        dialog = NameDialog(self, "Editar Nome", initial=a.name)
        if dialog.result:
            a.name = dialog.result
            self._app.save()
            self.refresh()
            self._app.on_acolytes_changed()

    def _delete_acolyte(self):
        a = self._require_selection()
        if not a:
            return
        if not messagebox.askyesno("Confirmar", f"Excluir '{a.name}'? Esta ação não pode ser desfeita."):
            return
        self._app.acolytes = [ac for ac in self._app.acolytes if ac.id != a.id]
        self._selected_acolyte = None
        self._app.save()
        self.refresh()
        self._app.on_acolytes_changed()

    def _register_absence(self):
        a = self._require_selection()
        if not a:
            return
        dialog = AbsenceDialog(self)
        if dialog.result:
            date, desc = dialog.result
            a.absences.append(Absence(date=date, description=desc))
            self._app.save()
            self._render_detail()

    def _suspend(self):
        a = self._require_selection()
        if not a:
            return
        dialog = SuspendDialog(self)
        if dialog.result:
            reason, duration = dialog.result
            today = datetime.now().strftime("%d/%m/%Y")
            a.suspensions.append(Suspension(date=today, reason=reason, duration=duration, active=True))
            a.is_suspended = True
            a.suspension_duration = duration
            self._app.save()
            self.refresh()

    def _lift_suspension(self):
        a = self._require_selection()
        if not a:
            return
        if not a.is_suspended:
            messagebox.showinfo("Aviso", f"{a.name} não está suspenso.")
            return
        for s in a.suspensions:
            if s.active:
                s.active = False
        a.is_suspended = False
        a.suspension_duration = ""
        self._app.save()
        self.refresh()

    def _give_bonus(self):
        a = self._require_selection()
        if not a:
            return
        dialog = BonusDialog(self, "Dar Bônus")
        if dialog.result:
            amount, desc = dialog.result
            today = datetime.now().strftime("%d/%m/%Y")
            a.bonus += amount
            a.bonus_movements.append(BonusMovement(date=today, type="give", amount=amount, description=desc))
            self._app.save()
            self._render_detail()

    def _use_bonus(self):
        a = self._require_selection()
        if not a:
            return
        dialog = BonusDialog(self, "Usar Bônus")
        if dialog.result:
            amount, desc = dialog.result
            if amount > a.bonus:
                messagebox.showerror(
                    "Erro", f"{a.name} só tem {a.bonus} bônus disponíveis.", parent=self
                )
                return
            today = datetime.now().strftime("%d/%m/%Y")
            a.bonus -= amount
            a.bonus_movements.append(BonusMovement(date=today, type="use", amount=amount, description=desc))
            self._app.save()
            self._render_detail()

    def _edit_bonus_direct(self):
        a = self._require_selection()
        if not a:
            return
        dialog = DirectBonusDialog(self, current=a.bonus)
        if dialog.result is not None:
            a.bonus = dialog.result
            self._app.save()
            self._render_detail()

    def _close_semester(self):
        if not messagebox.askyesno(
            "Fechar Semestre",
            "Isso irá resetar as faltas de todos os acólitos.\nDeseja também resetar os bônus?",
        ):
            return
        reset_bonus = messagebox.askyesno("Resetar Bônus?", "Resetar os bônus de todos os acólitos?")
        for a in self._app.acolytes:
            a.absences.clear()
            if reset_bonus:
                a.bonus = 0
                a.bonus_movements.clear()
        self._app.save()
        self.refresh()
        messagebox.showinfo("Concluído", "Semestre fechado com sucesso!")

    def _generate_pdf(self):
        from reports.pdf_generator import generate_pdf
        filepath = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile="relatorio_acolitos.pdf",
            title="Salvar Relatório PDF",
        )
        if not filepath:
            return
        try:
            generate_pdf(self._app.acolytes, filepath)
            messagebox.showinfo("Sucesso", f"Relatório salvo em:\n{filepath}")
        except Exception as exc:
            messagebox.showerror("Erro", f"Não foi possível gerar o PDF:\n{exc}")
