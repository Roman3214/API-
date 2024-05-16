# main.py
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession 
from passlib.context import CryptContext
from jose import JWTError, jwt
from typing import Optional, List
from datetime import datetime, timedelta
import models
import schemas
from database import async_session_factory
from config import secret_key
import logging

app = FastAPI()

logging.basicConfig(filename='app.log', level=logging.INFO)
logger = logging.getLogger(__name__)

SECRET_KEY = secret_key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def get_db():
    db = async_session_factory()
    try:
        yield db
    finally:
        await db.close()


@app.post("/users/")
async def register(user: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    hashed_password = pwd_context.hash(user.password)
    db_user = models.User(id=None, username=user.username, email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return {"message": "User created successfully."}

@app.get("/users/{user_id}")
async def read_user(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    db_user = result.scalars().first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@app.put("/users/{user_id}")
async def update_user(user_id: int, user: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    db_user = result.scalars().first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    db_user.username = user.username
    db_user.email = user.email
    db_user.hashed_password = pwd_context.hash(user.password)
    await db.commit()
    await db.refresh(db_user)
    return {"message": "User updated successfully."}

@app.delete("/users/{user_id}")
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    db_user = result.scalars().first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    await db.delete(db_user)
    await db.commit()
    return {"message": "User deleted successfully."}


async def authenticate_user(db: AsyncSession, username: str, password: str):
    result = await db.execute(select(models.User).where(models.User.username == username))
    user = result.scalars().first()
    if not user:
        return False
    if not pwd_context.verify(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

async def get_current_user(db: AsyncSession = Depends(get_db), token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        logger.info(f"Decoded JWT payload: {payload}")
        if username is None:
            logger.warning("Username is None")
            raise credentials_exception
    except (JWTError, jwt.ExpiredSignatureError) as e:
        logger.error(f"JWTError occurred: {e}")
        raise credentials_exception
    user = await db.execute(select(models.User).where(models.User.username == username))
    user = user.scalars().first()
    logger.info(f"User fetched from DB: {user}")
    if user is None:
        logger.warning("User is None")
        raise credentials_exception
    return user
 

@app.post("/notes/", response_model=schemas.NoteBase)
async def create_note(note: schemas.NoteBase, db: AsyncSession = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    result = await db.execute(select(models.User.id).where(models.User.username == current_user.username))
    user_id = result.scalar_one_or_none()
    db_note = models.Note(id=None, title=note.title, content=note.content, user_id=user_id)
    db.add(db_note)
    await db.commit()
    await db.refresh(db_note)
    return {"title": db_note.title, "content": db_note.content}

@app.get("/notes/{note_id}")
async def read_note(note_id: int, db: Session = Depends(get_db)):
    result = await db.execute(select(models.Note).where(models.Note.id == note_id))
    db_note = result.scalar_one_or_none()
    if db_note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    return db_note

@app.put("/notes/{note_id}")
async def update_note(note_id: int, note: schemas.NoteBase, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    result = await db.execute(select(models.Note).where(models.Note.id == note_id, models.Note.user_id == current_user.id))
    db_note = result.scalar_one_or_none()
    if db_note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    db_note.title = note.title
    db_note.content = note.content
    await db.commit()
    await db.refresh(db_note)
    return {"message": "Note updated successfully."}

@app.delete("/notes/{note_id}")
async def delete_note(note_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    result = await db.execute(select(models.Note).where(models.Note.id == note_id, models.Note.user_id == current_user.id))
    db_note = result.scalar_one_or_none()
    if db_note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    await db.delete(db_note)
    await db.commit()
    return {"message": "Note deleted successfully."}


@app.get("/users/{user_id}/notes", response_model=List[schemas.NoteInDB])
async def read_user_notes(user_id: int, db: Session = Depends(get_db)):
    result = await db.execute(select(models.Note).where(models.Note.user_id == user_id))
    db_notes = result.scalars().all()
    if not db_notes:
        raise HTTPException(status_code=404, detail="No notes found for this user")
    return db_notes

@app.get("/notes", response_model=List[schemas.NoteInDB])
async def read_notes(title: Optional[str] = None, created_at: Optional[datetime] = None, db: Session = Depends(get_db)):
    if title and created_at:
        result = await db.execute(select(models.Note).where(models.Note.title.contains(title), models.Note.created_at == created_at))
        db_notes = result.scalars().all()
    elif title:
        result = await db.execute(select(models.Note).where(models.Note.title.contains(title)))
        db_notes = result.scalars().all()
    elif created_at:
        result = await db.execute(select(models.Note).where(models.Note.created_at == created_at))
        db_notes = result.scalars().all()
    else:
        db_notes = await db.execute(models.Note).all()
    if not db_notes:
        raise HTTPException(status_code=404, detail="No notes found")
    return db_notes
