from fastapi import FastAPI, HTTPException
import pandas as pd

df = pd.read_json("products.json")


NO_DATA_FOUND = 404
app = FastAPI()

# Get all product

@app.get("/products/")
def get_products():
    return df.to_dict(orient="records")
