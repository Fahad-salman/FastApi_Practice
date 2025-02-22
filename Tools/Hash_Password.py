from passlib.context import CryptContext

# In this program you can see how lock hashed password. 
# Set up the password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str):
    return pwd_context.hash(password)

# Generate hashed passwords for admin and user
admin_password = hash_password("admin@2025")
user_password = hash_password("user@2025")

# Print valid hashed passwords
print("Admin hashed password:", admin_password)
print("User hashed password:", user_password)