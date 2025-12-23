from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
from models import create_tables

# Create FastAPI app
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # allow any origin (development)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database name
DB_NAME = "database.db"

# Ensure tables exist
create_tables()

# List all schools
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
        s.website,
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
            "website": r[5],
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

@app.get("/students/{student_id}")
def get_student_detail(student_id: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Student basic info
    cursor.execute("""
    SELECT id, name, age, grade
    FROM students
    WHERE id = ?
    """, (student_id,))
    student = cursor.fetchone()

    if student is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Student not found")

    # Schools this student attended
    cursor.execute("""
    SELECT
        s.id,
        s.name,
        s.type,
        e.status,
        e.start_year,
        e.end_year
    FROM enrollments e
    JOIN schools s ON e.school_id = s.id
    WHERE e.student_id = ?
    """, (student_id,))

    schools = cursor.fetchall()
    conn.close()

    return {
        "student": {
            "id": student[0],
            "name": student[1],
            "age": student[2],
            "grade": student[3]
        },
        "schools": [
            {
                "id": r[0],
                "name": r[1],
                "type": r[2],
                "status": r[3],
                "start_year": r[4],
                "end_year": r[5]
            } for r in schools
        ]
    }

@app.get("/search")
def search(q: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Search schools
    cursor.execute("""
    SELECT id, name
    FROM schools
    WHERE name LIKE ?
    """, (f"%{q}%",))

    schools = [
        {"id": r[0], "name": r[1], "type": "school"}
        for r in cursor.fetchall()
    ]

    # Search students
    cursor.execute("""
    SELECT id, name
    FROM students
    WHERE name LIKE ?
    """, (f"%{q}%",))

    students = [
        {"id": r[0], "name": r[1], "type": "student"}
        for r in cursor.fetchall()
    ]

    conn.close()

    return schools + students
