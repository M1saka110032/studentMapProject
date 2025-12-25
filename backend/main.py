from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from models import Student, School
import os
import shutil

# 创建数据库表
Base.metadata.create_all(bind=engine)

app = FastAPI()

# ------------------------ CORS ------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------ save photo ------------------------
PHOTO_DIR = "photos"
os.makedirs(PHOTO_DIR, exist_ok=True)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ------------------------ school ------------------------
@app.get("/schools")
def get_schools():
    db: Session = next(get_db())
    schools = db.query(School).all()
    result = []
    for s in schools:
        total_students = len(s.students)
        current_students = sum(1 for st in s.students if getattr(st, "status", "current") == "current")
        result.append({
            "id": s.id,
            "name": s.name,
            "type": s.type,
            "latitude": s.latitude,
            "longitude": s.longitude,
            "state": getattr(s, "state", ""),
            "total_students": total_students,
            "current_students": current_students
        })
    return result

@app.get("/schools/{school_id}")
def get_school_detail(school_id: int):
    db: Session = next(get_db())
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        raise HTTPException(status_code=404, detail="School not found")

    students = []
    for st in school.students:
        students.append({
            "id": st.id,
            "name": st.name,
            "age": st.age,
            "grade": st.grade,
            "photo_path": st.photo_path,
            "status": getattr(st, "status", "current"),
            "start_year": getattr(st, "start_year", None),
            "end_year": getattr(st, "end_year", None)
        })

    return {
        "school": {
            "id": school.id,
            "name": school.name,
            "type": school.type,
            "latitude": school.latitude,
            "longitude": school.longitude,
            "state": getattr(school, "state", ""),
        },
        "students": students
    }

# ------------------------ student ------------------------
@app.get("/students/{student_id}")
def get_student_detail(student_id: int):
    db: Session = next(get_db())
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    school_info = None
    if student.school:
        school_info = {
            "id": student.school.id,
            "name": student.school.name,
            "type": student.school.type
        }

    return {
        "student": {
            "id": student.id,
            "name": student.name,
            "age": student.age,
            "grade": student.grade,
            "photo_path": student.photo_path
        },
        "school": school_info
    }

# ------------------------ add student ------------------------
@app.post("/students")
async def create_student(
    name: str = Form(...),
    age: int = Form(...),
    grade: str = Form(...),
    status: str = Form(...),
    school_id: int = Form(...),
    photo: UploadFile = File(None)
):
    db: Session = next(get_db())
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        raise HTTPException(status_code=404, detail="School not found")

    # save photo
    photo_path = None
    if photo:
        photo_filename = f"{school_id}_{name}_{photo.filename}"
        photo_path = os.path.join(PHOTO_DIR, photo_filename)
        with open(photo_path, "wb") as buffer:
            shutil.copyfileobj(photo.file, buffer)

    student = Student(
        name=name,
        age=age,
        grade=grade,
        status=status,
        school_id=school_id,
        photo_path=photo_path
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    return {"id": student.id}

# ------------------------ edit student ------------------------
@app.put("/students/{student_id}")
async def update_student(
    student_id: int,
    name: str = Form(...),
    age: int = Form(...),
    grade: str = Form(...),
    status: str = Form(...),
    school_id: int = Form(...),
    photo: UploadFile = File(None)
):
    db: Session = next(get_db())
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    student.name = name
    student.age = age
    student.grade = grade
    student.status = status
    student.school_id = school_id

    # update photo
    if photo:
        if student.photo_path and os.path.exists(student.photo_path):
            os.remove(student.photo_path)
        photo_filename = f"{school_id}_{name}_{photo.filename}"
        photo_path = os.path.join(PHOTO_DIR, photo_filename)
        with open(photo_path, "wb") as buffer:
            shutil.copyfileobj(photo.file, buffer)
        student.photo_path = photo_path

    db.commit()
    db.refresh(student)
    return {"id": student.id}

# ------------------------ search school ------------------------
@app.get("/search")
def search(q: str):
    db: Session = next(get_db())
    
    schools = db.query(School).filter(School.name.ilike(f"%{q}%")).all()
    students = db.query(Student).filter(Student.name.ilike(f"%{q}%")).all()

    school_results = [
        {
            "id": s.id,
            "name": s.name,
            "type": "school",
            "state": getattr(s, "state", ""),
            "latitude": s.latitude,
            "longitude": s.longitude
        } for s in schools
    ]

    student_results = [
        {"id": s.id, "name": s.name, "type": "student"} for s in students
    ]

    return school_results + student_results