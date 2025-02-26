from fastapi import APIRouter, HTTPException, Depends, status
from typing import Optional
import pandas as pd

router = APIRouter()

# Load JSON file for product data
df = pd.read_json("./Data/products.json")

# Get all products
@router.get("/products/")
def get_products():
    return df.to_dict(orient="records")

# Get a product by ID
@router.get("/product/{product_id}")
def get_product_by_id(product_id: int):
    product = df[df["product_id"] == product_id]
    if product.empty:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product.to_dict(orient="records")[0]
