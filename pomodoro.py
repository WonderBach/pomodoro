import tkinter as tk
import subprocess

WORK_MINUTES = 25
BREAK_MINUTES = 5

WORK_SECONDS = WORK_MINUTES * 60
BREAK_SECONDS = BREAK_MINUTES * 60

# Color palette — warm terracotta/cream theme
COLOR_BG = "#faf5f3"
COLOR_SURFACE = "#fffaf7"
COLOR_PRIMARY = "#b5715f"
COLOR_PRIMARY_DARK = "#9e5e4e"
COLOR_RING_TRACK = "#e8ddd6"
COLOR_RING_FILL = "#b5715f"
COLOR_BREAK = "#7d9e8c"
COLOR_BREAK_DARK = "#6a8b79"
COLOR_BREAK_RING = "#7d9e8c"
COLOR_TEXT = "#3d2d28"
COLOR_TEXT_SECONDARY = "#9e8b84"
COLOR_BTN_SECONDARY = "#e0d5cf"
COLOR_BTN_SECONDARY_HOVER = "#d0c5bf"

FONT_TIMER = ("Helvetica Neue", 52, "bold")
FONT_LABEL = ("Helvetica Neue", 15, "bold")
FONT_BUTTON = ("Helvetica Neue", 13)
FONT_SMALL = ("Helvetica Neue", 11)
FONT_TITLE = ("Helvetica Neue", 13)


def notify(title, message):
    script = f'display notification "{message}" with title "{title}" sound name "Glass"'
    subprocess.run(["osascript", "-e", script], capture_output=True)


class PomodoroTimer(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Pomodoro")
        self.resizable(False, False)
        self.configure(bg=COLOR_BG)

        self.work_seconds = WORK_SECONDS
        self.break_seconds = BREAK_SECONDS
        self.remaining = self.work_seconds
        self.phase = "work"
        self.state = "idle"
        self.after_id = None
        self.sessions = 0

        self._build_ui()
        self._center_window(360, 430)
        self.update_idletasks()
        self.lift()
        self.focus_force()

    def _center_window(self, w, h):
        ws = self.winfo_screenwidth()
        hs = self.winfo_screenheight()
        x = (ws - w) // 2
        y = (hs - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _build_ui(self):
        # Main container with subtle border
        container = tk.Frame(self, bg=COLOR_BG, highlightbackground=COLOR_RING_TRACK,
                             highlightthickness=1, bd=0)
        container.pack(fill="both", expand=True, padx=1, pady=1)

        # Title
        title_label = tk.Label(
            container, text="Pomodoro",
            font=FONT_TITLE, fg=COLOR_TEXT, bg=COLOR_BG
        )
        title_label.pack(pady=(20, 4))

        # Phase indicator
        self.phase_label = tk.Label(
            container, text="FOCUS",
            font=FONT_LABEL, fg=COLOR_PRIMARY, bg=COLOR_BG
        )
        self.phase_label.pack()

        # Timer canvas — donut progress ring
        self.timer_canvas = tk.Canvas(
            container, width=240, height=240, bg=COLOR_BG,
            highlightthickness=0
        )
        self.timer_canvas.pack(pady=(6, 0))

        # Draw track ring
        self.timer_canvas.create_oval(
            28, 28, 212, 212,
            outline=COLOR_RING_TRACK, width=10, tags="track"
        )
        # Initial progress arc
        self.timer_canvas.create_arc(
            28, 28, 212, 212,
            start=90, extent=-359.9,
            outline=COLOR_RING_FILL, width=10, style="arc", tags="progress"
        )
        # Timer text
        self.timer_text = self.timer_canvas.create_text(
            120, 120, text=self._format_time(self.remaining),
            font=FONT_TIMER, fill=COLOR_TEXT
        )

        # Button frame
        btn_frame = tk.Frame(container, bg=COLOR_BG)
        btn_frame.pack(pady=(18, 8))

        btn_style = {
            "font": FONT_BUTTON,
            "relief": "flat",
            "padx": 24,
            "pady": 8,
            "cursor": "hand2",
            "borderwidth": 0,
        }

        self.start_btn = tk.Button(
            btn_frame, text="Start",
            bg=COLOR_PRIMARY, fg="white",
            activebackground=COLOR_PRIMARY_DARK, activeforeground="white",
            command=self.start, **btn_style
        )
        self.start_btn.pack(side="left", padx=4)

        self.pause_btn = tk.Button(
            btn_frame, text="Pause",
            bg=COLOR_BTN_SECONDARY, fg=COLOR_TEXT,
            activebackground=COLOR_BTN_SECONDARY_HOVER, activeforeground=COLOR_TEXT,
            command=self.pause, state="disabled", **btn_style
        )
        self.pause_btn.pack(side="left", padx=4)

        self.reset_btn = tk.Button(
            btn_frame, text="Reset",
            bg=COLOR_BTN_SECONDARY, fg=COLOR_TEXT,
            activebackground=COLOR_BTN_SECONDARY_HOVER, activeforeground=COLOR_TEXT,
            command=self.reset, **btn_style
        )
        self.reset_btn.pack(side="left", padx=4)

        # Session counter
        self.session_label = tk.Label(
            container, text=f"{self.sessions} sessions completed",
            font=FONT_SMALL, fg=COLOR_TEXT_SECONDARY, bg=COLOR_BG
        )
        self.session_label.pack(pady=(14, 4))

        # Always-on-top toggle
        self.top_var = tk.BooleanVar(value=False)
        top_cb = tk.Checkbutton(
            container, text="Always on top", variable=self.top_var,
            font=FONT_SMALL, bg=COLOR_BG, fg=COLOR_TEXT_SECONDARY,
            activebackground=COLOR_BG, selectcolor=COLOR_SURFACE,
            cursor="hand2", command=self._toggle_top
        )
        top_cb.pack(pady=(0, 12))

    def _accent_color(self):
        return COLOR_PRIMARY if self.phase == "work" else COLOR_BREAK

    def _accent_dark(self):
        return COLOR_PRIMARY_DARK if self.phase == "work" else COLOR_BREAK_DARK

    def _progress_color(self):
        return COLOR_RING_FILL if self.phase == "work" else COLOR_BREAK_RING

    def _draw_progress(self, fraction):
        self.timer_canvas.delete("progress")
        if fraction <= 0:
            return
        angle = fraction * 360
        start = 90
        extent = -angle
        self.timer_canvas.create_arc(
            28, 28, 212, 212,
            start=start, extent=extent,
            outline=self._progress_color(),
            width=10, style="arc", tags="progress"
        )

    def _format_time(self, seconds):
        m = seconds // 60
        s = seconds % 60
        return f"{m:02d}:{s:02d}"

    def _update_phase_ui(self):
        phase_text = "FOCUS" if self.phase == "work" else "BREAK"
        self.phase_label.config(text=phase_text, fg=self._accent_color())
        self.start_btn.config(
            bg=self._accent_color(),
            activebackground=self._accent_dark()
        )

    def start(self):
        if self.state == "idle":
            self.remaining = self.work_seconds
            self.phase = "work"
            self._update_phase_ui()

        self.state = "running"
        self.start_btn.config(state="disabled")
        self.pause_btn.config(state="normal")
        self._tick()

    def pause(self):
        self.state = "paused"
        if self.after_id:
            self.after_cancel(self.after_id)
            self.after_id = None
        self.start_btn.config(state="normal", text="Resume")
        self.pause_btn.config(state="disabled")

    def reset(self):
        self.state = "idle"
        if self.after_id:
            self.after_cancel(self.after_id)
            self.after_id = None
        self.phase = "work"
        self.remaining = self.work_seconds
        self._update_phase_ui()
        self._update_display()
        self._draw_progress(1.0)
        self.start_btn.config(state="normal", text="Start")
        self.pause_btn.config(state="disabled")
        self.title("Pomodoro")

    def _tick(self):
        if self.state != "running":
            return

        if self.remaining <= 0:
            self._phase_complete()
            return

        self.remaining -= 1
        self._update_display()

        total = self.work_seconds if self.phase == "work" else self.break_seconds
        self._draw_progress(self.remaining / total)

        self.title(f"{self._format_time(self.remaining)} - Pomodoro")
        self.after_id = self.after(1000, self._tick)

    def _phase_complete(self):
        if self.phase == "work":
            self.sessions += 1
            self.session_label.config(text=f"{self.sessions} sessions completed")
            self.phase = "break"
            self.remaining = self.break_seconds
            notify("Pomodoro", "Work session complete! Time for a break.")
        else:
            self.phase = "work"
            self.remaining = self.work_seconds
            notify("Pomodoro", "Break over! Back to work.")

        self._update_phase_ui()
        self._update_display()
        self._draw_progress(1.0)
        self.title("Pomodoro")
        self.bell()
        self._tick()

    def _update_display(self):
        self.timer_canvas.itemconfig(
            self.timer_text, text=self._format_time(self.remaining)
        )

    def _toggle_top(self):
        self.attributes("-topmost", self.top_var.get())


if __name__ == "__main__":
    app = PomodoroTimer()
    app.mainloop()
