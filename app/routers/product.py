# app/routers/product.py

import os
import shutil

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, File, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from starlette.status import HTTP_303_SEE_OTHER

from app.crud import get_current_user
from app.database import get_db
from app.models import Product, Category
from app.schemas import UserResponse
from config import templates

router = APIRouter()

PRODUCT_DIR = "app/static/media/product_images"


@router.get("/new")
async def new_product(request: Request, db: Session = Depends(get_db)):
    errors = {}
    # Fetch all categories from the database
    categories = db.query(Category).all()
    return templates.TemplateResponse("app/product_form.html", {
        "request": request,
        "errors": errors,
        "categories": categories
    })


@router.post("/new")
async def new_product(name: str = Form(...), description: str = Form(...), price: int = Form(...),
                      location: str = Form(...), category: str = Form(...), new_category: str = Form(None),
                      product_image: UploadFile = File(None), db: Session = Depends(get_db),
                      current_user=Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if new_category:
        category_obj = Category(name=new_category)
        db.add(category_obj)
        db.commit()
        db.refresh(category_obj)
    else:
        category_obj = db.query(Category).filter_by(id=category).first()
    if product_image.filename:
        filename = f"{current_user.id}_{product_image.filename}"
        file_path = os.path.join(PRODUCT_DIR, filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(product_image.file, buffer)
        image_path = f"media/product_images/{filename}"
    else:
        image_path = "media/product_images/default_product.png"
    new_product = Product(name=name, description=description, price=price, location=location,
                          image=image_path, category_id=category_obj.id, user_id=current_user.id)
    db.add(new_product)
    db.commit()
    return RedirectResponse(url="/", status_code=303)


@router.get("/edit/{product_id}")
async def product_edit(
        request: Request,
        product_id: int,
        db: Session = Depends(get_db),
        current_user: UserResponse = Depends(get_current_user)
):
    errors = {}

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


@router.post("/edit/{product_id}")
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
        current_user=Depends(get_current_user)
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


@router.post("/delete/{product_id}")
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


@router.get("/detail/{product_id}")
async def product_detail(
        request: Request,
        product_id: int,
        db: Session = Depends(get_db),
        current_user=Depends(get_current_user)
):
    product = db.query(Product).filter_by(id=product_id).first()
    return templates.TemplateResponse("app/product_detail.html", {
        "request": request,
        "product": product,
        "current_user": current_user
    })
