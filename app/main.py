from fastapi import FastAPI
from app.auth import router as auth_router
from app.products import router as products_router  # Assuming you'll modularize products later

app = FastAPI()

# Include authentication routes
app.include_router(auth_router)

# Include product routes
app.include_router(products_router)
