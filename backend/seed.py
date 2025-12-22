import sqlite3

DB_NAME = "database.db"

def seed():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # --- Schools ---
    schools = [
        ("Harvard University", "university", 42.3770, -71.1167, "https://www.harvard.edu"),
        ("MIT", "university", 42.3601, -71.0942, "https://www.mit.edu"),
        ("Boston High School", "highschool", 42.3605, -71.0590, "https://bostonpublicschools.org"),
        ("Cambridge High School", "highschool", 42.3732, -71.1190, "https://cambridgepublicschools.org"),
    ]

    cursor.executemany("""
        INSERT INTO schools (name, type, latitude, longitude, website)
        VALUES (?, ?, ?, ?, ?)
    """, schools)

    # --- Students ---
    students = [
        ("Alice", 18, "12th Grade"),
        ("Bob", 20, "College Sophomore"),
        ("Charlie", 17, "11th Grade"),
        ("David", 22, "College Senior"),
        ("Eve", 16, "10th Grade"),
        ("Frank", 19, "College Freshman"),
    ]

    cursor.executemany("""
        INSERT INTO students (name, age, grade)
        VALUES (?, ?, ?)
    """, students)

    # --- Enrollments ---
    enrollments = [
        # Alice
        (1, 3, "current", 2022, None), # Boston High School
        # Bob
        (2, 1, "current", 2021, None), # Harvard
        (2, 4, "past", 2017, 2020),    # Cambridge High
        # Charlie
        (3, 4, "current", 2022, None), # Cambridge High
        # David
        (4, 2, "current", 2019, None), # MIT
        # Eve
        (5, 3, "current", 2023, None), # Boston High
        # Frank
        (6, 1, "current", 2023, None), # Harvard
    ]

    cursor.executemany("""
        INSERT INTO enrollments (student_id, school_id, status, start_year, end_year)
        VALUES (?, ?, ?, ?, ?)
    """, enrollments)

    conn.commit()
    conn.close()
    print("Database seeded successfully!")

if __name__ == "__main__":
    seed()
