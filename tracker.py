# tracker.py
import ctypes
import queue
import threading
import time
import psutil

import categories
import database

CHECK_EVERY_SECONDS = 3
IDLE_LIMIT_SECONDS = 240
WARNING_GAP_SECONDS = 45


class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", ctypes.c_uint),
        ("dwTime", ctypes.c_uint),
    ]


def get_active_window():
    user32 = ctypes.windll.user32
    window = user32.GetForegroundWindow()
    if not window:
        return "desktop", "Desktop"

    length = user32.GetWindowTextLengthW(window)
    buffer = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(window, buffer, length + 1)
    title = buffer.value

    pid = ctypes.c_ulong()
    user32.GetWindowThreadProcessId(window, ctypes.byref(pid))
    try:
        name = psutil.Process(pid.value).name()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        name = "system"

    name = name.lower().replace(".exe", "")
    return name, title


def get_idle_seconds():
    info = LASTINPUTINFO()
    info.cbSize = ctypes.sizeof(LASTINPUTINFO)
    ctypes.windll.user32.GetLastInputInfo(ctypes.byref(info))
    ctypes.windll.kernel32.GetTickCount.restype = ctypes.c_uint
    now = ctypes.windll.kernel32.GetTickCount()
    return (now - info.dwTime) / 1000.0


class Tracker:
    def __init__(self):
        self.running = False
        self.thread = None
        self.current_app = None
        self.last_recorded_app = None
        self.focus_mode = False
        self.last_warning_time = 0
        self.warnings = queue.Queue()

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread is not None:
            self.thread.join(timeout=CHECK_EVERY_SECONDS + 1)
        self.current_app = None
        self.last_recorded_app = None

    def _run_loop(self):
        while self.running:
            try:
                idle = get_idle_seconds()
                if idle < IDLE_LIMIT_SECONDS:
                    raw_name, title = get_active_window()
                    app_label = categories.get_app_label(raw_name, title)
                    self.current_app = app_label

                    # Log context switch if the user changes active window
                    if app_label != self.last_recorded_app:
                        database.record_window_switch(app_label)
                        self.last_recorded_app = app_label

                    database.add_usage(app_label, CHECK_EVERY_SECONDS)
                    self._check_distraction()
                else:
                    self.current_app = "[Idle / Away]"
            except Exception as err:
                print(f"[Tracker Loop Error]: {err}")

            time.sleep(CHECK_EVERY_SECONDS)

    def _check_distraction(self):
        if not self.focus_mode or not self.current_app:
            return
        if categories.get_category(self.current_app) != "Distracting":
            return

        now = time.time()
        if now - self.last_warning_time >= WARNING_GAP_SECONDS:
            self.last_warning_time = now
            self.warnings.put(self.current_app)