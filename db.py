import sqlite3
import datetime

DB = "booster.db"


def init():
    con = sqlite3.connect(DB)
    con.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id         INTEGER PRIMARY KEY,
            full_name  TEXT,
            username   TEXT,
            first_seen TEXT,
            last_seen  TEXT,
            uses       INTEGER DEFAULT 1
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS boosts (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER,
            platform   TEXT,
            service    TEXT,
            target_url TEXT,
            est_sent   INTEGER,
            ran_at     TEXT
        )
    """)
    con.commit()
    con.close()


def log_user(user_id: int, full_name: str, username: str):
    now = datetime.datetime.now().isoformat()
    con = sqlite3.connect(DB)
    existing = con.execute("SELECT id FROM users WHERE id=?", (user_id,)).fetchone()
    if existing:
        con.execute(
            "UPDATE users SET last_seen=?, uses=uses+1, full_name=?, username=? WHERE id=?",
            (now, full_name, username, user_id)
        )
    else:
        con.execute(
            "INSERT INTO users VALUES (?,?,?,?,?,1)",
            (user_id, full_name, username, now, now)
        )
    con.commit()
    con.close()


def log_boost(user_id: int, platform: str, service: str, target_url: str, est_sent: int):
    now = datetime.datetime.now().isoformat()
    con = sqlite3.connect(DB)
    con.execute(
        "INSERT INTO boosts (user_id, platform, service, target_url, est_sent, ran_at) VALUES (?,?,?,?,?,?)",
        (user_id, platform, service, target_url, est_sent, now)
    )
    con.commit()
    con.close()


def get_all_users():
    con = sqlite3.connect(DB)
    rows = con.execute(
        "SELECT id, full_name, username, first_seen, last_seen, uses FROM users ORDER BY first_seen DESC"
    ).fetchall()
    con.close()
    return rows


def get_all_ids():
    con = sqlite3.connect(DB)
    rows = con.execute("SELECT id FROM users").fetchall()
    con.close()
    return [r[0] for r in rows]


def count_users():
    con = sqlite3.connect(DB)
    count = con.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    con.close()
    return count


def count_boosts():
    con = sqlite3.connect(DB)
    count = con.execute("SELECT COUNT(*) FROM boosts").fetchone()[0]
    con.close()
    return count


def get_boost_stats():
    con = sqlite3.connect(DB)
    rows = con.execute(
        "SELECT platform, service, SUM(est_sent) FROM boosts GROUP BY platform, service"
    ).fetchall()
    con.close()
    return rows
