import sqlite3
from pathlib import Path

from mqtt_config import DB_FOLDER, DB_FILE_NAME


# Build the database path relative to this file, not relative to the terminal folder.
# This keeps the DB in SafeCore_Project/database/safecore.db even if the script
# is executed from another directory.
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / DB_FOLDER / DB_FILE_NAME


def now_local_sql():
    return "datetime('now', 'localtime')"


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH, timeout=10)


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS telemetry (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_id TEXT NOT NULL,
        device_type TEXT NOT NULL,
        zone TEXT NOT NULL,
        temperature REAL,
        humidity REAL,
        status_text TEXT,
        created_at TEXT DEFAULT ({now_local_sql()})
    )
    """)

    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_type TEXT NOT NULL,
        source_name TEXT NOT NULL,
        zone TEXT NOT NULL,
        message TEXT NOT NULL,
        created_at TEXT DEFAULT ({now_local_sql()})
    )
    """)

    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS alarms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        alarm_code TEXT NOT NULL,
        severity TEXT NOT NULL,
        zone TEXT NOT NULL,
        message TEXT NOT NULL,
        is_active INTEGER NOT NULL,
        created_at TEXT DEFAULT ({now_local_sql()})
    )
    """)

    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS system_state (
        state_key TEXT PRIMARY KEY,
        state_value TEXT NOT NULL,
        updated_at TEXT DEFAULT ({now_local_sql()})
    )
    """)

    conn.commit()
    conn.close()


def save_telemetry(
    device_id,
    device_type,
    zone,
    temperature=None,
    humidity=None,
    status_text=None
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO telemetry (
            device_id, device_type, zone, temperature, humidity, status_text, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, datetime('now', 'localtime'))
    """, (device_id, device_type, zone, temperature, humidity, status_text))

    conn.commit()
    conn.close()


def save_event(event_type, source_name, zone, message):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO events (
            event_type, source_name, zone, message, created_at
        )
        VALUES (?, ?, ?, ?, datetime('now', 'localtime'))
    """, (event_type, source_name, zone, message))

    conn.commit()
    conn.close()


def save_alarm(alarm_code, severity, zone, message, is_active):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO alarms (
            alarm_code, severity, zone, message, is_active, created_at
        )
        VALUES (?, ?, ?, ?, ?, datetime('now', 'localtime'))
    """, (alarm_code, severity, zone, message, is_active))

    conn.commit()
    conn.close()


def set_system_state(state_key, state_value):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO system_state (state_key, state_value, updated_at)
        VALUES (?, ?, datetime('now', 'localtime'))
        ON CONFLICT(state_key)
        DO UPDATE SET
            state_value = excluded.state_value,
            updated_at = datetime('now', 'localtime')
    """, (state_key, str(state_value)))

    conn.commit()
    conn.close()


def get_current_states():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT state_key, state_value
        FROM system_state
    """)
    rows = cursor.fetchall()

    conn.close()

    return {key: value for key, value in rows}


def get_active_alarm_count():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        WITH latest_alarm_per_code AS (
            SELECT alarm_code, MAX(id) AS max_id
            FROM alarms
            GROUP BY alarm_code
        )
        SELECT COUNT(*)
        FROM alarms a
        INNER JOIN latest_alarm_per_code l
            ON a.id = l.max_id
        WHERE a.is_active = 1
    """)

    count = cursor.fetchone()[0]
    conn.close()

    return count


def get_recent_history(limit=20):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT created_at, 'EVENT' AS record_type, event_type, source_name, zone, message
        FROM events
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))
    event_rows = cursor.fetchall()

    cursor.execute("""
        SELECT created_at, 'ALARM' AS record_type, alarm_code, severity, zone, message
        FROM alarms
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))
    alarm_rows = cursor.fetchall()

    conn.close()

    rows = event_rows + alarm_rows
    rows.sort(key=lambda row: row[0], reverse=True)

    result = []

    for row in rows[:limit]:
        created_at, record_type, item_1, item_2, zone, message = row

        if " " in created_at:
            time_only = created_at.split(" ")[1]
        else:
            time_only = created_at

        result.append(
            f"[{time_only}] {record_type} | {item_1} | {item_2} | {zone} | {message}"
        )

    return result