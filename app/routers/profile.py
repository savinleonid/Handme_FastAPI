# app/routers/profile.py
import os
import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from starlette.status import HTTP_303_SEE_OTHER

from app.crud import get_current_user
from app.database import get_db
from app.schemas import UserResponse
from config import templates

router = APIRouter()

PROFILE_DIR = Path("app/static/media/profile_pics")


@router.get("/")
async def profile(request: Request, user: UserResponse = Depends(get_current_user)):
    return templates.TemplateResponse("app/profile.html", {"request": request, "current_user": user})


@router.post("/")
async def upload_profile_photo(
        request: Request,
        profile_picture: UploadFile = File(...),
        db: Session = Depends(get_db),
        current_user=Depends(get_current_user),
):
    # Ensure the user is authenticated
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Path to the directory where profile pictures are stored
    if not PROFILE_DIR.exists():
        PROFILE_DIR.mkdir(parents=True, exist_ok=True)

    # Delete the old profile picture if it exists and is not the default one
    old_picture_path = Path("app/static") / current_user.profile.profile_picture
    if old_picture_path.exists() and "default.png" not in str(old_picture_path):
        try:
            os.remove(old_picture_path)
        except Exception as e:
            print(f"Error deleting old profile picture: {e}")

    # Save the uploaded file
    filename = f"{current_user.id}_{profile_picture.filename}"
    file_path = PROFILE_DIR / filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(profile_picture.file, buffer)

    # Update the user's profile picture in the database
    current_user.profile.profile_picture = f"media/profile_pics/{filename}"
    db.commit()

    # Redirect back to the profile page after the upload
    response = RedirectResponse(url="/profile", status_code=HTTP_303_SEE_OTHER)
    return response
