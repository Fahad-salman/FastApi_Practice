from fastapi import FastAPI, HTTPException
import pandas as pd

# install the following packages 
# # pip install fastapi uvicorn

# To run our API : ( py -m uvicorn FAST_API_Example:app --reload ) or ( python3 -m uvicorn FAST_API_Example:app --reload ) 
# here's the API url (http://127.0.0.1:8000/products/)

df = pd.read_json("products.json")

NO_DATA_FOUND = 404
app = FastAPI()

# Get all product

@app.get("/products/")
def get_products():
    return df.to_dict(orient="records")


@app.get("/product/{product_id}")
def get_product_by_id(product_id: int):
    product = df[df["product_id"] == product_id] # Filter by product_id
    if product.empty:
        raise HTTPException(status_code=NO_DATA_FOUND, detail="Product not found")
    return product.to_dict(orient="records")[0] # Return first matching product as dict

# Search by product name.
@app.get("/products/search/{product_name}")
def search_product(product_name: str):
    matched_products = df[df["product_name"].str.contains(product_name, case=False, na=False)]
    if matched_products.empty:
        raise HTTPException(status_code=NO_DATA_FOUND, detail=f"There's no product like {product_name} ")
    return matched_products.to_dict(orient="records")