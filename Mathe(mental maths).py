#!/usr/bin/env python3
# Mathe-Kopfrechentrainer — vollständiges Programm
# Fenster wird zuverlässig zentriert. GUI-Inhalt bleibt mittig und skaliert.

import random
import operator
import time
import math
import sys

try:
    import tkinter as tk
    from tkinter import ttk, messagebox
    import tkinter.font as tkfont
except Exception:
    tk = None

# --- Konfiguration ---
OPS = {
    '+': {'func': operator.add, 'low': -10000, 'high': 99999, 'weight': 1},
    '-': {'func': operator.sub, 'low': -10000, 'high': 99999, 'weight': 1},
    '*': {'func': operator.mul, 'low': -100, 'high': 100, 'weight': 2},
    '/': {'func': operator.truediv, 'low': -100, 'high': 100, 'weight': 3}
}
PENALTY_RATIO = 0.25
TOL_DIV = 1e-2
GRADE_THRESHOLDS = [(90,"1.0"), (80,"2.0"), (65,"3.0"), (50,"4.0"), (30,"5.0"), (0,"6.0")]

# --- Utility: zuverlässiges Zentrieren des Fensters ---
def center_window(root, width=None, height=None, _tries=0):
    """
    Zentriert `root`. Falls width/height gegeben werden, setzt diese Größe.
    Versucht bis zu 30x, falls Tk noch keine endgültige Größe liefert.
    """
    if _tries > 30:
        return
    if width and height:
        try:
            root.geometry(f"{int(width)}x{int(height)}")
        except Exception:
            pass
    root.update_idletasks()
    w = root.winfo_width()
    h = root.winfo_height()
    # Manche Plattformen liefern noch 1 oder 0 unmittelbar nach Erzeugung
    if w <= 1 or h <= 1:
        root.after(40, lambda: center_window(root, width, height, _tries + 1))
        return
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    x = (sw - w) // 2
    y = (sh - h) // 2
    root.geometry(f"{w}x{h}+{x}+{y}")
    root.update_idletasks()

# --- Gemeinsame Logik ---
def generate_task_for_op(op_symbol):
    cfg = OPS[op_symbol]
    low, high = cfg['low'], cfg['high']
    a = random.randint(low, high)
    b = random.randint(low, high)
    if op_symbol == '/':
        while b == 0:
            b = random.randint(low, high)
    return a, b, cfg['func'], cfg['weight']

def evaluate_answer(a, b, op_symbol, user_input):
    func = OPS[op_symbol]['func']; weight = OPS[op_symbol]['weight']; possible = weight
    try:
        user_val = float(str(user_input).replace(',', '.'))
    except Exception:
        return False, -PENALTY_RATIO * weight, possible
    try:
        true_val = func(a, b)
    except Exception:
        return False, -PENALTY_RATIO * weight, possible
    tol = TOL_DIV if op_symbol == '/' else 1e-9
    if math.isfinite(true_val) and abs(user_val - true_val) <= tol:
        return True, weight, possible
    return False, -PENALTY_RATIO * weight, possible

def calculate_grade(points, possible):
    if possible <= 0:
        return 0.0, "6.0"
    pct = max(0.0, min(100.0, (points / possible) * 100.0))
    for thresh, grade in GRADE_THRESHOLDS:
        if pct >= thresh:
            return pct, grade
    return pct, "6.0"

def format_result_for_display(func, a, b, op_symbol):
    try:
        r = func(a, b)
        if op_symbol == '/':
            return f"{r:.2f}"
        if float(r).is_integer():
            return str(int(r))
        return str(r)
    except Exception:
        return "Fehler"

# --- Shell-Modus ---
def shell_menu():
    while True:
        print("\nMathe-Kopfrechentrainer — Shell-Modus (Privat)")
        print("Wähle Operatoren (z.B. + - * /). 'q' zum Beenden.")
        ops_raw = input("Operatoren -> ").strip()
        if ops_raw.lower() == 'q':
            return
        selected_ops = [op for op in ops_raw.split() if op in OPS]
        if not selected_ops:
            print("Keine gültigen Operatoren gewählt."); continue
        mode = input("Modus ('anzahl' oder 'zeit') -> ").strip().lower()
        if mode not in ('anzahl','zeit'): print("Ungültiger Modus."); continue
        val_raw = input(("Anzahl Aufgaben -> " if mode=='anzahl' else "Dauer in Minuten -> ")).strip()
        try:
            value = int(val_raw); 
            if value <= 0: raise ValueError
        except ValueError:
            print("Ungültige Zahl."); continue
        shell_session(selected_ops, mode, value)
        again = input("Nochmal? (j/n) -> ").strip().lower()
        if again != 'j': break

def shell_session(selected_ops, mode, value):
    total_tasks = 0; points = 0.0; possible = 0.0; start = time.time()
    time_limit = value * 60 if mode == 'zeit' else None
    print("\nSession startet. Tippe 'q' zum Abbrechen.\n")
    while True:
        if mode == 'anzahl' and total_tasks >= value: break
        if mode == 'zeit' and time.time() - start >= time_limit: break
        op_symbol = random.choice(selected_ops)
        a, b, func, weight = generate_task_for_op(op_symbol)
        ans = input(f"{a} {op_symbol} {b} = ")
        if ans.strip().lower() == 'q': break
        is_corr, earned, poss = evaluate_answer(a, b, op_symbol, ans)
        points += earned; possible += poss; total_tasks += 1
        if is_corr: print("Richtig.")
        else: print(f"Falsch. Richtige Antwort: {format_result_for_display(func,a,b,op_symbol)}")
        pct,_ = calculate_grade(points, possible)
        print(f"Punkte: {points:.2f} / {possible:.2f}  ({pct:.1f}%)\n")
    elapsed = time.time() - start; pct, grade = calculate_grade(points, possible)
    print("\n--- Auswertung ---")
    print(f"Punkte: {points:.2f} / {possible:.2f}")
    print(f"Prozent: {pct:.1f}%    Note: {grade}")
    print(f"Dauer: {int(elapsed//60)}m {int(elapsed%60)}s")
    input("\nDrücke Enter zum Zurückkehren...")

# --- GUI-Modus (zentriert & responsiv) ---
if tk is not None:
    class TrainerGUI:
        def __init__(self, root):
            self.root = root
            root.title("Mathe-Kopfrechentrainer — GUI (responsiv)")
            self.selected_ops = {op: tk.BooleanVar(value=True) for op in OPS}
            self.mode = tk.StringVar(value='anzahl')
            self.value = tk.IntVar(value=10)
            self.fonts = {
                'heading': tkfont.Font(family="Helvetica", size=18, weight="bold"),
                'normal' : tkfont.Font(family="Helvetica", size=12),
                'large'  : tkfont.Font(family="Helvetica", size=22, weight="bold"),
                'small'  : tkfont.Font(family="Helvetica", size=10)
            }
            self.session_running = False
            self.points = 0.0; self.possible = 0.0; self.total_tasks = 0
            self.current_task = None; self.time_limit = 0; self.start_time = None
            self.fullscreen = False
            self._resize_after_id = None
            root.bind('<F11>', lambda e: self.toggle_fullscreen())
            root.bind('<Escape>', lambda e: self.exit_fullscreen())
            root.bind('<Configure>', self._on_configure_debounced)
            self.build_main_menu()
            # initial scale
            self.on_resize()

        def _on_configure_debounced(self, event):
            if self._resize_after_id:
                try: self.root.after_cancel(self._resize_after_id)
                except Exception: pass
            self._resize_after_id = self.root.after(80, self.on_resize)

        def on_resize(self):
            w = max(320, self.root.winfo_width()); h = max(240, self.root.winfo_height())
            scale_w = w / 900.0; scale_h = h / 650.0
            scale = min(scale_w, scale_h); scale = max(0.7, min(scale, 3.5))
            self.fonts['heading'].configure(size=max(12, int(20 * scale)))
            self.fonts['normal'].configure(size=max(9, int(12 * scale)))
            self.fonts['large'].configure(size=max(14, int(28 * scale)))
            self.fonts['small'].configure(size=max(8, int(10 * scale)))
            self._apply_fonts_to_widgets()

        def toggle_fullscreen(self):
            self.fullscreen = not self.fullscreen
            self.root.attributes('-fullscreen', self.fullscreen)

        def exit_fullscreen(self):
            self.fullscreen = False
            self.root.attributes('-fullscreen', False)

        def _apply_fonts_to_widgets(self):
            try:
                if hasattr(self, 'main_title'): self.main_title.configure(font=self.fonts['heading'])
                if hasattr(self, 'ops_frame'):
                    for child in self.ops_frame.winfo_children():
                        try: child.configure(font=self.fonts['normal'])
                        except Exception: pass
                if hasattr(self, 'spin_value'):
                    try: self.spin_value.configure(font=self.fonts['normal'])
                    except Exception: pass
                if hasattr(self, 'question_label'): self.question_label.configure(font=self.fonts['large'])
                if hasattr(self, 'answer_entry'):
                    try: self.answer_entry.configure(font=self.fonts['normal'])
                    except Exception: pass
                if hasattr(self, 'score_label'): self.score_label.configure(font=self.fonts['normal'])
                if hasattr(self, 'timer_label'): self.timer_label.configure(font=self.fonts['small'])
                if hasattr(self, 'feedback_label'): self.feedback_label.configure(font=self.fonts['normal'])
                if hasattr(self, 'session_buttons'):
                    for btn in self.session_buttons:
                        try: btn.configure(font=self.fonts['normal'])
                        except Exception: pass
            except Exception:
                pass

        # zentriertes Hauptmenü mit place(relx=0.5,rely=0.5,anchor='center')
        def build_main_menu(self):
            for w in self.root.winfo_children(): w.destroy()
            outer = ttk.Frame(self.root); outer.pack(fill='both', expand=True)
            frm = ttk.Frame(outer, padding=12)
            frm.place(relx=0.5, rely=0.5, anchor='center')
            self.main_title = ttk.Label(frm, text="Mathe-Kopfrechentrainer — GUI", anchor='center')
            self.main_title.grid(row=0, column=0, columnspan=4, pady=(0,12))
            self.main_title.configure(font=self.fonts['heading'])
            ttk.Label(frm, text="Operatoren:").grid(row=1, column=0, sticky='w')
            self.ops_frame = ttk.Frame(frm); self.ops_frame.grid(row=2, column=0, columnspan=4, sticky='')
            for i, op in enumerate(self.selected_ops):
                cb = ttk.Checkbutton(self.ops_frame, text=op, variable=self.selected_ops[op])
                cb.grid(row=0, column=i, padx=6, pady=6)
            ttk.Label(frm, text="Modus:").grid(row=3, column=0, sticky='w', pady=(10,0))
            r1 = ttk.Radiobutton(frm, text="Anzahl Aufgaben", variable=self.mode, value='anzahl')
            r2 = ttk.Radiobutton(frm, text="Zeit (Minuten)", variable=self.mode, value='zeit')
            r1.grid(row=4, column=0, sticky='w'); r2.grid(row=4, column=1, sticky='w')
            ttk.Label(frm, text="Wert (Anzahl oder Minuten):").grid(row=5, column=0, sticky='w', pady=(10,0))
            self.spin_value = ttk.Spinbox(frm, from_=1, to=10000, textvariable=self.value, width=8)
            self.spin_value.grid(row=6, column=0, sticky='w')
            start_btn = ttk.Button(frm, text="Start", command=self.start_session_gui)
            start_btn.grid(row=7, column=0, pady=12)
            quit_btn = ttk.Button(frm, text="Beenden", command=self.root.destroy)
            quit_btn.grid(row=7, column=1, pady=12)
            self.session_buttons = [start_btn, quit_btn]
            self._apply_fonts_to_widgets()

        def start_session_gui(self):
            ops = [op for op,var in self.selected_ops.items() if var.get()]
            if not ops:
                messagebox.showwarning("Fehler","Keine Operatoren gewählt."); return
            self.ops = ops
            self.mode_val = self.mode.get(); self.value_val = int(self.value.get())
            self.points = 0.0; self.possible = 0.0; self.total_tasks = 0
            self.session_running = True; self.start_time = time.time()
            self.time_limit = self.value_val * 60 if self.mode_val == 'zeit' else None
            for w in self.root.winfo_children(): w.destroy()
            self.build_session_frame()
            self.next_task_gui()
            if self.mode_val == 'zeit': self.update_timer_gui()

        def build_session_frame(self):
            for w in self.root.winfo_children(): w.destroy()
            outer = ttk.Frame(self.root); outer.pack(fill='both', expand=True)
            self.frame = ttk.Frame(outer, padding=12); self.frame.place(relx=0.5, rely=0.5, anchor='center')
            self.score_label = ttk.Label(self.frame, text="Punkte: 0 / 0"); self.score_label.grid(row=0, column=0, sticky='w')
            self.timer_label = ttk.Label(self.frame, text=""); self.timer_label.grid(row=0, column=1, sticky='e')
            self.question_var = tk.StringVar(value=""); self.question_label = ttk.Label(self.frame, textvariable=self.question_var)
            self.question_label.grid(row=1, column=0, columnspan=2, pady=12)
            self.answer_var = tk.StringVar(); self.answer_entry = ttk.Entry(self.frame, textvariable=self.answer_var)
            self.answer_entry.grid(row=2, column=0, sticky='we'); self.answer_entry.bind("<Return>", lambda e: self.submit_answer_gui())
            submit_btn = ttk.Button(self.frame, text="Antwort prüfen", command=self.submit_answer_gui); submit_btn.grid(row=2, column=1, padx=6)
            self.feedback_label = ttk.Label(self.frame, text=""); self.feedback_label.grid(row=3, column=0, columnspan=2, pady=8)
            self.end_btn = ttk.Button(self.frame, text="Abbrechen (zurück)", command=self.stop_and_return); self.end_btn.grid(row=4, column=0, pady=8)
            self.session_buttons = [submit_btn, self.end_btn]
            self.frame.columnconfigure(0, weight=1)
            self._apply_fonts_to_widgets()
            try: self.answer_entry.focus_set()
            except Exception: pass

        def next_task_gui(self):
            if self.mode_val == 'anzahl' and self.total_tasks >= self.value_val:
                self.finish_session_gui(); return
            if self.mode_val == 'zeit' and (time.time() - self.start_time) >= self.time_limit:
                self.finish_session_gui(); return
            op = random.choice(self.ops)
            a, b, func, weight = generate_task_for_op(op)
            self.current_task = (a, b, op, func, weight)
            self.question_var.set(f"{a} {op} {b} = ")
            self.answer_var.set(""); self.feedback_label.config(text=""); self.update_progress_gui()
            try: self.answer_entry.focus_set()
            except Exception: pass

        def submit_answer_gui(self):
            if not self.current_task: return
            a, b, op, func, weight = self.current_task
            user_input = self.answer_var.get()
            is_corr, earned, poss = evaluate_answer(a, b, op, user_input)
            self.points += earned; self.possible += poss; self.total_tasks += 1
            if is_corr: self.feedback_label.config(text="Richtig.", foreground="green")
            else:
                correct = format_result_for_display(func, a, b, op)
                self.feedback_label.config(text=f"Falsch. richtig: {correct}", foreground="red")
            self.update_progress_gui()
            self.root.after(600, self.next_task_gui)

        def update_progress_gui(self):
            pct, _ = calculate_grade(self.points, self.possible)
            self.score_label.config(text=f"Punkte: {self.points:.2f} / {self.possible:.2f}  ({pct:.1f}%)")
            if self.mode_val == 'zeit':
                rem = max(0, int(self.time_limit - (time.time() - self.start_time)))
                self.timer_label.config(text=f"Verbleibende Zeit: {rem//60:02d}:{rem%60:02d}")
            else:
                self.timer_label.config(text=f"Aufgaben: {self.total_tasks} / {self.value_val}")

        def update_timer_gui(self):
            if not self.session_running: return
            if self.mode_val != 'zeit': return
            if (time.time() - self.start_time) >= self.time_limit:
                self.finish_session_gui(); return
            self.update_progress_gui(); self.root.after(500, self.update_timer_gui)

        def finish_session_gui(self):
            self.session_running = False
            pct, grade = calculate_grade(self.points, self.possible)
            res = tk.Toplevel(self.root); res.title("Auswertung")
            frm = ttk.Frame(res, padding=12); frm.pack(fill='both', expand=True)
            ttk.Label(frm, text="--- Auswertung ---", font=self.fonts['heading']).grid(row=0, column=0, columnspan=2)
            ttk.Label(frm, text=f"Punkte: {self.points:.2f} / {self.possible:.2f}").grid(row=1, column=0, sticky='w')
            ttk.Label(frm, text=f"Prozent: {pct:.1f}%").grid(row=2, column=0, sticky='w')
            ttk.Label(frm, text=f"Note: {grade}").grid(row=3, column=0, sticky='w')
            ttk.Label(frm, text=f"Bearbeitete Aufgaben: {self.total_tasks}").grid(row=4, column=0, sticky='w')
            ttk.Button(frm, text="Zum Hauptmenü", command=lambda:(res.destroy(), self.build_main_menu())).grid(row=5, column=0, pady=8)
            ttk.Button(frm, text="Beenden", command=self.root.destroy).grid(row=5, column=1, pady=8)

        def stop_and_return(self):
            if messagebox.askyesno("Abbrechen","Session abbrechen und zum Hauptmenü zurück?"):
                self.session_running = False; self.build_main_menu()

# --- Startpunkt ---
def main():
    random.seed()
    while True:
        print("Mathe-Kopfrechentrainer — Wahlmodus")
        print("1) Shell (Terminal)")
        if tk is not None:
            print("2) GUI (separates Fenster, benötigt Tkinter)")
        print("q) Beenden")
        choice = input("Auswahl -> ").strip().lower()
        if choice == '1':
            shell_menu()
        elif choice == '2' and tk is not None:
            root = tk.Tk()
            # optionale Startgröße, erleichtert Layout; passt sich später an
            root.geometry("900x650")
            app = TrainerGUI(root)
            # zentrieren nach Aufbau; die Funktion versucht solange bis Größe bekannt ist
            center_window(root, 900, 650)
            root.mainloop()
        elif choice == 'q':
            print("Beende Programm.")
            return
        else:
            print("Ungültige Auswahl.")

if __name__ == "__main__":
    main()
