import sqlite3
import os
from contextlib import contextmanager

DB_PATH = os.getenv("DATABASE_PATH", "healthengine.db")

@contextmanager
def get_db():
    """Context manager for SQLite database connection."""
    db_dir = os.path.dirname(DB_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    """Create tables if they don't already exist and seed initial demo user."""
    with get_db() as conn:
        cursor = conn.cursor()

        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                age INTEGER DEFAULT 30,
                height REAL DEFAULT 180,
                weight REAL DEFAULT 67,
                goal TEXT DEFAULT 'muscle_gain',
                diet TEXT DEFAULT 'Plant-Based / Vegetarian',
                protein_target INTEGER DEFAULT 94,
                routine TEXT DEFAULT 'Standard Day',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Day Logs (Daily Health Engine Scores & Inputs)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS day_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                workout_done INTEGER DEFAULT 1,
                workout_split TEXT DEFAULT 'Push',
                sleep_hours REAL DEFAULT 7.5,
                sleep_feeling INTEGER DEFAULT 2,
                stress_level TEXT DEFAULT 'Low',
                meditation_done INTEGER DEFAULT 1,
                soreness_level TEXT DEFAULT 'None',
                habit_acv INTEGER DEFAULT 1,
                habit_seeds INTEGER DEFAULT 1,
                habit_fasting INTEGER DEFAULT 1,
                score INTEGER DEFAULT 80,
                yesterday_score INTEGER DEFAULT 74,
                delta INTEGER DEFAULT 6,
                readiness_pct INTEGER DEFAULT 85,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE (user_id, date)
            )
        """)

        # Workout Sets
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workout_sets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                split TEXT NOT NULL,
                exercise_name TEXT NOT NULL,
                set_num INTEGER NOT NULL,
                weight REAL NOT NULL,
                reps INTEGER NOT NULL,
                est_1rm REAL NOT NULL,
                is_pr INTEGER DEFAULT 0,
                pr_type TEXT DEFAULT 'none',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)

        # Meals
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS meals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                text TEXT NOT NULL,
                calories INTEGER DEFAULT 0,
                protein INTEGER DEFAULT 0,
                fiber INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)

        # Exercise Historical Strength Milestones (for Chart.js strength curves)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS strength_milestones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                exercise_key TEXT NOT NULL,
                week_label TEXT NOT NULL,
                working_weight REAL NOT NULL,
                reps INTEGER NOT NULL,
                est_1rm REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)

        # Seed initial demo user if empty
        cursor.execute("SELECT id FROM users WHERE email = 'alex@example.com'")
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO users (name, email, password_hash, age, height, weight, goal, diet, protein_target, routine)
                VALUES ('Alex Rivera', 'alex@example.com', 'demo_hash_123', 32, 185, 67.0, 'muscle_gain', 'Plant-Based / Vegetarian', 94, 'Late Shift (1:00 PM – 10:00 PM)')
            """)
            user_id = cursor.lastrowid

            # Seed demo strength milestones for Bench Press
            bench_weeks = [
                ("W1 (Oct 4)", 45.0, 6, 54.0),
                ("W2 (Oct 11)", 47.5, 6, 57.0),
                ("W3 (Oct 18)", 47.5, 8, 60.2),
                ("W4 (Oct 25)", 50.0, 7, 61.7),
                ("W5 (Oct 28)", 50.0, 8, 63.3),
                ("W6 (Today)", 52.5, 10, 66.7),
            ]
            for w, weight, reps, one_rm in bench_weeks:
                cursor.execute("""
                    INSERT INTO strength_milestones (user_id, exercise_key, week_label, working_weight, reps, est_1rm)
                    VALUES (?, 'bench', ?, ?, ?, ?)
                """, (user_id, w, weight, reps, one_rm))
