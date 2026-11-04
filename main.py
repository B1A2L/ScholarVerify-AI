import os
from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from backend.db import engine, Base, get_db
from backend.models import User, UserRole, Scholarship, Application, ApplicationStatus, Document
from backend.auth import create_access_token, authenticate_user, role_required, get_current_active_user
from backend.routers import auth as auth_router, scholarship as scholarship_router, application as application_router, officer as officer_router

app = FastAPI(title="ScholarVerify AI Demo Backend")

# CORS – allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create tables
Base.metadata.create_all(bind=engine)

# Seed demo data if not present
def seed_data(db: Session):
    # Users
    if not db.query(User).filter(User.username == "student1").first():
        from backend.auth import get_password_hash
        db.add(
            User(
                username="student1",
                hashed_password=get_password_hash("studentpw"),
                role=UserRole.student,
                full_name="Demo Student",
            )
        )
    if not db.query(User).filter(User.username == "admin1").first():
        from backend.auth import get_password_hash
        db.add(
            User(
                username="admin1",
                hashed_password=get_password_hash("adminpw"),
                role=UserRole.admin,
                full_name="Demo Admin",
            )
        )
    if not db.query(User).filter(User.username == "officer1").first():
        from backend.auth import get_password_hash
        db.add(
            User(
                username="officer1",
                hashed_password=get_password_hash("officerpw"),
                role=UserRole.officer,
                full_name="Dr. Rajesh Kumar (Senior Officer)",
            )
        )
    if not db.query(User).filter(User.username == "officer2").first():
        from backend.auth import get_password_hash
        db.add(
            User(
                username="officer2",
                hashed_password=get_password_hash("officerpw"),
                role=UserRole.officer,
                full_name="Priya Sharma (Verification Officer)",
            )
        )
    # Scholarships
    if not db.query(Scholarship).filter(Scholarship.name == "Demo Scholarship").first():
        db.add(
            Scholarship(
                name="Merit-cum-Means Technical Scholarship",
                description="Financial support for meritorious engineering and science students from low-income families.",
                max_income=250000,
                min_marks=75,
            )
        )
    if not db.query(Scholarship).filter(Scholarship.name == "National Post-Matric Scholarship").first():
        db.add(
            Scholarship(
                name="National Post-Matric Scholarship",
                description="Government scholarship to enable economically disadvantaged students to pursue post-secondary education.",
                max_income=200000,
                min_marks=60,
            )
        )
    db.commit()

@app.on_event("startup")
def startup_event():
    with Session(bind=engine) as db:
        seed_data(db)

# Register routers
app.include_router(auth_router.router, prefix="/api/auth", tags=["auth"])
app.include_router(scholarship_router.router, prefix="/api/scholarships", tags=["scholarships"])
app.include_router(application_router.router, prefix="/api/applications", tags=["applications"])
app.include_router(officer_router.router, prefix="/api/officer", tags=["officer"])

# Simple health check
@app.get("/health")
def health():
    return {"status": "ok"}

# File upload endpoint – used by application router but also stand‑alone for demo
@app.post("/api/upload", dependencies=[Depends(role_required(UserRole.student))])
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    uploads_dir = os.getenv("UPLOADS_DIR", "uploads")
    os.makedirs(uploads_dir, exist_ok=True)
    file_path = os.path.join(uploads_dir, file.filename)
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    return {"filename": file.filename, "path": file_path}

