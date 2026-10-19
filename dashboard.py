# dashboard.py
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

import analytics
import database
from tracker import Tracker

# Configure CustomTkinter modern aesthetics
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

PALETTE = {
    "bg": "#121316",
    "card": "#1E1F24",
    "card_border": "#2B2D35",
    "Productive": "#00E676",
    "Neutral": "#78909C",
    "Distracting": "#FF5252",
    "accent": "#2979FF",
    "text": "#ECEFF1",
    "subtext": "#90A4AE"
}

matplotlib.rcParams.update({
    "text.color": PALETTE["text"],
    "axes.labelcolor": PALETTE["text"],
    "xtick.color": PALETTE["subtext"],
    "ytick.color": PALETTE["subtext"],
    "figure.facecolor": PALETTE["card"],
    "axes.facecolor": PALETTE["card"],
    "grid.color": PALETTE["card_border"],
    "font.family": "sans-serif"
})


class FocusLensApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("FocusLens Pro • Intelligence & Telemetry")
        self.geometry("1180x760")
        self.minsize(1040, 680)
        self.configure(fg_color=PALETTE["bg"])

        self.tracker = Tracker()

        # Pomodoro State
        self.work_seconds = 25 * 60
        self.break_seconds = 5 * 60
        self.time_remaining = self.work_seconds
        self.is_work_interval = True
        self.pomodoro_active = False
        self.timer_job = None

        self._build_sidebar()
        self._build_content_area()

        self.refresh_all_visuals()
        self._start_event_loops()
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=PALETTE["card"])
        self.sidebar.pack(side="left", fill="y")

        title = ctk.CTkLabel(
            self.sidebar, text="FOCUSLENS", font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#FFFFFF"
        )
        title.pack(pady=(28, 4))

        subtitle = ctk.CTkLabel(
            self.sidebar, text="Analytics Engine v2.0", font=ctk.CTkFont(size=11),
            text_color=PALETTE["subtext"]
        )
        subtitle.pack(pady=(0, 24))

        self.track_toggle_btn = ctk.CTkButton(
            self.sidebar, text="Activate Tracker", command=self._toggle_tracking,
            fg_color=PALETTE["accent"], hover_color="#1C54B2", height=38,
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.track_toggle_btn.pack(padx=18, pady=8, fill="x")

        self.status_indicator = ctk.CTkLabel(
            self.sidebar, text="● Engine Offline", text_color=PALETTE["Distracting"],
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.status_indicator.pack(pady=(0, 16))

        self.focus_mode_switch = ctk.CTkSwitch(
            self.sidebar, text="Focus Sentinel", command=self._toggle_focus_mode,
            progress_color=PALETTE["accent"]
        )
        self.focus_mode_switch.pack(padx=20, pady=12, anchor="w")

        ctk.CTkFrame(self.sidebar, height=1, fg_color=PALETTE["card_border"]).pack(fill="x", padx=16, pady=16)

        # Navigation Buttons
        self.nav_btns = {}
        for tab_name in ["Dashboard", "Chronology", "Deep Focus", "Export"]:
            btn = ctk.CTkButton(
                self.sidebar, text=tab_name, height=36,
                fg_color="transparent", hover_color="#2A2B33", anchor="w",
                font=ctk.CTkFont(size=13),
                command=lambda name=tab_name: self._switch_tab(name)
            )
            btn.pack(fill="x", padx=12, pady=4)
            self.nav_btns[tab_name] = btn

    def _build_content_area(self):
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(side="right", fill="both", expand=True, padx=16, pady=16)

        self.views = {
            "Dashboard": self._init_dashboard_tab(),
            "Chronology": self._init_chronology_tab(),
            "Deep Focus": self._init_pomodoro_tab(),
            "Export": self._init_export_tab()
        }
        self._switch_tab("Dashboard")

    def _switch_tab(self, name):
        for tab_name, view in self.views.items():
            if tab_name == name:
                view.pack(fill="both", expand=True)
                self.nav_btns[tab_name].configure(fg_color="#2A2B33")
            else:
                view.pack_forget()
                self.nav_btns[tab_name].configure(fg_color="transparent")

    # ------------------ TAB 1: DASHBOARD ------------------
    def _init_dashboard_tab(self):
        view = ctk.CTkFrame(self.container, fg_color="transparent")

        # Metric KPI cards
        kpi_row = ctk.CTkFrame(view, fg_color="transparent")
        kpi_row.pack(fill="x", pady=(0, 10))

        self.kpi_labels = {}
        cards = [
            ("Score", "0%", PALETTE["Productive"]),
            ("Focus Efficiency", "0.0", PALETTE["accent"]),
            ("Productive Time", "0h 00m", PALETTE["Productive"]),
            ("Distractions", "0h 00m", PALETTE["Distracting"]),
            ("App Switches", "0", PALETTE["subtext"])
        ]
        for key, default, color in cards:
            card = ctk.CTkFrame(kpi_row, fg_color=PALETTE["card"], corner_radius=10)
            card.pack(side="left", fill="both", expand=True, padx=4)
            ctk.CTkLabel(card, text=key.upper(), font=ctk.CTkFont(size=10, weight="bold"),
                         text_color=PALETTE["subtext"]).pack(pady=(10, 0))
            lbl = ctk.CTkLabel(card, text=default, font=ctk.CTkFont(size=18, weight="bold"),
                               text_color=color)
            lbl.pack(pady=(0, 10))
            self.kpi_labels[key] = lbl

        # Chart Zone
        chart_zone = ctk.CTkFrame(view, fg_color="transparent")
        chart_zone.pack(fill="both", expand=True)

        self.fig_dash = Figure(figsize=(7, 4), dpi=100)
        self.canvas_dash = FigureCanvasTkAgg(self.fig_dash, master=chart_zone)
        self.canvas_dash.get_tk_widget().pack(fill="both", expand=True)

        # AI Insights pill
        self.insight_banner = ctk.CTkLabel(
            view, text="", font=ctk.CTkFont(size=12), text_color="#CFD8DC",
            fg_color=PALETTE["card"], corner_radius=8, height=36
        )
        self.insight_banner.pack(fill="x", pady=(8, 0))

        return view

    # ------------------ TAB 2: CHRONOLOGY ------------------
    def _init_chronology_tab(self):
        view = ctk.CTkFrame(self.container, fg_color="transparent")
        self.fig_chrono = Figure(figsize=(8, 5), dpi=100)
        self.canvas_chrono = FigureCanvasTkAgg(self.fig_chrono, master=view)
        self.canvas_chrono.get_tk_widget().pack(fill="both", expand=True)
        return view

    # ------------------ TAB 3: DEEP FOCUS ------------------
    def _init_pomodoro_tab(self):
        view = ctk.CTkFrame(self.container, fg_color="transparent")

        card = ctk.CTkFrame(view, fg_color=PALETTE["card"], corner_radius=12, width=420, height=360)
        card.place(relx=0.5, rely=0.5, anchor="center")

        self.pomodoro_phase_lbl = ctk.CTkLabel(
            card, text="Sprint Interval", font=ctk.CTkFont(size=16, weight="bold"),
            text_color=PALETTE["accent"]
        )
        self.pomodoro_phase_lbl.pack(pady=(28, 4))

        self.pomodoro_time_lbl = ctk.CTkLabel(
            card, text="25:00", font=ctk.CTkFont(size=54, weight="bold"), text_color="#FFFFFF"
        )
        self.pomodoro_time_lbl.pack(pady=10)

        ctl_row = ctk.CTkFrame(card, fg_color="transparent")
        ctl_row.pack(pady=16)

        self.pomo_start_btn = ctk.CTkButton(
            ctl_row, text="Start Session", width=110, command=self._toggle_pomodoro,
            fg_color=PALETTE["accent"]
        )
        self.pomo_start_btn.pack(side="left", padx=8)

        ctk.CTkButton(
            ctl_row, text="Reset", width=90, fg_color="#37474F", hover_color="#455A64",
            command=self._reset_pomodoro
        ).pack(side="left", padx=8)

        return view

    # ------------------ TAB 4: EXPORT ------------------
    def _init_export_tab(self):
        view = ctk.CTkFrame(self.container, fg_color="transparent")

        box = ctk.CTkFrame(view, fg_color=PALETTE["card"], corner_radius=12, width=460)
        box.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(box, text="Database Controls", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(24, 8))
        ctk.CTkButton(box, text="Export CSV Telemetry", width=240, command=self._export_csv).pack(pady=8)
        ctk.CTkButton(box, text="Wipe All History", width=240, fg_color=PALETTE["Distracting"],
                      hover_color="#D32F2F", command=self._wipe_database).pack(pady=(8, 24))

        return view

    # ------------------ REFRESH & CHARTS ------------------
    def refresh_all_visuals(self):
        df_today = analytics.load_data(days=1)
        metrics = analytics.calculate_metrics(df_today, days=1)

        # Update KPIs
        self.kpi_labels["Score"].configure(text=f"{metrics['score']}%")
        self.kpi_labels["Focus Efficiency"].configure(text=f"{metrics['focus_efficiency']}")
        self.kpi_labels["Productive Time"].configure(text=metrics["productive_time"])
        self.kpi_labels["Distractions"].configure(text=metrics["distracting_time"])
        self.kpi_labels["App Switches"].configure(text=str(metrics["context_switches"]))

        # Update Insights
        insights = analytics.generate_executive_insights(df_today)
        self.insight_banner.configure(text="  •  ".join(insights))

        # Render Dashboard Charts
        self.fig_dash.clear()
        if not df_today.empty:
            ax1 = self.fig_dash.add_subplot(121)
            totals = df_today.groupby("category")["seconds"].sum()
            colors = [PALETTE[cat] for cat in totals.index]
            wedges, _, _ = ax1.pie(
                totals, labels=totals.index, autopct="%1.0f%%", startangle=90,
                colors=colors, wedgeprops=dict(width=0.45, edgecolor=PALETTE["card"])
            )
            ax1.set_title("Distribution Ratio", fontsize=11, pad=10)

            ax2 = self.fig_dash.add_subplot(122)
            top = analytics.top_apps_breakdown(df_today, 5)
            if not top.empty:
                bars = ax2.barh(top.index[::-1], top.values[::-1], color=PALETTE["accent"], height=0.55)
                ax2.set_title("Dominant Applications (Minutes)", fontsize=11, pad=10)
                ax2.spines["top"].set_visible(False)
                ax2.spines["right"].set_visible(False)
                ax2.grid(axis="x", linestyle="--", alpha=0.3)
        self.fig_dash.tight_layout()
        self.canvas_dash.draw()

        # Render Chronology Charts (Stacked 7-Day & 24h Hourly Profile)
        df_week = analytics.load_data(days=7)
        self.fig_chrono.clear()
        if not df_week.empty:
            ax_week = self.fig_chrono.add_subplot(211)
            week_table = analytics.weekly_trend(df_week)
            week_table.plot(
                kind="bar", stacked=True, ax=ax_week,
                color=[PALETTE[c] for c in week_table.columns], width=0.45
            )
            ax_week.set_title("7-Day Trajectory (Hours)", fontsize=11)
            ax_week.set_ylabel("Hours")
            ax_week.spines["top"].set_visible(False)
            ax_week.spines["right"].set_visible(False)

            ax_hourly = self.fig_chrono.add_subplot(212)
            matrix = analytics.hourly_intensity_matrix(df_week)
            ax_hourly.plot(matrix.index, matrix["Productive"], label="Productive", color=PALETTE["Productive"], lw=2)
            ax_hourly.plot(matrix.index, matrix["Distracting"], label="Distracting", color=PALETTE["Distracting"], lw=2)
            ax_hourly.fill_between(matrix.index, matrix["Productive"], color=PALETTE["Productive"], alpha=0.15)
            ax_hourly.set_title("24-Hour Diurnal Focus Profile (Average Minutes/Hour)", fontsize=11)
            ax_hourly.set_xlabel("Hour of Day (0 - 23)")
            ax_hourly.set_xticks(range(0, 24, 2))
            ax_hourly.legend(frameon=False, loc="upper right")
            ax_hourly.spines["top"].set_visible(False)
            ax_hourly.spines["right"].set_visible(False)

        self.fig_chrono.tight_layout()
        self.canvas_chrono.draw()

    # ------------------ EVENT LOOPS ------------------
    def _start_event_loops(self):
        self._check_warnings()
        self._schedule_refresh()

    def _schedule_refresh(self):
        self.refresh_all_visuals()
        self.after(20000, self._schedule_refresh)

    def _check_warnings(self):
        while not self.tracker.warnings.empty():
            bad_app = self.tracker.warnings.get()
            messagebox.showwarning(
                "Focus Sentinel Triggered",
                f"Attention Diversion Detected:\nActive App: '{bad_app}'\nRedirect focus to active goals."
            )
        self.after(1000, self._check_warnings)

    # ------------------ CONTROLS ------------------
    def _toggle_tracking(self):
        if self.tracker.running:
            self.tracker.stop()
            self.track_toggle_btn.configure(text="Activate Tracker", fg_color=PALETTE["accent"])
            self.status_indicator.configure(text="● Engine Offline", text_color=PALETTE["Distracting"])
        else:
            self.tracker.start()
            self.track_toggle_btn.configure(text="Deactivate Tracker", fg_color="#C62828")
            self.status_indicator.configure(text="● Real-Time Telemetry ON", text_color=PALETTE["Productive"])

    def _toggle_focus_mode(self):
        self.tracker.focus_mode = self.focus_mode_switch.get()

    def _toggle_pomodoro(self):
        if self.pomodoro_active:
            self.pomodoro_active = False
            if self.timer_job:
                self.after_cancel(self.timer_job)
            self.pomo_start_btn.configure(text="Resume")
        else:
            self.pomodoro_active = True
            self.pomo_start_btn.configure(text="Pause")
            self._tick_pomodoro()

    def _tick_pomodoro(self):
        if self.time_remaining > 0:
            self.time_remaining -= 1
            mins = self.time_remaining // 60
            secs = self.time_remaining % 60
            self.pomodoro_time_lbl.configure(text=f"{mins:02d}:{secs:02d}")
            self.timer_job = self.after(1000, self._tick_pomodoro)
        else:
            self.is_work_interval = not self.is_work_interval
            self.time_remaining = self.work_seconds if self.is_work_interval else self.break_seconds
            status = "Sprint Interval" if self.is_work_interval else "Recovery Period"
            self.pomodoro_phase_lbl.configure(text=status)
            messagebox.showinfo("Deep Focus Protocol", f"Interval complete! Entering: {status}")
            self._tick_pomodoro()

    def _reset_pomodoro(self):
        if self.timer_job:
            self.after_cancel(self.timer_job)
        self.pomodoro_active = False
        self.is_work_interval = True
        self.time_remaining = self.work_seconds
        self.pomodoro_phase_lbl.configure(text="Sprint Interval")
        self.pomodoro_time_lbl.configure(text="25:00")
        self.pomo_start_btn.configure(text="Start Session")

    def _export_csv(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("CSV", "*.csv")],
            initialfile="focuslens_telemetry.csv"
        )
        if path:
            df = analytics.load_data(days=30)
            analytics.export_csv(df, path)
            messagebox.showinfo("Export Engine", "30-day telemetry successfully written.")

    def _wipe_database(self):
        if messagebox.askyesno("Confirm Purge", "Permanently erase logged telemetry records?"):
            database.clear_all()
            self.refresh_all_visuals()

    def _on_closing(self):
        if self.tracker.running:
            self.tracker.stop()
        self.destroy()