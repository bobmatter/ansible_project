import os
import sqlite3
from werkzeug.security import generate_password_hash

BASE_DIR="/home/world/Documents/sensor_reboot_panel"
DB_PATH=os.path.join(BASE_DIR,"sensor_panel.db")

def main():
    if os.path.exists(DB_PATH):
        print("Database already exists. Init aborted.")
        return

    os.makedirs(BASE_DIR, exist_ok=True)

    conn=sqlite3.connect(DB_PATH)
    cur=conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS sensors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        ansible_host_name TEXT NOT NULL,
        playbook_path TEXT NOT NULL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('superadmin','user'))
    )
    """)

    sensors=[
        ("Sensor 1","sensor1"),
        ("Sensor 2","sensor2"),
        ("Sensor 3","sensor3")
    ]

    for s in sensors:
        cur.execute(
            "INSERT INTO sensors (name, ansible_host_name, playbook_path) VALUES (?,?,?)",
            (s[0],s[1],os.path.join(BASE_DIR,"ansible/reboot_sensor.yml"))
        )

    cur.execute(
        "INSERT INTO users (username,password_hash,role) VALUES (?,?,?)",
        ("admin",generate_password_hash("N3X$RcPl@y"),"superadmin")
    )

    conn.commit()
    conn.close()
    print("DB initialized")

if __name__ == "__main__":
    main()
