# app/models.py

from sqlalchemy import Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String, nullable=False)

    # Relationship to Profile
    profile = relationship('Profile', back_populates='user', cascade='all, delete-orphan', uselist=False)

    # Relationship to Products
    products = relationship('Product', back_populates='creator', cascade='all, delete-orphan')  # One-to-many relationship


class Profile(Base):
    __tablename__ = "profiles"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    profile_picture = Column(String, nullable=True, default="media/profile_pics/default.png")
    location = Column(String(100), nullable=True)
    bio = Column(Text, nullable=True)

    user = relationship("User", back_populates="profile")


class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)

    # Relationship to Products
    products = relationship('Product', back_populates='category', cascade='all, delete-orphan')  # One-to-many relationship with Product


class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    price = Column(Integer)
    image = Column(String, nullable=True, default="media/product_images/default_product.png")
    location = Column(String(50))
    user_id = Column(Integer, ForeignKey("users.id"))
    category_id = Column(Integer, ForeignKey("categories.id"))

    # Relationships
    creator = relationship("User", back_populates="products")  # Relationship to User
    category = relationship("Category", back_populates="products")  # Relationship to Category
