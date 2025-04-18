from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from fastapi import Security


from auth.mail import send_email
from db.database import SessionLocal
from models.class_fee_model import ClassFeeStructure
from models.student_fee_payment_model import StudentFeePayment
from models.teacher_salary_model import TeacherSalary
from models.user_model import User
from models.teacher_model import Teacher
from models.student_model import Student
from schemas.class_fee_schema import ClassFeeCreateUpdate
from schemas.fee_payment_schema import FeePaymentUpdate, StudentFeeStatus
from schemas.reminder_schema import ReminderRequest
from schemas.salary_schema import SetSalary
from schemas.user_schema import UserCreate, UserLogin
from schemas.teacher_schema import TeacherCreate
from schemas.student_schema import StudentCreate
from models.class_model import ClassSection
from schemas.class_schema import ClassSectionCreate
from models.subject_model import Subject
from schemas.subject_schema import SubjectCreate
from models.teacher_class_map_model import TeacherClassMap
from schemas.teacher_class_schema import AssignTeacherClasses


from auth.auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    decode_token
)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

router = APIRouter()


# Dependency: Get DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Dependency: Principal Auth
def get_current_principal(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = decode_token(token)
    if not payload or payload["role"] != "PRINCIPAL":
        raise HTTPException(status_code=401, detail="Unauthorized")
    user = db.query(User).filter(User.id == payload["id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="Principal not found")
    return user

# Dependency: Teacher Auth
def get_current_teacher(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = decode_token(token)
    if not payload or payload["role"] != "TEACHER":
        raise HTTPException(status_code=401, detail="Unauthorized")
    user = db.query(Teacher).filter(Teacher.id == payload["id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="Teacher not found")
    return user

# ----------------------- Principal Routes -----------------------

@router.post("/principal/signup")
def principal_signup(data: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed = get_password_hash(data.password)
    user = User(name=data.name, email=data.email, password=hashed, role="PRINCIPAL")
    db.add(user)
    db.commit()
    return {"message": "Principal account created successfully"}

@router.post("/principal/login")
def principal_login(data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email, User.role == "PRINCIPAL").first()
    if not user or not verify_password(data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"id": user.id, "role": "PRINCIPAL"})
    return {"access_token": token, "token_type": "bearer"}

@router.post("/principal/create-class")
def create_class(data: ClassSectionCreate, db: Session = Depends(get_db), principal=Depends(get_current_principal)):
    existing = db.query(ClassSection).filter(
        ClassSection.class_name == data.class_name,
        ClassSection.section == data.section
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Class-section already exists")
    cs = ClassSection(class_name=data.class_name, section=data.section)
    db.add(cs)
    db.commit()
    return {"message": "Class-section created", "id": cs.id}

@router.post("/principal/add-teacher")
def add_teacher(data: TeacherCreate, db: Session = Depends(get_db), principal=Depends(get_current_principal)):
    if db.query(Teacher).filter(Teacher.email == data.email).first():
        raise HTTPException(status_code=400, detail="Teacher already exists")

    class_section = db.query(ClassSection).filter(ClassSection.id == data.class_section_id).first()
    if not class_section:
        raise HTTPException(status_code=404, detail="Class-section not found")

    teacher = Teacher(
        name=data.name,
        email=data.email,
        password=get_password_hash(data.password),
        class_section_id=data.class_section_id,
        created_by=principal.id
    )
    db.add(teacher)
    db.commit()
    return {"message": "Teacher added successfully"}


@router.post("/principal/set-fee")
def set_or_update_class_fee(data: ClassFeeCreateUpdate, db: Session = Depends(get_db), principal=Depends(get_current_principal)):
    existing = db.query(ClassFeeStructure).filter(ClassFeeStructure.class_section_id == data.class_section_id).first()
    
    if existing:
        existing.tuition_fee = data.tuition_fee
        existing.exam_fee = data.exam_fee
        existing.library_fee = data.library_fee
        existing.transport_fee = data.transport_fee
        db.commit()
        return {"message": "Class fee updated successfully"}
    
    new_fee = ClassFeeStructure(
        class_section_id=data.class_section_id,
        tuition_fee=data.tuition_fee,
        exam_fee=data.exam_fee,
        library_fee=data.library_fee,
        transport_fee=data.transport_fee
    )
    db.add(new_fee)
    db.commit()
    return {"message": "Class fee set successfully"}

@router.get("/principal/class/{class_id}/fee")
def get_class_fee(class_id: int, db: Session = Depends(get_db), principal=Depends(get_current_principal)):
    fee = db.query(ClassFeeStructure).filter(ClassFeeStructure.class_section_id == class_id).first()
    if not fee:
        raise HTTPException(status_code=404, detail="Fee structure not found")
    return {
        "class_section_id": fee.class_section_id,
        "tuition_fee": fee.tuition_fee,
        "exam_fee": fee.exam_fee,
        "library_fee": fee.library_fee,
        "transport_fee": fee.transport_fee,
        "total": fee.tuition_fee + fee.exam_fee + fee.library_fee + fee.transport_fee
    }


@router.post("/principal/reminder/{class_section_id}")
def send_reminder_by_path(
    class_section_id: int,
    month: str = Query(default=None),
    db: Session = Depends(get_db),
    principal=Depends(get_current_principal)
):
    students = db.query(Student).filter(Student.class_section_id == class_section_id).all()
    if not students:
        raise HTTPException(status_code=404, detail="No students in this class")

    success = 0
    failed = 0
    logs = []

    for s in students:
        if send_email(s.email, s.name, s.class_name, month=month):
            success += 1
            logs.append(f"✅ Sent to {s.name} ({s.email})")
        else:
            failed += 1
            logs.append(f"❌ Failed to send to {s.name} ({s.email})")

    return {
        "total": len(students),
        "sent": success,
        "failed": failed,
        "details": logs
    }

@router.get("/principal/pending-fees/{class_section_id}")
def get_pending_fee_students(
    class_section_id: int,
    db: Session = Depends(get_db),
    principal=Depends(get_current_principal)
):
    # Get all students in the class
    students = db.query(Student).filter(Student.class_section_id == class_section_id).all()

    if not students:
        raise HTTPException(status_code=404, detail="No students found in this class")

    # Check payment table for each student
    pending_students = []
    for s in students:
        payment = db.query(StudentFeePayment).filter(
            StudentFeePayment.student_id == s.id,
            StudentFeePayment.class_section_id == class_section_id
        ).first()

        if not payment or payment.status != "Paid":
            pending_students.append({
                "student_id": s.id,
                "name": s.name,
                "email": s.email,
                "class": s.class_name,
                "payment_status": payment.status if payment else "Not Paid",
                "paid_amount": payment.paid_amount if payment else 0
            })

    return {
        "class_section_id": class_section_id,
        "pending_count": len(pending_students),
        "students": pending_students
    }


@router.post("/principal/set-salary")
def set_teacher_salary(
    data: SetSalary,
    db: Session = Depends(get_db),
    principal=Depends(get_current_principal)
):
    # Check if teacher exists
    teacher = db.query(Teacher).filter(Teacher.id == data.teacher_id).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")

    # Set or update salary
    salary_record = db.query(TeacherSalary).filter(TeacherSalary.teacher_id == data.teacher_id).first()

    if salary_record:
        salary_record.salary_amount = data.salary_amount
        message = "Salary updated successfully"
    else:
        salary_record = TeacherSalary(
            teacher_id=data.teacher_id,
            salary_amount=data.salary_amount
        )
        db.add(salary_record)
        message = "Salary set successfully"

    db.commit()

    return {
        "teacher_id": data.teacher_id,
        "salary": data.salary_amount,
        "message": message
    }

@router.get("/principal/teacher-salaries")
def view_all_salaries(
    db: Session = Depends(get_db),
    principal=Depends(get_current_principal)
):
    salaries = db.query(TeacherSalary).all()

    result = []
    for s in salaries:
        teacher = db.query(Teacher).filter(Teacher.id == s.teacher_id).first()
        if teacher:
            result.append({
                "teacher_id": s.teacher_id,
                "name": teacher.name,
                "email": teacher.email,
                "salary": s.salary_amount
            })

    return {
        "total_teachers": len(result),
        "salaries": result
    }

@router.get("/principal/me")
def get_principal_profile(
    principal=Depends(get_current_principal)
):
    return {
        "id": principal.id,
        "name": principal.name,
        "email": principal.email,
        "role": principal.role
    }



# ----------------------- Teacher Routes -----------------------

@router.post("/teacher/login")
def teacher_login(data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(Teacher).filter(Teacher.email == data.email).first()
    if not user or not verify_password(data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"id": user.id, "role": "TEACHER"})
    return {"access_token": token, "token_type": "bearer"}

@router.post("/teacher/add-student")
def add_student(
    data: StudentCreate,
    db: Session = Depends(get_db),
    token: str = Security(oauth2_scheme)
):
    payload = decode_token(token)
    if not payload or payload["role"] != "TEACHER":
        raise HTTPException(status_code=401, detail="Unauthorized")

    teacher = db.query(Teacher).filter(Teacher.id == payload["id"]).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")

    if db.query(Student).filter(Student.email == data.email).first():
        raise HTTPException(status_code=400, detail="Student already exists")

    student = Student(
    name=data.name,
    email=data.email,
    password=get_password_hash(data.password),
    age=data.age,
    gender=data.gender,
    class_name=data.class_name,
    class_section_id=data.class_section_id,  # ✅ this must be added!
    created_by=teacher.id
)
    db.add(student)
    db.commit()
    return {"message": "Student added successfully"}

@router.post("/student/login")
def student_login(data: UserLogin, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.email == data.email).first()  # ✅ Fix here
    if not student or not verify_password(data.password, student.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"id": student.id, "role": "STUDENT"})
    return {"access_token": token, "token_type": "bearer"}

@router.post("/teacher/add-subject")
def add_subject(data: SubjectCreate, db: Session = Depends(get_db), teacher=Depends(get_current_teacher)):
    # Check if class-section exists
    class_section = db.query(ClassSection).filter(ClassSection.id == data.class_section_id).first()
    if not class_section:
        raise HTTPException(status_code=404, detail="Class-section not found")

    # Optional: Prevent duplicate subject
    existing = db.query(Subject).filter(
        Subject.subject_name == data.subject_name,
        Subject.class_section_id == data.class_section_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Subject already exists for this class-section")

    subject = Subject(
        subject_name=data.subject_name,
        class_section_id=data.class_section_id,
        created_by=teacher.id
    )
    db.add(subject)
    db.commit()
    return {"message": "Subject added successfully"}

@router.post("/principal/assign-teacher-to-classes")
def assign_teacher_to_classes(
    data: AssignTeacherClasses,
    db: Session = Depends(get_db),
    principal=Depends(get_current_principal)
):
    assigned = []
    for cs_id in data.class_section_ids:
        exists = db.query(TeacherClassMap).filter(
            TeacherClassMap.teacher_id == data.teacher_id,
            TeacherClassMap.class_section_id == cs_id
        ).first()
        if not exists:
            mapping = TeacherClassMap(
                teacher_id=data.teacher_id,
                class_section_id=cs_id
            )
            db.add(mapping)
            assigned.append(cs_id)
    db.commit()
    return {
        "message": "Teacher assigned to classes successfully",
        "assigned_class_section_ids": assigned
    }

@router.post("/principal/mark-payment")
def mark_payment(
    data: StudentFeeStatus,
    db: Session = Depends(get_db),
    principal=Depends(get_current_principal)
):
    payment = db.query(StudentFeePayment).filter(
        StudentFeePayment.student_id == data.student_id,
        StudentFeePayment.class_section_id == data.class_section_id
    ).first()

    if payment:
        payment.paid_amount = data.paid_amount
        payment.status = data.status
    else:
        payment = StudentFeePayment(
            student_id=data.student_id,
            class_section_id=data.class_section_id,
            paid_amount=data.paid_amount,
            status=data.status
        )
        db.add(payment)
    db.commit()
    return {"message": "Payment updated"}


@router.get("/stats/students/count")
def total_students(db: Session = Depends(get_db)):
    count = db.query(Student).count()
    return {"total_students": count}

@router.get("/stats/teachers/count")
def total_teachers(db: Session = Depends(get_db)):
    count = db.query(Teacher).count()
    return {"total_teachers": count}

@router.get("/stats/subjects/count")
def total_subjects(db: Session = Depends(get_db)):
    count = db.query(Subject).count()
    return {"total_subjects": count}

@router.get("/stats/classes/count")
def total_class_sections(db: Session = Depends(get_db)):
    count = db.query(ClassSection).count()
    return {"total_class_sections": count}

@router.get("/classes/all")
def list_classes(db: Session = Depends(get_db)):
    classes = db.query(ClassSection).all()
    return [{"id": c.id, "class": c.class_name, "section": c.section} for c in classes]

@router.get("/classes/{class_id}/subjects")
def get_subjects_by_class(class_id: int, db: Session = Depends(get_db)):
    subjects = db.query(Subject).filter(Subject.class_section_id == class_id).all()
    return [{"id": s.id, "subject_name": s.subject_name} for s in subjects]

@router.get("/stats/students")
def all_students(db: Session = Depends(get_db)):
    students = db.query(Student).all()
    return {
        "total_students": len(students),
        "students": [
            {
                "id": s.id,
                "name": s.name,
                "email": s.email,
                "age": s.age,
                "gender": s.gender,
                "class": s.class_name
            } for s in students
        ]
    }

@router.get("/stats/teachers")
def all_teachers(db: Session = Depends(get_db)):
    teachers = db.query(Teacher).all()
    return {
        "total_teachers": len(teachers),
        "teachers": [
            {
                "id": t.id,
                "name": t.name,
                "email": t.email,
                "class_section_id": t.class_section_id
            } for t in teachers
        ]
    }

@router.get("/stats/subjects")
def all_subjects(db: Session = Depends(get_db)):
    subjects = db.query(Subject).all()
    return {
        "total_subjects": len(subjects),
        "subjects": [
            {
                "id": s.id,
                "subject_name": s.subject_name,
                "class_section_id": s.class_section_id
            } for s in subjects
        ]
    }

@router.get("/stats/classes")
def all_class_sections(db: Session = Depends(get_db)):
    classes = db.query(ClassSection).all()
    return {
        "total_class_sections": len(classes),
        "classes": [
            {
                "id": c.id,
                "class": c.class_name,
                "section": c.section
            } for c in classes
        ]
    }

@router.get("/teacher/students")
def get_students_by_teacher(db: Session = Depends(get_db), teacher=Depends(get_current_teacher)):
    students = db.query(Student).filter(Student.created_by == teacher.id).all()
    return {
        "teacher_id": teacher.id,
        "total_students": len(students),
        "students": [
            {
                "id": s.id,
                "name": s.name,
                "email": s.email,
                "age": s.age,
                "gender": s.gender,
                "class": s.class_name
            }
            for s in students
        ]
    }

@router.get("/principal/teacher/{teacher_id}/classes")
def get_teacher_assigned_classes(teacher_id: int, db: Session = Depends(get_db), principal=Depends(get_current_principal)):
    mappings = db.query(TeacherClassMap).filter(TeacherClassMap.teacher_id == teacher_id).all()
    result = []
    for m in mappings:
        class_sec = db.query(ClassSection).filter(ClassSection.id == m.class_section_id).first()
        if class_sec:
            result.append({
                "class_section_id": class_sec.id,
                "class": class_sec.class_name,
                "section": class_sec.section
            })

    return {
        "teacher_id": teacher_id,
        "total_classes": len(result),
        "classes": result
    }

@router.get("/teacher/assigned-classes")
def get_my_assigned_classes(
    db: Session = Depends(get_db),
    teacher=Depends(get_current_teacher)
):
    mappings = db.query(TeacherClassMap).filter(TeacherClassMap.teacher_id == teacher.id).all()

    result = []
    for m in mappings:
        class_section = db.query(ClassSection).filter(ClassSection.id == m.class_section_id).first()
        if class_section:
            result.append({
                "class_section_id": class_section.id,
                "class": class_section.class_name,
                "section": class_section.section
            })

    return {
        "teacher_id": teacher.id,
        "teacher_name": teacher.name,
        "total_classes_assigned": len(result),
        "classes": result
    }

@router.get("/student/fee-reminder")
def get_student_fee_reminder(
    token: str = Security(oauth2_scheme),
    db: Session = Depends(get_db)
):
    payload = decode_token(token)
    if not payload or payload["role"] != "STUDENT":
        raise HTTPException(status_code=401, detail="Unauthorized")

    student = db.query(Student).filter(Student.id == payload["id"]).first()
    if not student or not student.class_section_id:
        raise HTTPException(status_code=404, detail="Student not found or not assigned")

    fee = db.query(ClassFeeStructure).filter(ClassFeeStructure.class_section_id == student.class_section_id).first()
    if not fee:
        raise HTTPException(status_code=404, detail="Fee structure not found")

    payment = db.query(StudentFeePayment).filter(
        StudentFeePayment.student_id == student.id,
        StudentFeePayment.class_section_id == student.class_section_id
    ).first()

    return {
        "student_id": student.id,
        "student_name": student.name,
        "class_section_id": student.class_section_id,
        "fee_structure": {
            "tuition_fee": fee.tuition_fee,
            "exam_fee": fee.exam_fee,
            "library_fee": fee.library_fee,
            "transport_fee": fee.transport_fee,
            "total": fee.tuition_fee + fee.exam_fee + fee.library_fee + fee.transport_fee
        },
        "payment_status": {
            "status": payment.status if payment else "Pending",
            "paid_amount": payment.paid_amount if payment else 0
        }
    }

@router.post("/student/pay-fee")
def student_pay_fee(
    data: FeePaymentUpdate,
    token: str = Security(oauth2_scheme),
    db: Session = Depends(get_db)
):
    payload = decode_token(token)
    if not payload or payload["role"] != "STUDENT":
        raise HTTPException(status_code=401, detail="Unauthorized")

    student = db.query(Student).filter(Student.id == payload["id"]).first()
    if not student or not student.class_section_id:
        raise HTTPException(status_code=404, detail="Student not found or class not assigned")

    # Check for existing payment record
    payment = db.query(StudentFeePayment).filter(
        StudentFeePayment.student_id == student.id,
        StudentFeePayment.class_section_id == student.class_section_id
    ).first()

    if payment:
        if payment.status == "Paid":
            raise HTTPException(status_code=400, detail="Fee already paid")
        else:
            payment.paid_amount = data.paid_amount
            payment.status = data.status
    else:
        payment = StudentFeePayment(
            student_id=student.id,
            class_section_id=student.class_section_id,
            paid_amount=data.paid_amount,
            status=data.status
        )
        db.add(payment)

    db.commit()

    return {
        "message": "Payment submitted successfully",
        "student_id": student.id,
        "status": data.status,
        "paid_amount": data.paid_amount
    }

@router.get("/class-section/{id}")
def get_class_section(id: int, db: Session = Depends(get_db)):
    class_section = db.query(ClassSection).filter(ClassSection.id == id).first()
    if not class_section:
        raise HTTPException(status_code=404, detail="Class-section not found")
    
    return {
        "id": class_section.id,
        "class_name": class_section.class_name,
        "section": class_section.section
    }


@router.get("/teacher/me")
def get_teacher_profile(
    teacher=Depends(get_current_teacher)
):
    return {
        "id": teacher.id,
        "name": teacher.name,
        "email": teacher.email,
        "class_section_id": teacher.class_section_id
    }

@router.get("/student/me")
def get_student_profile(
    token: str = Security(oauth2_scheme),
    db: Session = Depends(get_db)
):
    payload = decode_token(token)
    if not payload or payload["role"] != "STUDENT":
        raise HTTPException(status_code=401, detail="Unauthorized")

    student = db.query(Student).filter(Student.id == payload["id"]).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    return {
        "id": student.id,
        "name": student.name,
        "email": student.email,
        "age": student.age,
        "gender": student.gender,
        "class_name": student.class_name,
        "class_section_id": student.class_section_id
    }
