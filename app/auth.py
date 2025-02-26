from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Secret key for JWT
SECRET_KEY = "your_secret_key_here"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# In-memory users database
users_db: Dict[str, Dict] = {
    "admin": {
        "username": "admin",
        "full_name": "Admin User",
        "password": pwd_context.hash("admin@2025"),
        "role": "admin"
    },
    "user": {
        "username": "user",
        "full_name": "Regular User",
        "password": pwd_context.hash("user@2025"),
        "role": "user"
    }
}

# Define a router for authentication
router = APIRouter()

# Pydantic model for user registration
class UserRegister(BaseModel):
    username: str = Field(..., min_length=4, max_length=20)
    full_name: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    role: Optional[str] = "user"  # Default role is user

# Function to hash a password
def hash_password(password: str):
    return pwd_context.hash(password)

# Generate JWT token
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# User registration endpoint
@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_user(user: UserRegister):
    if user.username in users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )

    # Add the new user to the in-memory database
    hashed_password = hash_password(user.password)
    users_db[user.username] = {
        "username": user.username,
        "full_name": user.full_name,
        "password": hashed_password,
        "role": user.role
    }

    return {"message": f"User {user.username} registered successfully!"}
