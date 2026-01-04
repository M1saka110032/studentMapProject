from fastapi import FastAPI, HTTPException, UploadFile, File, Form ,Depends
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from models import Student, School ,Achievement,Enrollment
import os
import shutil
from typing import Optional
import json
import requests
from bs4 import BeautifulSoup


PHOTO_DIR = "static/photos"
DEFAULT_PHOTO_PATH = "/static/avatar/default_avatar.png"
os.makedirs(PHOTO_DIR, exist_ok=True)

# 创建数据库表
Base.metadata.create_all(bind=engine)

app = FastAPI()


app.mount("/static", StaticFiles(directory="static"), name="static")

# ------------------------ CORS ------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ------------------------ school ------------------------
@app.post("/schools")
def create_school(
    name: str = Form(...),
    type: str = Form(...),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    state: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    # prevent duplicate schools
    existing = db.query(School).filter(School.name == name).first()
    if existing:
        return {"id": existing.id}

    school = School(
        name=name,
        type=type,
        latitude=latitude,
        longitude=longitude,
        state=state
    )
    db.add(school)
    db.commit()
    db.refresh(school)

    return {"id": school.id}

@app.get("/schools")
def get_schools(db: Session = Depends(get_db)):
    schools = db.query(School).all()
    result = []
    for s in schools:
        enrollments = db.query(Enrollment).filter(Enrollment.school_id == s.id).all()
        total_students = len(enrollments)
        current_students = sum(1 for e in enrollments if e.status == "current")
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
def get_school_detail(school_id: int,db: Session = Depends(get_db)):
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        raise HTTPException(status_code=404, detail="School not found")

    enrollments = db.query(Enrollment).filter(Enrollment.school_id == school_id).all()
    students = []
    for e in enrollments:
        st = e.student
        students.append({
        "id": st.id,
        "name": st.name,
        "age": st.age,
        "grade": st.grade,
        "status": e.status,
        "start_year": e.start_year,
        "end_year": e.end_year
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
def get_student_detail(student_id: int, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # 返回学生信息
    student_data = {
        "id": student.id,
        "name": student.name,
        "age": student.age,
        "grade": student.grade,
        "photo_path": student.photo_path if student.photo_path else DEFAULT_PHOTO_PATH
    }

    # 返回学校信息（可能是多个）
    enrollments = db.query(Enrollment).filter(Enrollment.student_id == student.id).all()
    schools_data = []
    for e in enrollments:
        school = db.query(School).filter(School.id == e.school_id).first()
        if school:
            schools_data.append({
                "id": school.id,
                "name": school.name,
                "status": e.status,
                "start_year": e.start_year,
                "end_year": e.end_year
            })

    # 返回成就
    achievements_data = [{"id": a.id, "title": a.title} for a in student.achievements]

    return {
        "student": student_data,
        "schools": schools_data,
        "achievements": achievements_data
    }
# ------------------------ add student ------------------------
@app.post("/students")
async def create_student(
    name: str = Form(...),
    age: int = Form(...),
    grade: str = Form(...),
    photo: UploadFile = File(None),
    achievements: Optional[str] = Form(None),
    enrollments: str = Form(...),
    db: Session = Depends(get_db)
):

    # 解析 enrollments
    try:
        enrollment_list = json.loads(enrollments)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid enrollments format")

    if not enrollment_list:
        raise HTTPException(status_code=400, detail="At least one enrollment is required")

    # 修复点2: 先创建学生，不依赖 school_id
    student = Student(
        name=name,
        age=age,
        grade=grade,
    )
    db.add(student)
    db.commit()
    db.refresh(student)

    # 保存 enrollments
    for e in enrollment_list:
        if not e.get("schoolId"):
            raise HTTPException(status_code=400, detail="Each enrollment must have schoolId")
        db.add(Enrollment(
            student_id=student.id,
            school_id=e["schoolId"],
            status=e.get("status", "current"),
            start_year=int(e.get("startYear")),
            end_year=int(e.get("endYear")) if e.get("endYear") else None
        ))
    db.commit()

    # 保存 achievements
    if achievements:
        try:
            achievement_list = json.loads(achievements)
        except:
            achievement_list = []

        for a in achievement_list:
            db.add(Achievement(
                student_id=student.id,
                title=a["title"]
            ))
        db.commit()

    # 保存 photo
    if photo and photo.filename:
        os.makedirs(PHOTO_DIR, exist_ok=True)
        photo_filename = f"{student.id}_{photo.filename}"
        file_path = os.path.join(PHOTO_DIR, photo_filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(photo.file, buffer)
        student.photo_path = f"/static/photos/{photo_filename}"
    else:
        student.photo_path = DEFAULT_PHOTO_PATH
    db.commit()
    return {"id": student.id}

# ------------------------ edit student ------------------------
@app.put("/students/{student_id}")
async def update_student(
    student_id: int,
    name: str = Form(...),
    age: int = Form(...),
    grade: str = Form(...),
    photo: UploadFile = File(None),
    achievements: Optional[str] = Form(None),
    enrollments: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    student.name = name
    student.age = age
    student.grade = grade

    # 更新 enrollments
    if enrollments:
        # 删除旧 enrollments
        db.query(Enrollment).filter(Enrollment.student_id == student_id).delete()
        enrollment_list = json.loads(enrollments)
        for e in enrollment_list:
            if not e.get("schoolId"):
                raise HTTPException(status_code=400, detail="Each enrollment must have schoolId")
            db.add(Enrollment(
                student_id=student_id,
                school_id=e["schoolId"],
                status=e.get("status", "current"),
                start_year=int(e.get("startYear")),
                end_year=int(e.get("endYear")) if e.get("endYear") else None
            ))

    # 更新 achievements
    db.query(Achievement).filter(Achievement.student_id == student_id).delete()
    if achievements:
        try:
            achievement_list = json.loads(achievements)
        except:
            achievement_list = []

        for a in achievement_list:
            db.add(Achievement(
                student_id=student_id,
                title=a["title"]
            ))

    # 更新 photo
    if photo and photo.filename:
        # 删除旧文件
        if student.photo_path and student.photo_path.startswith("/static/"):
            old_path = student.photo_path.lstrip("/")
            if os.path.exists(old_path):
                os.remove(old_path)
        # 保存新图片
        photo_filename = f"{student.id}_{name}_{photo.filename}"
        file_path = os.path.join(PHOTO_DIR, photo_filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(photo.file, buffer)
        student.photo_path = f"/static/photos/{photo_filename}"

    db.commit()
    db.refresh(student)
    return {"id": student.id}

# ------------------------ search school ------------------------
@app.get("/search")
def search(q: str,db: Session = Depends(get_db)):
    
    try:
        schools = db.query(School).filter(School.name.ilike(f"%{q}%")).all()
        students = db.query(Student).filter(Student.name.ilike(f"%{q}%")).all()
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    
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


@app.get("/students/{student_id}/achievements")
def get_student_achievements(
    student_id: int,
    db: Session = Depends(get_db)
):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    return [
        {
            "id": a.id,
            "title": a.title,
        }
        for a in student.achievements
    ]


from pydantic import BaseModel

class AchievementCreate(BaseModel):
    title: str
    description: str | None = None


@app.post("/students/{student_id}/achievements")
def create_achievement(
    student_id: int,
    achievement: AchievementCreate,
    db: Session = Depends(get_db)
):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    new_achievement = Achievement(
        student_id=student_id,
        title=achievement.title,
    )

    db.add(new_achievement)
    db.commit()
    db.refresh(new_achievement)

    return {
        "id": new_achievement.id,
        "title": new_achievement.title,
    }


@app.delete("/achievements/{achievement_id}")
def delete_achievement(
    achievement_id: int,
    db: Session = Depends(get_db)
):
    achievement = db.query(Achievement).filter(
        Achievement.id == achievement_id
    ).first()

    if not achievement:
        raise HTTPException(status_code=404, detail="Achievement not found")

    db.delete(achievement)
    db.commit()

    return {"message": "Achievement deleted successfully"}



@app.post("/schools/{school_id}/detect-website")
def detect_school_website(
    school_id: int,
    db: Session = Depends(get_db)
):
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        raise HTTPException(status_code=404, detail="School not found")

    if getattr(school, "website", None):
        return {"website": school.website}

    query = f"{school.name} official website"
    url = f"https://duckduckgo.com/html/?q={query}"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    r = requests.get(url, headers=headers, timeout=10)
    soup = BeautifulSoup(r.text, "html.parser")

    for a in soup.select("a.result__a"):
        href = a.get("href")
        if href and href.startswith("http"):
            school.website = href
            db.commit()
            return {"website": href}

    return {"website": None}

app.mount("/", StaticFiles(directory="static", html=True), name="static")

