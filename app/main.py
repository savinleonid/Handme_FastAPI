# app/main.py
import os
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt
from fastapi import FastAPI, Depends, HTTPException, Request, Form, UploadFile, File
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import or_
from sqlalchemy.orm import Session
from starlette.status import HTTP_303_SEE_OTHER

from app.auth import get_current_user
from app.crud import create_user, get_user_by_username, pwd_context, delete_user
from app.database import get_db
from app.schemas import UserCreate, UserResponse
from . import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from .models import Product, Category

app = FastAPI()


# Mount the static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

templates = Jinja2Templates(directory="app/templates")

PROFILE_DIR = Path("app/static/media/profile_pics")
PRODUCT_DIR = Path("app/static/media/product_images")

@app.get("/register", response_class=HTMLResponse)
async def register_form(request: Request):
    errors = {}
    return templates.TemplateResponse("registration/register.html", {"request": request, "errors": errors})


@app.post("/register")
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
    access_token = jwt.encode({"sub": user.username}, "your_secret_key", algorithm="HS256")
    response = RedirectResponse(url="/", status_code=HTTP_303_SEE_OTHER)
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
    return response

@app.get("/login")
async def login_form(request: Request):
    errors = {}
    return templates.TemplateResponse("registration/login.html", {"request": request, "errors": errors})

@app.post("/login")
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

@app.post("/logout")
async def logout(request: Request):
    # Redirect to the homepage after logging out
    response = RedirectResponse(url="/", status_code=HTTP_303_SEE_OTHER)
    # Remove the access_token by setting it to an empty value and a past expiration
    response.delete_cookie("access_token")
    return response


@app.post("/delete_account")
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

@app.get("/", response_class=HTMLResponse)
async def home(
    request: Request,
    q: str = '',
    category: str = '',
    location: str = '',
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    # Fetch all categories from the database
    categories = db.query(Category).all()

    # Fetch all unique locations from products
    locations = db.query(Product.location).distinct().all()
    locations = [loc[0] for loc in locations]  # Extract the location strings

    # Initialize the query to fetch all products
    products_query = db.query(Product)

    # Apply search filter if provided
    if q:
        products_query = products_query.filter(
            or_(
                Product.name.ilike(f"%{q}%"),
                Product.description.ilike(f"%{q}%"),
                Product.location.ilike(f"%{q}%")
            )
        )

    # Apply category filter if selected
    if category:
        products_query = products_query.filter_by(category_id=category)

    # Apply location filter if selected
    if location:
        products_query = products_query.filter_by(location=location)

    # Execute the query to get the products
    products = products_query.all()

    # Fetch user's profile picture if authenticated
    profile_picture = None
    if current_user:
        profile_picture = current_user.profile.profile_picture if current_user.profile.profile_picture else ""

    # Render the home template
    return templates.TemplateResponse(
        "app/home.html",
        {
            "request": request,
            "products": products,
            "categories": categories,
            "locations": locations,
            "selected_category": category,
            "selected_location": location,
            "profile_picture": profile_picture,
            "query": q,
            "current_user": current_user
        },
    )

@app.get("/product/detail/{product_id}")
async def product_detail(
        request: Request,
        product_id: int,
        db: Session = Depends(get_db),
        current_user = Depends(get_current_user)
):
    product = db.query(Product).filter_by(id=product_id).first()
    return templates.TemplateResponse("app/product_detail.html", {
        "request": request,
        "product": product,
        "current_user": current_user
    })


@app.get("/product/edit/{product_id}")
async def product_edit(
        request: Request,
        product_id: int,
        db: Session = Depends(get_db),
        current_user: UserResponse = Depends(get_current_user)
):
    errors ={}

    # Fetch product for current user
    product = db.query(Product).filter_by(id=product_id, creator=current_user).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Fetch all categories
    categories = db.query(Category).all()

    return templates.TemplateResponse("app/product_edit.html", {
        "request": request,
        "product": product,
        "categories": categories,
        "errors": errors
    })


@app.post("/product/edit/{product_id}")
async def product_edit(
        request: Request,
        product_id: int,
        name: str = Form(...),
        description: str = Form(...),
        price: int = Form(...),
        location: str = Form(...),
        category: str = Form(None),
        new_category: str = Form(None),
        product_image: UploadFile = File(None),
        db: Session = Depends(get_db),
        current_user = Depends(get_current_user)
):
    # Fetch product for current user
    product = db.query(Product).filter_by(id=product_id, creator=current_user).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Update product details
    product.name = name
    product.description = description
    product.price = price
    product.location = location

    # Update category
    if new_category:
        # Add new category if specified
        new_category_obj = Category()
        new_category_obj.name = new_category
        db.add(new_category_obj)
        db.commit()
        db.refresh(new_category_obj)
        product.category_id = new_category_obj.id
    elif category:
        product.category_id = category

    # Update product image if provided
    if product_image:
        # Delete the old image if it exists
        if product.image:
            old_image_path = os.path.join("app/static", product.image)
            if os.path.exists(old_image_path) and not product.image == "media/product_images/default_product.png":
                os.remove(old_image_path)

        # Save the new image
        if product_image.filename:
            filename = f"{product_id}_{product_image.filename}"
            file_path = os.path.join("app/static/media/product_images", filename)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(product_image.file, buffer)

            product.image = f"media/product_images/{filename}"
        else:
            product.image = "media/product_images/default_product.png"

    # Commit changes to the database
    db.add(product)
    db.commit()

    # Redirect to home after updating
    return RedirectResponse(url="/", status_code=HTTP_303_SEE_OTHER)


@app.get("/product/new")
async def new_product(request: Request, db: Session = Depends(get_db)):
    errors ={}
    # Fetch all categories from the database
    categories = db.query(Category).all()
    return templates.TemplateResponse("app/product_form.html", {
        "request": request,
        "errors": errors,
        "categories": categories
    })

@app.post("/product/new")
async def new_product(
    request: Request,
    name: str = Form(...),
    description: str = Form(...),
    price: int = Form(...),
    location: str = Form(...),
    category: str = Form(...),
    new_category: str = Form(None),
    product_image: UploadFile = File(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    # Ensure the user is authenticated
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Determine the category
    if new_category:
        # Create new category logic here, or reuse existing logic to add a category
        category = Category()
        category.name = new_category
    else:
        selected_category = Category()
        selected_category.name = category
        category = selected_category

    db.add(category)

    # Save product image if provided
    image_path = None
    if product_image:
        filename = f"{current_user.id}_{product_image.filename}"
        file_path = PRODUCT_DIR / filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(product_image.file, buffer)
        image_path = f"media/product_images/{filename}"

    # Add the product to the database
    new_product = Product(
        name=name,
        description=description,
        price=price,
        location=location,
        image=image_path,
        category_id=category.id,
        user_id=current_user.id  # Associate the product with the current user
    )
    db.add(new_product)
    db.commit()

    # Redirect to the home page or a product list page
    return RedirectResponse(url="/", status_code=HTTP_303_SEE_OTHER)


@app.post("/product/delete/{product_id}")
async def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    # Get product by primary key and seller
    product = db.query(Product).filter_by(id=product_id, creator=current_user).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Delete the product from the session and commit to the database
    db.delete(product)
    db.commit()

    # Redirect to profile after deletion
    return RedirectResponse(url="/profile", status_code=HTTP_303_SEE_OTHER)


@app.get("/profile")
async def profile(request: Request, user: UserResponse = Depends(get_current_user)):
    return templates.TemplateResponse("app/profile.html", {"request": request, "current_user": user})

@app.post("/profile")
async def upload_profile_photo(
    request: Request,
    profile_picture: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
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


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

