import sqlite3

# Define target data storage file link
DATABASE_NAME = "church_v3.db"

conn = sqlite3.connect(DATABASE_NAME)
cur = conn.cursor()

print(f"Initializing connection layout structures for '{DATABASE_NAME}'...")

# 1. Main Church Schools Roster Table
cur.execute("""
CREATE TABLE IF NOT EXISTS church_schools (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    church_name TEXT NOT NULL,
    place TEXT NOT NULL,
    council TEXT NOT NULL,
    headquarters_branch TEXT NOT NULL,
    alphabet_key TEXT NOT NULL,
    num_teachers INTEGER DEFAULT 0,
    teacher_names TEXT,
    amount_due INTEGER DEFAULT 0,
    payment_status TEXT DEFAULT 'No',
    lkg_id TEXT, lkg_name TEXT,
    ukg_id TEXT, ukg_name TEXT,
    std1_id TEXT, std1_name TEXT,
    std2_id TEXT, std2_name TEXT,
    std3_id TEXT, std3_name TEXT,
    std4_id TEXT, std4_name TEXT,
    std5_id TEXT, std5_name TEXT,
    std6_id TEXT, std6_name TEXT,
    std7_id TEXT, std7_name TEXT,
    std8_id TEXT, std8_name TEXT,
    std9_id TEXT, std9_name TEXT,
    std10_id TEXT, std10_name TEXT,
    std11_id TEXT, std11_name TEXT,
    std12_id TEXT, std12_name TEXT
)
""")

# 2. Performance Tracking Matrix Results Table
cur.execute("""
CREATE TABLE IF NOT EXISTS competition_results (
    result_id INTEGER PRIMARY KEY AUTOINCREMENT,
    council TEXT NOT NULL,
    headquarters_branch TEXT NOT NULL,
    standard TEXT NOT NULL,
    prize_position TEXT NOT NULL,
    participant_id TEXT NOT NULL,
    participant_name TEXT NOT NULL,
    church_name TEXT NOT NULL,
    place TEXT NOT NULL
)
""")

conn.commit()
conn.close()

print(f"SUCCESS: System core database schema configured on '{DATABASE_NAME}' successfully!")