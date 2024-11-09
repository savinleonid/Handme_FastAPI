# app/auth.py
from . import SECRET_KEY, ALGORITHM
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from app.crud import get_user_by_username
from app.database import get_db
from app.models import User
from sqlalchemy.orm import Session

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

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

