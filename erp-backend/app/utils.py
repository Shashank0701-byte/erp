from passlib.context import CryptContext

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash
    """
    return pwd_context.verify(plain_password, hashed_password)


def generate_order_number(prefix: str = "ORD") -> str:
    """
    Generate a unique order number
    """
    from datetime import datetime
    import random
    
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_suffix = random.randint(1000, 9999)
    return f"{prefix}-{timestamp}-{random_suffix}"


def calculate_pagination(page: int, page_size: int, total: int) -> dict:
    """
    Calculate pagination metadata
    """
    total_pages = (total + page_size - 1) // page_size
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1
    }


def format_currency(amount: float, currency: str = "USD") -> str:
    """
    Format amount as currency
    """
    return f"{currency} {amount:,.2f}"


def validate_file_extension(filename: str, allowed_extensions: list[str]) -> bool:
    """
    Validate file extension
    """
    import os
    _, ext = os.path.splitext(filename)
    return ext.lower() in allowed_extensions
