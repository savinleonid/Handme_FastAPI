# app/routers/auth.py
import jwt
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from starlette.responses import HTMLResponse
from starlette.status import HTTP_303_SEE_OTHER

from app.crud import create_user, get_user_by_username, delete_user, get_current_user, create_access_token, verify_password
from app.schemas import UserCreate
from app.database import get_db
from config import templates, SECRET_KEY, ALGORITHM

router = APIRouter()

@router.get("/register", response_class=HTMLResponse)
async def register_form(request: Request):
    errors = {}
    return templates.TemplateResponse("registration/register.html", {"request": request, "errors": errors})

@router.post("/register")
async def register(
        request: Request,
        username: str = Form(...),
        password: str = Form(...),
        password_confirm: str = Form(...),
        db: Session = Depends(get_db),
):
    errors = {}

    # Check if username already exists
    if get_user_by_username(db, username):
        errors["username"] = "Username already taken."

    # Check if passwords match
    if password != password_confirm:
        errors["password_confirm"] = "Passwords do not match."

    # If there are errors, re-render the form with errors
    if errors:
        return templates.TemplateResponse("registration/register.html", {
            "request": request,
            "username": username,
            "errors": errors,
        })

    # Create the user
    user_create = UserCreate(username=username, password=password, password_confirm=password_confirm)
    user = create_user(db, user_create)

    # Automatically log in the user after registration
    access_token = jwt.encode({"sub": user.username}, SECRET_KEY, algorithm=ALGORITHM)
    response = RedirectResponse(url="/", status_code=HTTP_303_SEE_OTHER)
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
    return response

@router.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    errors = {}
    return templates.TemplateResponse("registration/login.html", {"request": request, "errors": errors})

@router.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    errors = {}

    # Authenticate the user
    user = get_user_by_username(db, username)
    if not user or not verify_password(password, user.password):
        errors["login"] = "Invalid username or password."

    # If there are errors, re-render the form with errors
    if errors:
        return templates.TemplateResponse("registration/login.html", {
            "request": request,
            "username": username,
            "errors": errors,
        })

    access_token = create_access_token(data={"sub": username})
    response = RedirectResponse(url="/", status_code=HTTP_303_SEE_OTHER)
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
    return response

@router.post("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("access_token")
    return response

@router.post("/delete_account")
async def delete_account(
        request: Request,
        db: Session = Depends(get_db),
        current_user = Depends(get_current_user)
):
    # Delete the user from the database
    delete_user(db, user_id=current_user.id)

    # Remove the access_token by setting it to an empty value and a past expiration date
    response = RedirectResponse(url="/", status_code=HTTP_303_SEE_OTHER)
    response.delete_cookie("access_token")
    return response


