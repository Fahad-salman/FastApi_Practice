from fastapi import FastAPI, HTTPException, Query, status

import pandas as pd
from typing import Optional

# install the following packages 
# pip install fastapi uvicorn

# To run our API : ( py -m uvicorn FAST_API_Example:app --reload ) or ( python3 -m uvicorn FAST_API_Example:app --reload ) -> "FAST_API_Example" change it to your python file name.
# here's the API url (http://127.0.0.1:8000/products/)


df = pd.read_json("../Data/products.json")

app = FastAPI()    

# Get all product
@app.get("/products/")
def get_products():
    return df.to_dict(orient="records")

# Get product by id
@app.get("/product/{product_id}")
def get_product_by_id(product_id: int):
    product = df[df["product_id"] == product_id] # Filter by product_id
    if product.empty:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product.to_dict(orient="records")[0] # Return first matching product as dict

# Search by product name.
@app.get("/products/search/{product_name}")
def search_product(product_name: str):
    matched_products = df[df["product_name"].str.contains(product_name, case=False, na=False)]
    if matched_products.empty:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"There's no product like {product_name} ")
    return matched_products.to_dict(orient="records")

# Advanced search
@app.get("/products/search/")
def advanced_search(
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
def delete_product(product_id: int):
    global df
    if product_id not in df["product_id"].values:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    
    df[df["product_id"] != product_id]
    
    df.to_json("products.json", orient="records", indent=4)
    
    return {"message": f"Product with ID {product_id} deleted successfully"}


# Update Product
@app.put("/update/product/{product_id}")
def update_product(product_id: int, product_name: str = None, price: float = None, expiration_date: str = None):
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