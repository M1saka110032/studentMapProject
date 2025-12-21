from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
from models import create_tables

# 1️⃣ Create FastAPI app
app = FastAPI()

# 2️⃣ Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # allow any origin (development)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3️⃣ Database name
DB_NAME = "database.db"

# 4️⃣ Ensure tables exist
create_tables()

# 5️⃣ List all schools
@app.get("/schools")
def get_schools():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT
        s.id,
        s.name,
        s.type,
        s.latitude,
        s.longitude,
        COUNT(e.id) AS total_students,
        COALESCE(SUM(CASE WHEN e.status = 'current' THEN 1 ELSE 0 END), 0) AS current_students
    FROM schools s
    LEFT JOIN enrollments e ON s.id = e.school_id
    GROUP BY s.id;
    """)

    rows = cursor.fetchall()
    conn.close()

    schools = []
    for r in rows:
        schools.append({
            "id": r[0],
            "name": r[1],
            "type": r[2],
            "latitude": r[3],
            "longitude": r[4],
            "total_students": r[5],
            "current_students": r[6]
        })

    return schools

# 6️⃣ School detail endpoint
@app.get("/schools/{school_id}")
def get_school_detail(school_id: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 6a. Get school info
    cursor.execute("""
    SELECT id, name, type, latitude, longitude, website
    FROM schools
    WHERE id = ?
    """, (school_id,))

    school = cursor.fetchone()

    if school is None:
        conn.close()
        raise HTTPException(status_code=404, detail="School not found")

    # 6b. Get students in this school
    cursor.execute("""
    SELECT
        s.id,
        s.name,
        s.age,
        s.grade,
        e.status,
        e.start_year,
        e.end_year
    FROM enrollments e
    JOIN students s ON e.student_id = s.id
    WHERE e.school_id = ?
    """, (school_id,))

    students_rows = cursor.fetchall()
    conn.close()

    students = []
    for r in students_rows:
        students.append({
            "id": r[0],
            "name": r[1],
            "age": r[2],
            "grade": r[3],
            "status": r[4],
            "start_year": r[5],
            "end_year": r[6]
        })

    return {
        "school": {
            "id": school[0],
            "name": school[1],
            "type": school[2],
            "latitude": school[3],
            "longitude": school[4],
            "website": school[5]
        },
        "students": students
    }
