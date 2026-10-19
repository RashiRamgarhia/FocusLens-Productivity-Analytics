# database.py
import os
import sqlite3
from datetime import datetime

BASE_FOLDER = os.path.dirname(os.path.abspath(__file__))
DATA_FOLDER = os.path.join(BASE_FOLDER, "data")
DB_PATH = os.path.join(DATA_FOLDER, "focuslens.db")


def get_connection():
    return sqlite3.connect(DB_PATH)


def create_tables():
    os.makedirs(DATA_FOLDER, exist_ok=True)
    conn = get_connection()
    cursor = conn.cursor()

    # Main aggregated usage table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usage (
            date TEXT,
            hour INTEGER,
            app_name TEXT,
            seconds INTEGER,
            PRIMARY KEY (date, hour, app_name)
        )
    """)

    # Window context-switching log for flow-state analytics
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS window_switches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            date TEXT,
            hour INTEGER,
            app_name TEXT
        )
    """)

    conn.commit()
    conn.close()


def add_usage(app_name, seconds):
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    hour = now.hour

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO usage (date, hour, app_name, seconds)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(date, hour, app_name)
        DO UPDATE SET seconds = seconds + excluded.seconds
    """, (date_str, hour, app_name, seconds))
    conn.commit()
    conn.close()


def record_window_switch(app_name):
    now = datetime.now()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO window_switches (timestamp, date, hour, app_name)
        VALUES (?, ?, ?, ?)
    """, (now.isoformat(), now.strftime("%Y-%m-%d"), now.hour, app_name))
    conn.commit()
    conn.close()


def get_usage(start_date, end_date):
    conn = get_connection()
    cursor = conn.cursor()
    rows = cursor.execute("""
        SELECT date, hour, app_name, seconds 
        FROM usage 
        WHERE date BETWEEN ? AND ?
    """, (start_date, end_date)).fetchall()
    conn.close()
    return rows


def get_switch_count(start_date, end_date):
    conn = get_connection()
    cursor = conn.cursor()
    count = cursor.execute("""
        SELECT COUNT(*) 
        FROM window_switches 
        WHERE date BETWEEN ? AND ?
    """, (start_date, end_date)).fetchone()[0]
    conn.close()
    return count


def clear_all():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM usage")
    cursor.execute("DELETE FROM window_switches")
    conn.commit()
    conn.close()