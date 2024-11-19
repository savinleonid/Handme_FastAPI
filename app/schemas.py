# app/schemas.py

from pydantic import BaseModel, field_validator
from pydantic_core.core_schema import FieldValidationInfo


class UserCreate(BaseModel):
    username: str
    password: str
    password_confirm: str

    @field_validator("password_confirm")
    def passwords_match(cls, v, info: FieldValidationInfo):
        # Use info.data.get("password") to access the password field
        if info.data.get("password") != v:
            raise ValueError("Passwords do not match")
        return v

class UserResponse(BaseModel):
    id: int
    username: str

    class Config:
        from_attributes = True
