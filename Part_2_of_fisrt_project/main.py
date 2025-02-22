from fastapi import FastAPI, HTTPException, Query, status, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from jose import JWTError, jwt
from passlib.context import CryptContext

from datetime import datetime, timedelta

import pandas as pd
from typing import Optional

# install the following packages 
# pip install fastapi uvicorn

# Down below required packages for Authentication & Authorization
# pip install python-jose[cryptography] passlib[bcrypt] fastapi-users


# To run our API : ( py -m uvicorn FAST_API_Example:app --reload ) or ( python3 -m uvicorn FAST_API_Example:app --reload ) -> "FAST_API_Example" change it to your python file name.
# here's the API url (http://127.0.0.1:8000/products/)


SECRET_KEY = "your_secret_key_here" # you can create your own password by using the following program check if you want to (https://github.com/Fahad-salman/python-Practice/blob/main/PasswordGenerator.py) USE generate_password_v2 !
ALGORITHM = "HS256" # if you want to know what dose that mean "HS256" check here (https://stackoverflow.com/questions/39239051/rs256-vs-hs256-whats-the-difference)
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Dummy users DB for authentication
users_db = {
    "admin": {
        "username": "admin",
        "full_name": "Admin User",
        "password": "$2b$12$AGBqKOoqitgwFqTebJ0lNO9WYs3xjrPDrjBW0l2WnwQUxuZ4pNmPm",  # Example: admin_password -> admin@2025
        "role": "admin"
    },
    "user": {
        "username": "user",
        "full_name": "Regular User",
        "password": "$2b$12$2GqlzdQpokgoXRbpxrN0G.Ed803Iw9sOy7gwNXSGzYnGdvCSSfSse",  # Example: user_password -> user@2025
        "role": "user"
    }
}

# Security and password hashing setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

df = pd.read_json("../Data/products.json")

app = FastAPI()

# verify the password
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# Authenticate user
def authenticate_user(username: str, password: str):
    user = users_db.get(username)
    if not user:
        print("User not found in database")
        return False
    # Verify password and print the result
    password_matches = verify_password(password, user["password"])
    print(f"Password match result: {password_matches}")
    if not password_matches:
        print("Password does not match")
        return False
    return user

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

# Get the current user from token
async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = users_db.get(username)
    if user is None:
        raise credentials_exception
    return user

# Get the current admin user
async def get_current_admin_user(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can perform this action")
    return current_user

# Token endpoint for user login
@app.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Get all products
@app.get("/products")
def get_products(current_user: dict = Depends(get_current_user)):
    return df.to_dict(orient="records")

# Get product by id
@app.get("/product/{product_id}")
def get_product_by_id(product_id: int, current_user: dict = Depends(get_current_user)):
    product = df[df["product_id"] == product_id] # Filter by product_id
    if product.empty:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product.to_dict(orient="records")[0] # Return first matching product as dict

# Search by product name.
@app.get("/products/search/{product_name}")
def search_product(product_name: str, current_user: dict = Depends(get_current_user)):
    matched_products = df[df["product_name"].str.contains(product_name, case=False, na=False)]
    if matched_products.empty:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"There's no product like {product_name} ")
    return matched_products.to_dict(orient="records")

# Advanced search
@app.get("/products/search/")
def advanced_search(current_user: dict = Depends(get_current_user),
    product_name: Optional[str] = None,
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    sort_by: Optional[str] = Query(None, regex="^(price|product_name|expiration_date)$"),
    sort_order: Optional[str] = Query("asc", regex="^(asc|desc)$")
):
    global df
    results = df.copy()

    # Filter by partial product name case-insensitive
    if product_name:
        results = results[results["product_name"].str.contains(product_name, case=False, na=False)]

    # Filter by price range
    if min_price is not None:
        results = results[results["price"] >= min_price]
    if max_price is not None:
        results = results[results["price"] <= max_price]

    # Filter by expiration date range
    if from_date:
        try:
            from_date_parsed = pd.to_datetime(from_date)
            results = results[pd.to_datetime(results["expiration_date"]) >= from_date_parsed]
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid from_date format. Use YYYY-MM-DD.")
    if to_date:
        try:
            to_date_parsed = pd.to_datetime(to_date)
            results = results[pd.to_datetime(results["expiration_date"]) <= to_date_parsed]
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid to_date format. Use YYYY-MM-DD.")

    # Sorting
    if sort_by:
        results = results.sort_values(by=sort_by, ascending=(sort_order == "asc"))

    # If no results found
    if results.empty:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No matching products found.")

    return results.to_dict(orient="records")
        
# Delete product
@app.delete("/delete/product/{product_id}")
def delete_product(product_id: int, current_user: dict = Depends(get_current_admin_user)):
    global df
    if product_id not in df["product_id"].values:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    
    df[df["product_id"] != product_id]
    
    df.to_json("products.json", orient="records", indent=4)
    
    return {"message": f"Product with ID {product_id} deleted successfully"}

# Update Product
@app.put("/update/product/{product_id}")
def update_product(product_id: int, product_name: str = None, price: float = None, expiration_date: str = None, current_user: dict = Depends(get_current_admin_user)):
    global df

    # Check if product exists
    if product_id not in df["product_id"].values:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="The product does not exist.")

    # Ensure at least one field is provided
    if not any([product_name, price, expiration_date]):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one field must be provided for update.")

    # Locate the index of the product to update
    index = df[df["product_id"] == product_id].index[0]

    # Update only the provided fields
    if product_name is not None:
        df.at[index, "product_name"] = product_name
    if price is not None:
        df.at[index, "price"] = price
    if expiration_date is not None:
        df.at[index, "expiration_date"] = expiration_date

    # Save updated DataFrame back to JSON file
    df.to_json("products.json", orient="records", indent=4)

    return {
        "message": f"Product with ID {product_id} updated successfully",
        "updated_product": df.iloc[index].to_dict()
    }
    
    
