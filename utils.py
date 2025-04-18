from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from database import SessionLocal
from routes.auth.auth import decode_token
from models import Principal, Teacher

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_principal(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    data = decode_token(token)
    if not data or data["role"] != "principal":
        raise HTTPException(status_code=401, detail="Unauthorized")
    user = db.query(Principal).filter(Principal.id == data["id"]).first()
    return user

def get_current_teacher(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    data = decode_token(token)
    if not data or data["role"] != "teacher":
        raise HTTPException(status_code=401, detail="Unauthorized")
    user = db.query(Teacher).filter(Teacher.id == data["id"]).first()
    return user
