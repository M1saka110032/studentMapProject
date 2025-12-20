import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS schools (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    type TEXT,
    latitude REAL,
    longitude REAL,
    website TEXT,
    current_students INTEGER,
    historical_students INTEGER
)
""")

cursor.execute("""
INSERT INTO schools
(name, type, latitude, longitude, website, current_students, historical_students)
VALUES
('Harvard University', 'university', 42.3770, -71.1167,
 'https://www.harvard.edu', 12, 30),
('Boston High School', 'highschool', 42.3601, -71.0589,
 'https://bostonpublicschools.org', 0, 15)
""")

conn.commit()
conn.close()
