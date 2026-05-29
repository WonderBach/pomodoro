import tkinter as tk
import subprocess
import math

WORK_MINUTES = 25
BREAK_MINUTES = 5
WORK_SECONDS = WORK_MINUTES * 60
BREAK_SECONDS = BREAK_MINUTES * 60

# ---- refined dark palette ----
BG = "#161412"
SURFACE = "#1f1c18"
SURFACE_LIGHT = "#282420"
TEXT = "#e6ddd2"
TEXT_DIM = "#6b645c"
WORK_ACCENT = "#c9963e"
WORK_HOVER = "#d4a54f"
WORK_PRESS = "#b88730"
BREAK_ACCENT = "#6b9b8a"
BREAK_HOVER = "#7aaf9e"
BREAK_PRESS = "#5a8a78"
RING_TRACK = "#2a2520"
WHITE = "#f0ebe3"

FONT_TIMER = ("Helvetica Neue", 50, "bold")
FONT_PHASE = ("Helvetica Neue", 12, "bold")
FONT_BTN = ("Helvetica Neue", 13)
FONT_SMALL = ("Helvetica Neue", 11)


def notify(title, message):
    script = f'display notification "{message}" with title "{title}" sound name "Glass"'
    subprocess.run(["osascript", "-e", script], capture_output=True)


class PomodoroTimer(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Pomodoro")
        self.resizable(False, False)
        self.configure(bg=BG)

        self.work_seconds = WORK_SECONDS
        self.break_seconds = BREAK_SECONDS
        self.remaining = self.work_seconds
        self.phase = "work"
        self.state = "idle"
        self.after_id = None
        self.sessions = 0

        self._pulse_phase = 0
        self._pulse_id = None

        self._build_ui()
        self._center_window(340, 520)
        self.update_idletasks()
        self.lift()
        self.focus_force()

    # ---- helpers ----
    def _center_window(self, w, h):
        ws = self.winfo_screenwidth()
        hs = self.winfo_screenheight()
        x = (ws - w) // 2
        y = (hs - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _accent(self):
        return WORK_ACCENT if self.phase == "work" else BREAK_ACCENT

    def _accent_hover(self):
        return WORK_HOVER if self.phase == "work" else BREAK_HOVER

    def _accent_press(self):
        return WORK_PRESS if self.phase == "work" else BREAK_PRESS

    def _format_time(self, seconds):
        m = seconds // 60
        s = seconds % 60
        return f"{m:02d}:{s:02d}"

    # ---- UI construction ----
    def _build_ui(self):
        container = tk.Frame(self, bg=BG, padx=30, pady=24)
        container.pack(fill="both", expand=True)

        # phase label
        self.phase_label = tk.Label(
            container, text="FOCUS",
            font=FONT_PHASE, fg=WORK_ACCENT, bg=BG,
            anchor="center"
        )
        self.phase_label.pack(pady=(6, 28))

        # timer canvas
        self.canvas = tk.Canvas(
            container, width=270, height=270, bg=BG,
            highlightthickness=0, bd=0
        )
        self.canvas.pack()

        self._draw_ring(1.0)

        # timer text (overlay on canvas center)
        self.timer_text = self.canvas.create_text(
            135, 135, text=self._format_time(self.remaining),
            font=FONT_TIMER, fill=TEXT, anchor="center"
        )

        # button bar — use a Canvas for rounded buttons
        btn_bar = tk.Frame(container, bg=BG)
        btn_bar.pack(pady=(28, 14))

        self._btn_data = {}
        self._build_rounded_btn(btn_bar, "Reset", self.reset, secondary=True)
        self._build_rounded_btn(btn_bar, "Start", self.start, secondary=False)
        self._build_rounded_btn(btn_bar, "Pause", self.pause, secondary=True)

        # session counter
        self.session_label = tk.Label(
            container,
            text=f"session  {self.sessions}",
            font=FONT_SMALL, fg=TEXT_DIM, bg=BG
        )
        self.session_label.pack(pady=(8, 2))

        # always-on-top toggle
        self.top_var = tk.BooleanVar(value=False)
        top_frame = tk.Frame(container, bg=BG)
        top_frame.pack(pady=(14, 4))
        cb = tk.Checkbutton(
            top_frame, text="Always on top", variable=self.top_var,
            font=FONT_SMALL, bg=BG, fg=TEXT_DIM,
            activebackground=BG, activeforeground=TEXT,
            selectcolor=SURFACE_LIGHT,
            cursor="hand2", command=self._toggle_top,
            bd=0, highlightthickness=0
        )
        cb.pack()

    def _build_rounded_btn(self, parent, text, command, secondary=False):
        w, h = 80, 36
        r = 18
        c = tk.Canvas(
            parent, width=w, height=h, bg=BG,
            highlightthickness=0, bd=0, cursor="hand2"
        )
        c.pack(side="left", padx=6)

        fill = SURFACE_LIGHT if secondary else self._accent()
        text_fill = TEXT_DIM if secondary else BG

        rect = self._round_rect(c, 2, 2, w - 2, h - 2, r, fill=fill, outline="")
        label = c.create_text(w // 2, h // 2, text=text, font=FONT_BTN, fill=text_fill, anchor="center")

        data = {
            "canvas": c, "rect": rect, "label": label,
            "command": command, "secondary": secondary,
            "w": w, "h": h, "r": r,
            "fill": fill, "text_fill": text_fill,
        }
        self._btn_data[text] = data

        for tag in (rect, label):
            c.tag_bind(tag, "<Button-1>", lambda e, cmd=command: cmd())
            c.tag_bind(tag, "<Enter>", lambda e, t=text: self._on_btn_enter(t))
            c.tag_bind(tag, "<Leave>", lambda e, t=text: self._on_btn_leave(t))

    def _round_rect(self, canvas, x1, y1, x2, y2, r, **kwargs):
        """Draw a rounded rectangle using polygon + smooth bezier."""
        d = r * 0.45  # control point offset for smooth curves
        pts = [
            x1 + r, y1,
            x2 - r, y1,
            x2 - r + d, y1,
            x2, y1,
            x2, y1 + r - d,
            x2, y1 + r,
            x2, y2 - r,
            x2, y2 - r + d,
            x2, y2,
            x2 - r + d, y2,
            x2 - r, y2,
            x1 + r, y2,
            x1 + r - d, y2,
            x1, y2,
            x1, y2 - r + d,
            x1, y2 - r,
            x1, y1 + r,
            x1, y1 + r - d,
            x1, y1,
            x1 + r - d, y1,
        ]
        return canvas.create_polygon(pts, smooth=True, **kwargs)

    def _on_btn_enter(self, name):
        d = self._btn_data[name]
        if d["secondary"]:
            fill = SURFACE
        else:
            fill = self._accent_hover()
        d["canvas"].itemconfig(d["rect"], fill=fill)

    def _on_btn_leave(self, name):
        d = self._btn_data[name]
        if d["secondary"]:
            fill = SURFACE_LIGHT
        else:
            fill = self._accent()
        d["canvas"].itemconfig(d["rect"], fill=fill)

    # ---- ring drawing ----
    def _draw_ring(self, fraction):
        self.canvas.delete("ring")
        cx, cy, r = 135, 135, 105
        width = 9

        # track
        self.canvas.create_oval(
            cx - r, cy - r, cx + r, cy + r,
            outline=RING_TRACK, width=width, tags="ring"
        )

        if fraction <= 0.001:
            return

        accent = self._accent()
        angle = fraction * 360
        start = 90
        extent = -angle

        # outer glow (wider arc with stipple for pseudo-transparency)
        self.canvas.create_arc(
            cx - r, cy - r, cx + r, cy + r,
            start=start, extent=extent,
            outline=accent, width=width + 8,
            style="arc", stipple="gray12", tags="ring"
        )
        self.canvas.create_arc(
            cx - r, cy - r, cx + r, cy + r,
            start=start, extent=extent,
            outline=accent, width=width + 4,
            style="arc", stipple="gray25", tags="ring"
        )

        # main arc
        self.canvas.create_arc(
            cx - r, cy - r, cx + r, cy + r,
            start=start, extent=extent,
            outline=accent, width=width,
            style="arc", tags="ring"
        )

        # inner highlight
        self.canvas.create_arc(
            cx - r, cy - r, cx + r, cy + r,
            start=start, extent=extent,
            outline=WHITE, width=3,
            style="arc", stipple="gray25", tags="ring"
        )

    # ---- timer state machine ----
    def start(self):
        if self.state == "idle":
            self.remaining = self.work_seconds
            self.phase = "work"
            self._update_phase_ui()

        self.state = "running"
        self._set_btn_state("Start", False)
        self._set_btn_state("Pause", True)

        # rename start -> Resume for later pauses
        self._btn_data["Start"]["canvas"].itemconfig(
            self._btn_data["Start"]["label"], text="Pause", fill=BG
        )
        self._btn_data["Start"]["command"] = self.pause
        for tag in (self._btn_data["Start"]["rect"], self._btn_data["Start"]["label"]):
            self._btn_data["Start"]["canvas"].tag_unbind(tag, "<Button-1>")
            self._btn_data["Start"]["canvas"].tag_bind(tag, "<Button-1>", lambda e: self.pause())

        self._tick()

    def pause(self):
        self.state = "paused"
        if self.after_id:
            self.after_cancel(self.after_id)
            self.after_id = None

        self._set_btn_state("Pause", False)
        self._set_btn_state("Start", True)

        b = self._btn_data["Start"]
        b["canvas"].itemconfig(b["label"], text="Start", fill=BG)
        b["command"] = self.start
        for tag in (b["rect"], b["label"]):
            b["canvas"].tag_unbind(tag, "<Button-1>")
            b["canvas"].tag_bind(tag, "<Button-1>", lambda e: self.start())

    def reset(self):
        self.state = "idle"
        if self.after_id:
            self.after_cancel(self.after_id)
            self.after_id = None
        self.phase = "work"
        self.remaining = self.work_seconds
        self._update_phase_ui()
        self._update_display()
        self._draw_ring(1.0)
        self.title("Pomodoro")

        self._set_btn_state("Pause", False)
        self._set_btn_state("Start", True)

        b = self._btn_data["Start"]
        b["canvas"].itemconfig(b["label"], text="Start", fill=BG)
        b["command"] = self.start
        for tag in (b["rect"], b["label"]):
            b["canvas"].tag_unbind(tag, "<Button-1>")
            b["canvas"].tag_bind(tag, "<Button-1>", lambda e: self.start())

    def _set_btn_state(self, name, enabled):
        d = self._btn_data[name]
        if enabled:
            d["canvas"].configure(cursor="hand2")
            if d["secondary"]:
                d["canvas"].itemconfig(d["rect"], fill=SURFACE_LIGHT)
            d["canvas"].itemconfig(d["label"], fill=d["text_fill"])
        else:
            d["canvas"].configure(cursor="")
            d["canvas"].itemconfig(d["rect"], fill=SURFACE_LIGHT)
            d["canvas"].itemconfig(d["label"], fill=TEXT_DIM)

    def _tick(self):
        if self.state != "running":
            return

        if self.remaining <= 0:
            self._phase_complete()
            return

        self.remaining -= 1
        self._update_display()

        total = self.work_seconds if self.phase == "work" else self.break_seconds
        self._draw_ring(self.remaining / total)

        self.title(f"{self._format_time(self.remaining)} · Pomodoro")
        self.after_id = self.after(1000, self._tick)

    def _phase_complete(self):
        if self.phase == "work":
            self.sessions += 1
            self.session_label.config(text=f"session  {self.sessions}")
            self.phase = "break"
            self.remaining = self.break_seconds
            notify("Pomodoro", "Focus session complete — take a breath.")
        else:
            self.phase = "work"
            self.remaining = self.work_seconds
            notify("Pomodoro", "Break over — back to focus.")

        self._update_phase_ui()
        self._update_display()
        self._draw_ring(1.0)
        self.title("Pomodoro")
        self.bell()
        self._tick()

    # ---- UI updates ----
    def _update_phase_ui(self):
        if self.phase == "break":
            self.phase_label.config(text="BREATHE", fg=BREAK_ACCENT)
        else:
            self.phase_label.config(text="FOCUS", fg=WORK_ACCENT)

        # update primary button color
        b = self._btn_data["Start"]
        accent = self._accent()
        b["canvas"].itemconfig(b["rect"], fill=accent)
        b["fill"] = accent
        b["text_fill"] = BG

        # redraw ring
        total = self.work_seconds if self.phase == "work" else self.break_seconds
        self._draw_ring(self.remaining / total)

    def _update_display(self):
        self.canvas.itemconfig(
            self.timer_text, text=self._format_time(self.remaining)
        )

    def _toggle_top(self):
        self.attributes("-topmost", self.top_var.get())


if __name__ == "__main__":
    app = PomodoroTimer()
    app.mainloop()
