# app/crud.py
from datetime import timedelta, datetime, timezone

from fastapi import Depends, Request
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Profile
from app.schemas import UserCreate
from config import ACCESS_TOKEN_EXPIRE_MINUTES
from . import SECRET_KEY, ALGORITHM

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_current_user(request: Request, db: Session = Depends(get_db)):
    # Retrieve the token from the cookies
    token = request.cookies.get("access_token")

    if token is None:
        return None

    try:
        # If the token contains "Bearer ", split it to extract the actual token
        token = token.split(" ")[1] if " " in token else token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
    except JWTError:
        return None

    user = get_user_by_username(db, username=username)
    if user is None:
        return None
    return user


def get_password_hash(password):
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()


def create_user(db: Session, user: UserCreate):
    # Hash the password
    hashed_password = get_password_hash(user.password)

    # Create User instance with hashed password
    db_user = User(username=user.username, password=hashed_password)
    db.add(db_user)

    # Commit once, and refresh db_user to get the user ID
    db.commit()
    db.refresh(db_user)

    # Create a default Profile instance associated with the new user
    db_profile = Profile(user_id=db_user.id, profile_picture="media/profile_pics/default.png")
    db.add(db_profile)

    # Final commit to save the profile
    db.commit()
    db.refresh(db_profile)

    return db_user

def delete_user(db: Session, user_id: int):
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        db.delete(user)
        db.commit()
