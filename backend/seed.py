import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

cursor.execute("""
INSERT INTO schools (name, type, latitude, longitude, website)
VALUES
('Harvard University', 'university', 42.3770, -71.1167, 'https://www.harvard.edu'),
('Boston High School', 'highschool', 42.3601, -71.0589, 'https://bostonpublicschools.org')
""")

conn.commit()
conn.close()
