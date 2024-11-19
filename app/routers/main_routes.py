# app/routers/main_routes.py

from fastapi import APIRouter, Request, Depends
from sqlalchemy import or_
from sqlalchemy.orm import Session
from starlette.responses import HTMLResponse

from app.crud import get_current_user
from app.database import get_db
from app.models import Product, Category
from config import templates

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def home(
        request: Request,
        q: str = '',
        category: str = '',
        location: str = '',
        db: Session = Depends(get_db),
        current_user=Depends(get_current_user),
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
