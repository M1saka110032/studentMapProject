import sqlite3

DB_NAME = "database.db"

def create_tables():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Students table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        age INTEGER,
        grade TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Schools table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS schools (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        type TEXT CHECK(type IN ('highschool', 'university')) NOT NULL,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        website TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Enrollments table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS enrollments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        school_id INTEGER NOT NULL,
        status TEXT CHECK(status IN ('past', 'current')) NOT NULL,
        start_year INTEGER,
        end_year INTEGER,
        FOREIGN KEY(student_id) REFERENCES students(id),
        FOREIGN KEY(school_id) REFERENCES schools(id)
    );
    """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_tables()
