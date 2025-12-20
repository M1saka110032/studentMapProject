from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sqlite3

app = FastAPI()

# Allow frontend to access backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    return sqlite3.connect("database.db")

@app.get("/api/schools")
def get_schools():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, type, latitude, longitude, website,
               current_students, historical_students
        FROM schools
    """)
    rows = cursor.fetchall()
    conn.close()

    schools = []
    for r in rows:
        schools.append({
            "id": r[0],
            "name": r[1],
            "type": r[2],
            "lat": r[3],
            "lng": r[4],
            "website": r[5],
            "current_students": r[6],
            "historical_students": r[7]
        })

    return schools
