# config.py (in C:\Users\arroy\ecommerceflask)
import os

class Config:
    # Secret key for session management and security
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'

    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://postgres:042204rl@127.0.0.1/regformapp3'
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Disable to improve performance

    # Upload folder paths (centralized here instead of __init__.py)
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    PRODUCT_UPLOAD_FOLDER = os.path.join(BASE_DIR, 'app', 'uploads', 'products')
    BUSINESS_PERMIT_UPLOAD_FOLDER = os.path.join(BASE_DIR, 'app', 'uploads', 'business_permit')
    VALID_ID_UPLOAD_FOLDER = os.path.join(BASE_DIR, 'app', 'uploads', 'valid_id')

    # Flask-RESTful and debug settings
    PROPAGATE_EXCEPTIONS = True  # Ensure RESTful exceptions are visible in debug mode
    DEBUG = True  # Enable debug mode (matches run.py)