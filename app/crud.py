# app/crud.py

from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.models import User, Profile
from app.schemas import UserCreate

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

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
