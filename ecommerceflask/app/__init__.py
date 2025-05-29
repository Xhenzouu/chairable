# app/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api
import os
import logging

# Initialize the Flask app
app = Flask(__name__)

# Load configurations from config.py
app.config.from_object('config.Config')

# Ensure the uploads directories exist
try:
    os.makedirs(app.config['PRODUCT_UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['BUSINESS_PERMIT_UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['VALID_ID_UPLOAD_FOLDER'], exist_ok=True)
except Exception as e:
    logging.error(f"Error creating upload directories: {e}")

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Initialize Flask-RESTful API
api = Api(app)

# Import models first (no circular dependency)
from app import models

# Function to initialize routes after app, db, and api are ready
def init_routes():
    from app import routes  # Delayed import to avoid circular dependency

# Call the function to register routes
init_routes()