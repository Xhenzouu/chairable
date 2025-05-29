from flask import (
    Blueprint, Flask, render_template, render_template_string, request, redirect, url_for, flash, 
    session, make_response, get_flashed_messages, jsonify, send_from_directory, send_file
)
from app import api, app, db
import psycopg2
import json
import os
import uuid
import logging
from sqlalchemy.exc import IntegrityError
import random
import smtplib
import io
import csv
from datetime import datetime, timezone, timedelta
from sqlalchemy import not_
from app.models import Product, User, ProductApproval, Order, OrderItem, Notification, ChatMessage
from werkzeug.utils import secure_filename
from functools import wraps
from decimal import Decimal
import traceback
import decimal
from flask import current_app
from email.mime.text import MIMEText
from openpyxl import Workbook

# Create a Blueprint for API routes
api = Blueprint('api', __name__)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# File upload configuration
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Secret key configuration
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default_secret_key')


# Remove the duplicate UPLOAD_FOLDER configurations since they're now in __init__.py

def get_db_connection():
    return psycopg2.connect(
        host="127.0.0.1",
        user="postgres",
        password="042204rl",
        database="regformapp3"
    )

def load_countries():
    with open('data/countries.json') as f:
        return json.load(f)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'email' not in session:
            flash('You need to log in to access this page.', 'danger')
            return redirect(url_for('login'))

        if session.get('role') != 'admin':
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('index'))

        return f(*args, **kwargs)
    return decorated_function

def get_product_id_from_order(order_id):
    """Fetch the product ID associated with the given order ID."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT product_id FROM order_items WHERE order_id = %s', (order_id,))
                result = cur.fetchone()
                if result:
                    return result[0]  # Return the product_id
                else:
                    return None  # No product found for this order
    except Exception as e:
        print(f"Error fetching product ID from order: {str(e)}")
        return None
    
def get_product_by_id(product_id):
    """Fetch a product by its ID from the database."""
    try:
        with get_db_connection() as conn:  # Assuming you have a function to get DB connection
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM products WHERE id = %s", (product_id,))
                product = cur.fetchone()
                if product:
                    # Convert to dictionary for easier access
                    columns = [desc[0] for desc in cur.description]
                    return dict(zip(columns, product))
                else:
                    return None
    except Exception as e:
        print(f"Error fetching product by ID: {str(e)}")
        return None

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    # Assuming your files are stored in a folder called 'uploads'
    uploads_dir = os.path.join(current_app.root_path, 'uploads')
    return send_from_directory(uploads_dir, filename)

@app.route('/admin/commissions')
@admin_required
def admin_commissions():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Query to fetch delivered order commissions
                cur.execute("""
                    SELECT oi.order_id, p.name AS product_name, u.name AS buyer_name, 
                           oi.quantity * oi.price AS total_amount, o.status
                    FROM order_items oi
                    JOIN orders o ON oi.order_id = o.id
                    JOIN products p ON oi.product_id = p.id
                    JOIN users u ON o.user_id = u.id
                    WHERE o.status = 'DELIVERED'
                """)
                commissions_data = cur.fetchall()
                
                # Prepare data for rendering with commission calculation
                commissions_data = [
                    {
                        'order_id': row[0],
                        'product_name': row[1],
                        'buyer_name': row[2],
                        'total_amount': row[3],
                        'commission': Decimal(row[3]) * Decimal(0.05),  # Calculate 5% commission
                        'status': row[4]
                    }
                    for row in commissions_data
                ]
                
    except Exception as e:
        print(f"Error fetching commission data: {e}")
        commissions_data = []

    return render_template('admin_commissions.html', commissions_data=commissions_data)

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Check if user is already logged in
    if 'email' in session:
        if session['role'] == 'seller':
            return redirect(url_for('dashboard'))
        elif session['role'] == 'admin':
            return redirect(url_for('admin_users'))
        else:
            return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        remember_me = request.form.get('remember_me')

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Check user credentials
                    cur.execute('SELECT * FROM users WHERE email = %s AND password = %s', (email, password))
                    user = cur.fetchone()

                    if user:
                        # Check if the account is archived
                        if user[7]:  # Assuming `is_archived` is at index 7
                            flash('This account has been archived. Please contact an administrator.', 'error')
                            return render_template('login.html')

                        # Check approval status for sellers/admins
                        if user[8] is False and user[6] in ['seller', 'admin']:  # Assuming `approved` is at index 8 and `role` at index 6
                            flash('Your account has not been approved by the admin yet. Please wait for approval.', 'error')
                            return render_template('login.html')

                        # Store user details in session
                        session['user_id'] = user[0]  # id
                        session['email'] = user[2]  # email
                        session['role'] = user[6]  # role
                        session['approved'] = user[8]  # approved

                        # Handle OTP verification for users only
                        if session['role'] == 'user' and not user[9]:  # Assuming `otp_verified` is at index 9
                            otp = generate_otp()
                            send_otp(email, otp)
                            session['otp'] = otp
                            session['otp_verified'] = False  # Set to False initially
                            response = make_response(redirect(url_for('verify_otp')))
                            if remember_me:
                                response.set_cookie('remember_me', email, max_age=30 * 24 * 60 * 60)  # Cookie lasts for 30 days
                            return response

                        # If OTP is not required (for sellers and admins)
                        session['otp_verified'] = True

                        # Handle "Remember Me" functionality
                        response = make_response()
                        if remember_me:
                            response.set_cookie('remember_me', email, max_age=30 * 24 * 60 * 60)  # Cookie lasts for 30 days

                        # Role-based redirection
                        if session['role'] == 'admin':
                            return redirect(url_for('admin_users'))
                        elif session['role'] == 'seller':
                            return redirect(url_for('dashboard'))
                        else:
                            return redirect(url_for('index'))

                    else:
                        flash('Invalid email or password. Please try again.', 'error')

        except Exception as e:
            logging.error(f"An error occurred during login: {str(e)}")
            flash(f"An error occurred: {str(e)}", 'error')

    return render_template('login.html')




@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        # Handle email submission
        email = request.form.get('email')

        # Generate and send OTP
        otp = str(random.randint(100000, 999999))  # Generate a 6-digit OTP
        session['otp'] = otp  # Store OTP in session
        session['email'] = email  # Store email in session for validation later
        send_otp(email, otp)  # Send OTP via email

        flash('An OTP has been sent to your email. Please check your inbox.', 'info')
        return redirect(url_for('forgot_password_otp'))  # Redirect to OTP entry page

    # Render the initial email submission form
    return render_template('forgotpassword.html')

@app.route('/forgot-password-otp', methods=['GET', 'POST'])
def forgot_password_otp():
    if request.method == 'POST':
        # Handle OTP submission
        entered_otp = request.form.get('otp')
        new_password = request.form.get('new-password')

        if entered_otp == session.get('otp'):  # OTP is correct
            try:
                # Update password in the database
                with get_db_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute('UPDATE users SET password = %s WHERE email = %s', (new_password, session['email']))
                        conn.commit()
                        flash('Your password has been reset successfully!', 'success')
            except Exception as e:
                flash(f'An error occurred while resetting your password: {str(e)}', 'error')
            finally:
                # Clear session data
                session.pop('otp', None)
                session.pop('email', None)

            return redirect(url_for('login'))
        else:
            flash('Invalid OTP. Please try again.', 'error')
            return redirect(url_for('forgot_password_otp'))

    # Render the OTP submission form
    return render_template('forgotpassword_otp.html')

@app.route('/approvals')
def approvals():
    products = Product.query.all()  # Fetch all products

    # You may need to modify this to join with ProductApproval to get admin_id
    approvals_data = []
    for product in products:
        approval = ProductApproval.query.filter_by(product_id=product.id).first()
        approvals_data.append({
            'product': product,
            'admin_id': approval.admin_id if approval else None,  # Get admin_id if exists
            'comments': approval.comments if approval else None,
            'approval_date': approval.approval_date if approval else None,
        })

    return render_template('approvals.html', approvals=approvals_data)

@app.route('/update_product/<int:product_id>', methods=['POST'])
def update_product(product_id):
    # Get the status and comment from the request
    status = request.form.get('status')
    comment = request.form.get('comment')

    # Update the approval status and comments in the database
    product = ProductApproval.query.get(product_id)  # Reference the ProductApproval model
    if product:
        product.approval_status = status
        product.comments = comment
        product.approval_date = datetime.now(timezone.utc)  # Use timezone-aware UTC datetime
        product.updated_at = datetime.now(timezone.utc)  # Use timezone-aware UTC datetime
        db.session.commit()  # Commit changes to the database
        return jsonify({"message": "Product updated successfully!"}), 200
    else:
        return jsonify({"error": "Product not found!"}), 404
    
@app.route('/submit-approval', methods=['POST'])
def submit_approval():
    data = request.get_json()
    product_id = data.get('productId')
    status = data.get('status')
    comment = data.get('comment')

    try:
        product = Product.query.get(product_id)
        if product:
            # Update product approval status
            product.approval_status = status
            product.display_status = 'visible' if status == 'approved' else 'hidden'
            product.updated_at = datetime.now(timezone.utc)

            if status == 'approved':
                product.approval_date = datetime.now(timezone.utc)

                # Create a new ProductApproval record
                new_approval = ProductApproval(
                    product_id=product.id,
                    admin_id=session['user_id'],  # Assuming admin ID is stored in session
                    approval_status=status,
                    approval_date=datetime.now(timezone.utc),
                    comments=comment,
                    product_name=product.name,
                    product_description=product.description,
                    seller_id=product.seller_id,
                    category=product.category,
                    subcategory=product.subcategory
                )
                db.session.add(new_approval)

                # Create notifications
                seller_message = f'Your product "{product.name}" has been approved.'
                create_notification(product.seller_id, seller_message, 'product_approval')

                admin_message = f'Product "{product.name}" (ID: {product_id}) has been approved.'
                create_notification(session['user_id'], admin_message, 'admin_product_approval')  # Assuming admin ID is stored in session

            else:
                product.approval_date = None  # Clear the date if not approved

                # Create notifications for rejection
                seller_message = f'Your product "{product.name}" has been rejected. Comments: {comment}'
                create_notification(product.seller_id, seller_message, 'product_rejection')

                admin_message = f'Product "{product.name}" (ID: {product_id}) has been rejected.'
                create_notification(session['user_id'], admin_message, 'admin_product_rejection')  # Assuming admin ID is stored in session

            db.session.commit()

            return jsonify({
                'success': True,
                'message': 'Product approval updated successfully',
                'productId': product_id,
                'status': status,
                'comment': comment,
                'displayStatus': product.display_status,
                'approvalDate': product.approval_date.isoformat() if product.approval_date else None
            })

        return jsonify({'error': 'Product not found'}), 404

    except Exception as e:
        print(f"Error updating product approval: {str(e)}")
        return jsonify({'error': str(e)}), 500
                                
@app.route('/get-product/<int:product_id>')
def get_product(product_id):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT * FROM products WHERE id = %s', (product_id,))
                product = cur.fetchone()
                if product:
                    # Convert to dictionary for JSON serialization
                    columns = [desc[0] for desc in cur.description]
                    product_dict = dict(zip(columns, product))
                    return jsonify(product_dict)
                else:
                    return jsonify({'error': 'Product not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/api/products')
def get_products():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM products WHERE approval_status = 'approved'")
                products = cur.fetchall()
                return jsonify(products)  # Ensure this returns a JSON response
    except Exception as e:
        print(f"Error fetching products: {str(e)}")
        return jsonify({'error': 'Failed to fetch products'}), 500
    
@app.route('/api/product-stock/<int:product_id>')
def product_stock(product_id):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Get the current stock from the products table
                cur.execute("SELECT stock FROM products WHERE id = %s", (product_id,))
                stock = cur.fetchone()
                if not stock:
                    return jsonify({'success': False, 'message': 'Product not found.'}), 404

                current_stock = stock[0]

                # Calculate stock reserved by PENDING orders
                cur.execute('''
                    SELECT COALESCE(SUM(oi.quantity), 0)
                    FROM order_items oi
                    JOIN orders o ON oi.order_id = o.id
                    WHERE oi.product_id = %s AND o.status = 'PENDING'
                ''', (product_id,))
                reserved_stock = cur.fetchone()[0]

                # Available stock = current stock + reserved stock
                available_stock = current_stock + reserved_stock

                return jsonify({'success': True, 'stock': available_stock})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
                          
@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    user_id = session.get('user_id')
    
    if not user_id:
        return redirect(url_for('login'))  # Redirect to login if the user is not logged in
    
    # Fetch user data from the database
    user = User.query.filter_by(id=user_id).first()
    
    if user:
        if request.method == 'POST':
            # Get cart data from the request
            cart = request.json.get('cart', [])
            return render_template('checkout.html', user=user, cart=cart)
        
        # If it's a GET request, you can initialize an empty cart or fetch from session
        cart = session.get('cart', [])
        return render_template('checkout.html', user=user, cart=cart)
    else:
        return redirect(url_for('login'))  # If no user found, redirect to login
        
@app.route('/comparison')
def comparison():
    return render_template('comparison.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/api/cart', methods=['GET'])
def get_cart():
    """Retrieve the cart from the session."""
    return jsonify(session.get('cart', []))

@app.route('/api/cart/add', methods=['POST'])
def add_to_cart_api():
    """Add an item to the cart."""
    item = request.json
    if not item or 'id' not in item or 'quantity' not in item:
        return jsonify({'error': 'Invalid item data'}), 400

    # Initialize cart if it doesn't exist
    if 'cart' not in session:
        session['cart'] = []

    cart = session['cart']
    existing_item = next((i for i in cart if i['id'] == item['id']), None)

    if existing_item:
        # Update quantity if item already exists
        existing_item['quantity'] += item['quantity']
    else:
        # Add new item to the cart
        cart.append({
            'id': item['id'],
            'name': item['name'],
            'price': item['price'],
            'image': item['image'],
            'quantity': item['quantity']
        })

    session.modified = True  # Mark the session as modified
    return jsonify({'message': 'Item added to cart', 'cart': cart}), 200

@app.route('/api/cart/clear', methods=['POST'])
def clear_cart_api():
    """Clear the cart."""
    session.pop('cart', None)  # Remove the cart from the session
    return jsonify({'message': 'Cart cleared successfully'}), 200

@app.route('/api/cart/update', methods=['PUT'])
def update_cart_api():
    """Update the cart in the session with data from the client."""
    try:
        cart_items = request.json  # Get the cart data from the request
        
        # Validate that cart_items is a list
        if not isinstance(cart_items, list):
            return jsonify({'error': 'Invalid cart data'}), 400

        session['cart'] = cart_items  # Store the cart in the session
        session.modified = True  # Mark the session as modified
        return jsonify({'message': 'Cart updated successfully'}), 200
    except Exception as e:
        print(f"Error updating cart: {e}")  # Log the error for debugging
        return jsonify({'error': 'Failed to update cart'}), 500
            
@app.route('/add_to_cart/<int:product_id>')
def add_to_cart(product_id):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, name, price, image_url FROM products WHERE id = %s", (product_id,))
                product = cur.fetchone()
                if product:
                    cart = session.get('cart', [])
                    item = next((item for item in cart if item['id'] == product[0]), None)
                    if item:
                        item['quantity'] = item.get('quantity', 1) + 1
                    else:
                        cart.append({
                            'id': product[0],
                            'name': product[1],
                            'price': float(product[2]),  # Store as float
                            'image_url': product[3],
                            'quantity': 1
                        })
                    session['cart'] = cart
                    flash(f"{product[1]} has been added to your cart!")
                else:
                    flash("Product not found!")
    except Exception as e:
        logging.error(f"Error adding to cart: {str(e)}")
        flash(f"An error occurred while adding to cart: {str(e)}")
    
    return redirect(url_for('shop'))

@app.route('/remove_from_cart/<int:product_id>', methods=['POST'])
def remove_from_cart(product_id):
    if 'cart' in session:
        session['cart'] = [item for item in session['cart'] if item['id'] != product_id]
        flash("Product removed from cart!")
    else:
        flash("Cart is empty!")
    return redirect(url_for('cart'))

@app.route('/update_cart', methods=['POST'])
def update_cart():
    try:
        cart_items = request.json.get('cart', [])
        session['cart'] = cart_items  # Store the cart in the session
        subtotal = sum(float(item['price']) * int(item.get('quantity', 1)) for item in cart_items)
        shipping = max(subtotal * 0.10, 5)  # 10% of subtotal with $5 minimum
        total = subtotal + shipping
        return jsonify({
            'subtotal': f"{subtotal:.2f}",
            'shipping': f"{shipping:.2f}",
            'total': f"{total:.2f}"
        })
    except Exception as e:
        logging.error(f"Error updating cart: {str(e)}")
        return jsonify({'error': str(e)}), 400
        
@app.route('/clean_cart', methods=['POST'])
def clean_cart():
    try:
        if 'cart' in session:
            # Filter out invalid items
            cart_items = session['cart']
            valid_cart_items = []
            
            for item in cart_items:
                try:
                    # Verify item has all required fields and valid data
                    if (item and 
                        isinstance(item.get('id'), (int, str)) and 
                        isinstance(item.get('name'), str) and 
                        item.get('price') is not None and 
                        isinstance(item.get('image_url'), str) and 
                        isinstance(item.get('quantity'), int)):
                        
                        # Verify product exists in database
                        with get_db_connection() as conn:
                            with conn.cursor() as cur:
                                cur.execute("SELECT id FROM products WHERE id = %s", (item['id'],))
                                if cur.fetchone():
                                    valid_cart_items.append(item)
                
                except Exception as e:
                    logging.error(f"Error validating cart item: {str(e)}")
                    continue
            
            session['cart'] = valid_cart_items
            return jsonify({'message': 'Cart cleaned successfully', 'cart': valid_cart_items})
    
    except Exception as e:
        logging.error(f"Error cleaning cart: {str(e)}")
        return jsonify({'error': str(e)}), 400

@app.route('/cart')
def cart():
    # Get cart from local storage via JavaScript and calculate totals there
    return render_template('cart.html', 
                         subtotal=0.00,  # Initial values, will be updated by JavaScript
                         shipping=0.00,
                         total=0.00)

import logging

@app.route('/create-order', methods=['POST'])
def create_order():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please log in to complete your order'})

    try:
        data = request.get_json()
        cart = data.get('cart', [])
        if not cart:
            return jsonify({'success': False, 'message': 'Your cart is empty'})

        seller_ids = set()  # Use a set to track unique seller IDs

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Calculate subtotal using Decimal for accuracy
                subtotal = sum(Decimal(str(item['price'])) * Decimal(str(item.get('quantity', 1))) for item in cart)

                # Insert the order
                cur.execute(''' 
                    INSERT INTO orders 
                    (user_id, status, subtotal, created_at, updated_at) 
                    VALUES (%s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP) 
                    RETURNING id 
                ''', (session['user_id'], 'PENDING', float(subtotal)))  # Convert to float for DB

                order_id = cur.fetchone()[0]

                # Process each item and decrement stock
                for item in cart:
                    product_id = item['id']
                    quantity = item.get('quantity', 1)

                    # Atomically check and decrement stock
                    cur.execute('''
                        UPDATE products 
                        SET stock = stock - %s 
                        WHERE id = %s AND stock >= %s 
                        RETURNING stock
                    ''', (quantity, product_id, quantity))
                    updated_stock = cur.fetchone()
                    if updated_stock is None:
                        conn.rollback()
                        return jsonify({'success': False, 'message': f'Insufficient stock for Product ID {product_id}'}), 400

                    # Add item to order_items
                    cur.execute(''' 
                        INSERT INTO order_items 
                        (order_id, product_id, quantity, price) 
                        VALUES (%s, %s, %s, %s) 
                    ''', (order_id, product_id, quantity, float(item['price'])))

                    # Get the seller ID for the current product
                    cur.execute('SELECT seller_id FROM products WHERE id = %s', (product_id,))
                    result = cur.fetchone()
                    if result:
                        seller_ids.add(result[0])  # Add the seller ID to the set

                # Fetch the buyer's name
                cur.execute('SELECT name FROM users WHERE id = %s', (session['user_id'],))
                buyer_name = cur.fetchone()[0]  # Fetch the buyer's name

                # Create notifications for each unique seller with the buyer's name
                for seller_id in seller_ids:
                    cur.execute(''' 
                        INSERT INTO notifications (user_id, message, type) 
                        VALUES (%s, %s, %s) 
                    ''', (seller_id, f'A new order (ID: {order_id}) has been placed by {buyer_name}.', 'new_order'))

                # Create a notification for the buyer
                cur.execute(''' 
                    INSERT INTO notifications (user_id, message, type) 
                    VALUES (%s, %s, %s) 
                ''', (session['user_id'], 'Your order has been placed successfully.', 'order_update'))

                conn.commit()

        return jsonify({'success': True, 'order_id': order_id, 'message': 'Order created successfully'})

    except Exception as e:
        conn.rollback()
        logging.error(f"Error creating order: {str(e)}")
        return jsonify({'success': False, 'message': 'An error occurred while processing your order'}), 500
                    
def get_seller_id_from_cart(cart):
    """Get the seller ID from the cart items."""
    # Assuming the cart is a list of dictionaries with product IDs
    seller_ids = set()  # Use a set to avoid duplicates

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            for item in cart:
                product_id = item['id']
                cur.execute('SELECT seller_id FROM products WHERE id = %s', (product_id,))
                result = cur.fetchone()
                if result:
                    seller_ids.add(result[0])  # Add seller ID to the set

    # Return a single seller ID or handle multiple seller IDs as needed
    if len(seller_ids) == 1:
        return seller_ids.pop()  # Return the single seller ID
    else:
        # Handle the case where there are multiple sellers (optional)
        return None  # or raise an exception if needed
                                    
@app.route('/current_orders')
def current_orders():
    if 'user_id' not in session:
        flash('Please log in to view your orders.')
        return redirect(url_for('login'))

    orders = []
    notifications = []
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Fetch order details with all items
                cur.execute('''
                    SELECT 
                        o.id,
                        o.status,
                        o.created_at,
                        o.updated_at,
                        p.name,
                        p.image_url,
                        oi.quantity,
                        oi.price,
                        o.expected_delivery_start,
                        o.expected_delivery_end,
                        o.shipped_date,
                        o.delivered_date,
                        o.in_transit_date,
                        (oi.quantity * oi.price) as item_total,
                        o.confirmed_receipt,
                        oi.has_rated
                    FROM orders o
                    JOIN order_items oi ON o.id = oi.order_id
                    JOIN products p ON oi.product_id = p.id
                    WHERE o.user_id = %s
                    ORDER BY o.created_at DESC
                ''', (session['user_id'],))
                
                order_data = cur.fetchall()
                order_subtotals = {}
                order_items = {}  # To store all items per order for rating check

                # Process raw data into order structure
                for row in order_data:
                    order_id = row[0]
                    item_total = row[13]
                    
                    if order_id not in order_subtotals:
                        order_subtotals[order_id] = Decimal('0.00')
                        order_items[order_id] = []
                    order_subtotals[order_id] += Decimal(str(item_total))  # Ensure decimal handling
                    order_items[order_id].append({
                        'name': row[4],
                        'has_rated': row[15]
                    })

                    if order_id not in [o['id'] for o in orders]:
                        orders.append({
                            'id': order_id,
                            'status': row[1],
                            'created_at': row[2].strftime('%Y-%m-%d %H:%M:%S') if isinstance(row[2], datetime) else row[2],
                            'updated_at': row[3].strftime('%Y-%m-%d %H:%M:%S') if isinstance(row[3], datetime) else row[3],
                            'name': row[4],
                            'image_url': row[5],
                            'quantity': row[6],
                            'price': row[7],
                            'item_total': item_total,
                            'expected_delivery_start': row[8].strftime('%Y-%m-%d') if isinstance(row[8], datetime) else row[8],
                            'expected_delivery_end': row[9].strftime('%Y-%m-%d') if isinstance(row[9], datetime) else row[9],
                            'shipped_date': row[10].strftime('%Y-%m-%d') if isinstance(row[10], datetime) else row[10],
                            'delivered_date': row[11],
                            'in_transit_date': row[12].strftime('%Y-%m-%d') if isinstance(row[12], datetime) else row[12],
                            'confirmed_receipt': row[14],
                            'all_rated': False  # Placeholder, will be updated below
                        })

            # Update all_rated for each order
            for order in orders:
                order_items_list = order_items.get(order['id'], [])
                if order_items_list:
                    order['all_rated'] = all(item['has_rated'] == 1 for item in order_items_list)

            # Calculate totals
            for order in orders:
                subtotal = order_subtotals.get(order['id'], Decimal('0.00'))
                shipping_fee = Decimal('50.00')  # Fixed shipping fee of ₱50
                total = subtotal + shipping_fee
                order['shipping_fee'] = float(shipping_fee)
                order['subtotal'] = float(subtotal)
                order['total'] = float(total)

                if isinstance(order['delivered_date'], str):
                    order['delivered_date'] = datetime.strptime(order['delivered_date'], '%Y-%m-%d')

                if order['status'] == 'DELIVERED' and not order['confirmed_receipt']:
                    with conn.cursor() as notify_cur:
                        notify_cur.execute('''
                            INSERT INTO notifications (user_id, message, type) 
                            VALUES (%s, %s, %s)
                        ''', (session['user_id'], f'Your order #{order["id"]} has been delivered.', 'order_update'))
                        conn.commit()

            # Add status icons
            status_icons = {
                'PENDING': 'clock',
                'APPROVED': 'check',
                'SHIPPED': 'truck',
                'IN_TRANSIT': 'motorcycle',
                'DELIVERED': 'box',
                'CANCELLED': 'times'
            }

            for order in orders:
                order['icon'] = status_icons.get(order['status'].upper(), 'question')

            # Fetch notifications
            with conn.cursor() as notify_cur:
                notify_cur.execute('''
                    SELECT id, message, created_at FROM notifications 
                    WHERE user_id = %s 
                    ORDER BY created_at DESC
                ''', (session['user_id'],))
                notifications = notify_cur.fetchall()

        return render_template('current_orders.html', orders=orders, notifications=notifications)
    
    except Exception as e:
        logging.error(f"Error fetching current orders: {str(e)}")
        traceback.print_exc()
        flash('An error occurred while fetching your orders.')
        return render_template('current_orders.html', orders=[])
                                    
@app.route('/orders')
def orders():
    if 'user_id' not in session or session.get('role') != 'seller':
        flash('Please log in as a seller to view orders.')
        return redirect(url_for('login'))

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('''
                    SELECT 
                        o.id, 
                        u.name as buyer_name, 
                        p.name, 
                        oi.quantity, 
                        oi.price, 
                        (oi.quantity * oi.price) + 50.00 AS total,  -- Fixed shipping fee of ₱50
                        o.status, 
                        o.shipped_date,
                        o.delivered_date,
                        o.expected_delivery_start,
                        o.expected_delivery_end,
                        o.in_transit_date,
                        o.created_at 
                    FROM orders o 
                    JOIN order_items oi ON o.id = oi.order_id 
                    JOIN products p ON oi.product_id = p.id 
                    JOIN users u ON o.user_id = u.id 
                    WHERE p.seller_id = %s 
                    ORDER BY o.created_at DESC
                ''', (session['user_id'],))

                orders = []
                for row in cur.fetchall():
                    orders.append({
                        'id': row[0],
                        'buyer_name': row[1],
                        'name': row[2],
                        'quantity': row[3],
                        'price': row[4],
                        'total': row[5],  # Use total with fixed ₱50 shipping
                        'status': row[6],
                        'shipped_date': row[7],
                        'delivered_date': row[8],
                        'expected_delivery_start': row[9],
                        'expected_delivery_end': row[10],
                        'in_transit_date': row[11],
                        'created_at': row[12]
                    })

        return render_template('orders.html', orders=orders)
    except Exception as e:
        print(f"Error fetching seller orders: {str(e)}")
        traceback.print_exc()
        flash('An error occurred while fetching orders.')
        return redirect(url_for('dashboard'))
    
                                                                                                                
@app.route('/seller/orders')
def seller_orders():
    print("seller_orders function called")
    if 'user_id' not in session or session.get('role') != 'seller':
        return redirect(url_for('login'))

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                print(f"Fetching orders for seller ID: {session['user_id']}")
                cur.execute('''
                    SELECT 
                        o.id, 
                        u.name AS buyer_name, 
                        p.name, 
                        oi.quantity, 
                        oi.price, 
                        (oi.quantity * oi.price) + 50.00 AS total,  -- Align with /orders
                        o.status, 
                        o.shipped_date,
                        o.delivered_date,
                        o.expected_delivery_start,
                        o.expected_delivery_end,
                        o.in_transit_date,
                        o.created_at 
                    FROM orders o 
                    JOIN order_items oi ON o.id = oi.order_id 
                    JOIN products p ON oi.product_id = p.id 
                    JOIN users u ON o.user_id = u.id 
                    WHERE p.seller_id = %s 
                    ORDER BY o.created_at DESC
                ''', (session['user_id'],))

                orders = []
                for row in cur.fetchall():
                    orders.append({
                        'id': row[0],
                        'buyer_name': row[1],
                        'name': row[2],
                        'quantity': row[3],
                        'price': row[4],
                        'total': row[5],
                        'status': row[6],
                        'shipped_date': row[7],
                        'delivered_date': row[8],
                        'expected_delivery_start': row[9],
                        'expected_delivery_end': row[10],
                        'in_transit_date': row[11],
                        'created_at': row[12]
                    })
                print(f"Fetched {len(orders)} orders: {orders}")

        return render_template('orders.html', orders=orders)
    except psycopg2.Error as e:
        print(f"Database error fetching seller orders: {str(e)}")
        traceback.print_exc()
        flash(f"Database error while fetching orders: {str(e)}")
        return redirect(url_for('dashboard'))
    except Exception as e:
        print(f"Unexpected error fetching seller orders: {str(e)}")
        traceback.print_exc()
        flash('An unexpected error occurred while fetching orders.')
        return redirect(url_for('dashboard'))    

@app.route('/update-order-status/<int:order_id>', methods=['POST'])
def update_order_status(order_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized access'}), 403

    new_status = request.json.get('status')
    in_transit_date = request.json.get('in_transit_date')

    valid_statuses = ['IN_TRANSIT', 'DELIVERED', 'RECEIVED', 'APPROVED', 'CANCELLED']
    if new_status not in valid_statuses:
        return jsonify({'success': False, 'message': 'Invalid status update'}), 400

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT role FROM users WHERE id = %s', (session['user_id'],))
                user = cur.fetchone()
                if user is None:
                    return jsonify({'success': False, 'message': 'User not found'}), 404
                user_role = user[0]

                cur.execute('SELECT status, user_id, in_transit_date, confirmed_receipt FROM orders WHERE id = %s', (order_id,))
                order = cur.fetchone()
                if order is None:
                    return jsonify({'success': False, 'message': 'Order not found'}), 404

                current_status, order_user_id, current_in_transit_date, confirmed_receipt = order

                if new_status == 'DELIVERED':
                    if user_role == 'seller':
                        return jsonify({'success': False, 'message': 'Sellers cannot mark orders as delivered'}), 403
                    if user_role == 'user' and order_user_id != session['user_id']:
                        return jsonify({'success': False, 'message': 'Only the buyer can mark the order as delivered'}), 403
                    if user_role == 'rider' and current_status != 'IN_TRANSIT':
                        return jsonify({'success': False, 'message': 'Order must be IN_TRANSIT to mark as DELIVERED'}), 400
                elif new_status == 'RECEIVED':
                    if user_role != 'user' or order_user_id != session['user_id']:
                        return jsonify({'success': False, 'message': 'Only the buyer can mark the order as received'}), 403
                    if current_status != 'DELIVERED':
                        return jsonify({'success': False, 'message': 'Order must be DELIVERED to mark as RECEIVED'}), 400
                    if confirmed_receipt == 1:
                        return jsonify({'success': False, 'message': 'Order already confirmed as received'}), 400
                elif new_status == 'CANCELLED':
                    if current_status in ['DELIVERED', 'RECEIVED']:
                        return jsonify({'success': False, 'message': 'Cannot cancel a delivered or received order'}), 400

                print(f"Updating order {order_id} to status: {new_status}, in_transit_date: {in_transit_date}")

                # Increment stock if cancelling
                if new_status == 'CANCELLED':
                    cur.execute('SELECT product_id, quantity FROM order_items WHERE order_id = %s', (order_id,))
                    for item in cur.fetchall():
                        product_id, quantity = item
                        cur.execute('UPDATE products SET stock = stock + %s WHERE id = %s', (quantity, product_id))
                        logging.info(f"Restored stock for Product ID {product_id} by {quantity} due to order cancellation")

                if new_status == 'IN_TRANSIT':
                    cur.execute('''
                        UPDATE orders 
                        SET status = %s, updated_at = CURRENT_TIMESTAMP,
                            in_transit_date = %s
                        WHERE id = %s
                    ''', (new_status, in_transit_date, order_id))
                elif new_status == 'RECEIVED':
                    cur.execute('''
                        UPDATE orders 
                        SET status = %s, updated_at = CURRENT_TIMESTAMP,
                            confirmed_receipt = 1
                        WHERE id = %s
                    ''', (new_status, order_id))
                else:
                    cur.execute('''
                        UPDATE orders 
                        SET status = %s, updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    ''', (new_status, order_id))

                if new_status == 'IN_TRANSIT':
                    cur.execute(''' 
                        INSERT INTO notifications (user_id, message, type) 
                        VALUES (%s, %s, %s) 
                    ''', (order_user_id, f'Order ID {order_id} is out for delivery.', 'order_update'))

                if new_status == 'DELIVERED':
                    cur.execute('UPDATE orders SET delivered_date = CURRENT_TIMESTAMP WHERE id = %s', (order_id,))
                    cur.execute('SELECT product_id, quantity FROM order_items WHERE order_id = %s', (order_id,))
                    order_items = cur.fetchall()

                    seller_ids = set()
                    total_amount = Decimal(0)

                    for item in order_items:
                        product_id = item[0]
                        quantity = item[1]
                        cur.execute('SELECT price, seller_id FROM products WHERE id = %s', (product_id,))
                        product = cur.fetchone()
                        if product:
                            price = Decimal(product[0])
                            seller_id = product[1]
                            total_amount += price * quantity
                            seller_ids.add(seller_id)

                    commission_rate = Decimal(0.05)
                    commission_amount = total_amount * commission_rate    
                    cur.execute('''
                        INSERT INTO sales_report (order_id, total_amount, admin_commission)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (order_id) DO UPDATE SET 
                            total_amount = EXCLUDED.total_amount,
                            admin_commission = EXCLUDED.admin_commission
                    ''', (order_id, total_amount, commission_amount))

                    for seller_id in seller_ids:
                        cur.execute(''' 
                            INSERT INTO notifications (user_id, message, type) 
                            VALUES (%s, %s, %s) 
                        ''', (seller_id, f'Order ID {order_id} has been delivered to the buyer.', 'order_update'))

                    admin_user_id = 4
                    cur.execute(''' 
                        INSERT INTO notifications (user_id, message, type) 
                        VALUES (%s, %s, %s) 
                    ''', (admin_user_id, f'Commission earned for Order ID {order_id}: ₱{commission_amount:.2f}', 'commission_update'))

                if new_status == 'RECEIVED':
                    for seller_id in seller_ids:
                        cur.execute(''' 
                            INSERT INTO notifications (user_id, message, type) 
                            VALUES (%s, %s, %s) 
                        ''', (seller_id, f'Order ID {order_id} has been received by the buyer.', 'order_update'))

                if new_status == 'CANCELLED':
                    cur.execute(''' 
                        INSERT INTO notifications (user_id, message, type) 
                        VALUES (%s, %s, %s) 
                    ''', (order_user_id, f'Order ID {order_id} has been cancelled by the seller.', 'order_update'))

                conn.commit()

        return jsonify({'success': True, 'message': 'Order status updated successfully'})
    except Exception as e:
        conn.rollback()
        logging.error(f"Error updating order status: {str(e)}")
        return jsonify({'success': False, 'message': 'An error occurred while updating the order status.'}), 500
                                                                                                  
@app.route('/update-order-eta/<int:order_id>', methods=['POST'])
def update_order_eta(order_id):
    try:
        data = request.get_json()
        expected_delivery_start = data.get('eta_start')
        expected_delivery_end = data.get('eta_end')

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Fetch the existing shipped_date before updating
                cur.execute('SELECT shipped_date FROM orders WHERE id = %s', (order_id,))
                existing_shipped_date = cur.fetchone()

                if existing_shipped_date is None:
                    return jsonify({'success': False, 'message': 'Order not found'}), 404
                
                existing_shipped_date = existing_shipped_date[0]

                # Check the current status of the order
                cur.execute('SELECT status FROM orders WHERE id = %s', (order_id,))
                current_status = cur.fetchone()

                if current_status is None:
                    return jsonify({'success': False, 'message': 'Order not found'}), 404

                if current_status[0] == 'DELIVERED':
                    return jsonify({'success': False, 'message': 'Cannot update a delivered order'}), 400

                # Proceed to update the order
                cur.execute('''
                    UPDATE orders 
                    SET status = 'SHIPPED',
                        shipped_date = CURRENT_DATE,
                        expected_delivery_start = %s,
                        expected_delivery_end = %s,
                        updated_at = CURRENT_TIMESTAMP 
                    WHERE id = %s
                    RETURNING shipped_date
                ''', (expected_delivery_start, expected_delivery_end, order_id))

                result = cur.fetchone()
                conn.commit()

                if result:
                    shipped_date = result[0]
                    return jsonify({
                        'success': True, 
                        'message': 'Expected delivery dates updated successfully',
                        'existing_shipped_date': existing_shipped_date.strftime('%m/%d/%y') if existing_shipped_date else 'N/A',
                        'updated_shipped_date': shipped_date.strftime('%m/%d/%y') if shipped_date else 'N/A'
                    })
                else:
                    return jsonify({'success': False, 'message': 'Order not found or status not updated'}), 404

    except Exception as e:
        print(f"Error updating expected delivery dates: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500
                            
@app.route('/cancel-order/<int:order_id>', methods=['POST'])
def cancel_order(order_id):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Verify the order exists and belongs to the user
                cur.execute('SELECT user_id, status FROM orders WHERE id = %s', (order_id,))
                order = cur.fetchone()
                if order is None:
                    return jsonify({'success': False, 'message': 'Order not found'}), 404
                if order[0] != session['user_id']:
                    return jsonify({'success': False, 'message': 'Unauthorized to cancel this order'}), 403
                if order[1] in ['DELIVERED', 'RECEIVED']:
                    return jsonify({'success': False, 'message': 'Cannot cancel a delivered or received order'}), 400

                # Increment stock for each item
                cur.execute('SELECT product_id, quantity FROM order_items WHERE order_id = %s', (order_id,))
                for item in cur.fetchall():
                    product_id, quantity = item
                    cur.execute('UPDATE products SET stock = stock + %s WHERE id = %s', (quantity, product_id))
                    logging.info(f"Restored stock for Product ID {product_id} by {quantity} due to order cancellation")

                # Update order status
                cur.execute('UPDATE orders SET status = %s WHERE id = %s', ('CANCELLED', order_id))

                # Notify the seller(s)
                cur.execute('SELECT DISTINCT p.seller_id FROM order_items oi JOIN products p ON oi.product_id = p.id WHERE oi.order_id = %s', (order_id,))
                seller_ids = cur.fetchall()
                for seller_id in seller_ids:
                    cur.execute('''
                        INSERT INTO notifications (user_id, message, type)
                        VALUES (%s, %s, %s)
                    ''', (seller_id[0], f'Order ID {order_id} has been cancelled by the buyer.', 'order_update'))

                conn.commit()
        return jsonify({'success': True, 'message': 'Order cancelled successfully'})
    except Exception as e:
        conn.rollback()
        print(f"Error cancelling order: {str(e)}")
        return jsonify({'success': False, 'message': 'Error cancelling order'}), 500
        
@app.route('/remove-order/<int:order_id>', methods=['POST'])
def remove_order(order_id):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('''
                    DELETE FROM orders 
                    WHERE id = %s 
                    AND (status = 'CANCELLED' OR (status = 'DELIVERED' AND confirmed_receipt = 1))
                    RETURNING id
                ''', (order_id,))
                
                deleted_order = cur.fetchone()
                conn.commit()

                if deleted_order:
                    return jsonify({
                        'success': True,
                        'message': 'Order removed successfully'
                    }), 200
                else:
                    return jsonify({
                        'success': False,
                        'message': 'Order not found, not cancelled, or not confirmed as received'
                    }), 404

    except Exception as e:
        print(f"Error removing order: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error removing order: {str(e)}'
        }), 500
                                           
@app.route('/profile')
def profile():
    return render_template('profile.html')

@app.route('/shop')
def shop():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Fetch approved, visible products along with their subcategories
                cur.execute("""
                    SELECT id, name, description, price, image_url, category, subcategory, stock 
                    FROM products 
                    WHERE approval_status = 'approved' 
                    AND display_status = 'visible'
                    AND is_archived = FALSE
                """)
                products = cur.fetchall()
                print(f"Fetched {len(products)} approved and visible products")
    except Exception as e:
        print(f"Error fetching products: {str(e)}")
        flash(f"Error fetching products: {str(e)}")
        products = []

    return render_template('shop.html', products=products)

@app.route('/purchases')
def purchases():
    # You can fetch purchase history from your database here if needed
    # For now, we will just render the purchases.html template
    return render_template('purchases.html')

@app.route('/manage_products', methods=['GET'])
def manage_products():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        p.id,
                        p.name,
                        p.description,
                        p.price,
                        p.stock,
                        p.sku,
                        p.category,
                        p.subcategory,
                        p.variant,
                        p.image_url,
                        p.additional_images,
                        p.material,
                        p.dimensions,
                        p.weight,
                        p.shipping_weight,
                        p.shipping_dimensions,
                        p.indoor_outdoor,
                        p.color,
                        p.brand,
                        p.power_source,
                        p.warranty,
                        p.seller_id,
                        p.created_at,
                        p.updated_at,
                        p.approval_status,
                        pa.comments AS admin_comments,
                        p.display_status,
                        p.rating,
                        p.reviews,
                        p.tags,
                        p.sale_price,
                        p.is_on_sale,
                        p.availability_status,
                        p.discounted_price,
                        p.approval_date
                    FROM products p
                    LEFT JOIN product_approvals pa ON p.id = pa.product_id  -- Join with product_approvals
                    WHERE p.is_archived = FALSE  -- Filter out archived products
                    ORDER BY p.id DESC
                """)
                products = cur.fetchall()
                print(f"Fetched {len(products)} products")
        return render_template('manage_products.html', products=products)
    except Exception as e:
        print(f"Error fetching products: {str(e)}")
        flash(f"Error fetching products: {str(e)}")
        return render_template('manage_products.html', products=[])
    
@app.route('/archived_products', methods=['GET'])
def archived_products():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        id,
                        name,
                        description,
                        price,
                        stock,
                        sku,
                        category,
                        subcategory,
                        variant,
                        image_url,
                        additional_images,
                        material,
                        dimensions,
                        weight,
                        shipping_weight,
                        shipping_dimensions,
                        indoor_outdoor,
                        color,
                        brand,
                        power_source,
                        warranty,
                        seller_id,
                        created_at,
                        updated_at,
                        approval_status,
                        admin_comments,
                        display_status,
                        rating,
                        reviews,
                        tags,
                        sale_price,
                        is_on_sale,
                        availability_status,
                        discounted_price,
                        approval_date
                    FROM products
                    WHERE is_archived = TRUE
                    ORDER BY id DESC
                """)
                archived_products = cur.fetchall()
                print(f"Fetched {len(archived_products)} archived products")
        return render_template('archived_products.html', archived_products=archived_products)
    except Exception as e:
        print(f"Error fetching archived products: {str(e)}")
        flash('Error fetching archived products.', 'error')
        return render_template('archived_products.html', archived_products=[])

    
@app.route('/products/archive/<int:product_id>', methods=['POST'])
def admin_archive_product(product_id):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('UPDATE products SET is_archived = TRUE WHERE id = %s', (product_id,))
                conn.commit()
                flash('Product archived successfully.', 'success')
    except Exception as e:
        print(f"Error archiving product: {str(e)}")
        flash('Error archiving product.', 'error')
    return redirect(url_for('manage_products'))

@app.route('/products/archived', methods=['GET'])
def product_archive():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT * FROM products WHERE is_archived = TRUE')
                archived_products = cur.fetchall()
        return render_template('archived_products.html', archived_products=archived_products)
    except Exception as e:
        print(f"Error fetching archived products: {str(e)}")
        flash('Error fetching archived products.', 'error')
        return render_template('archived_products.html', archived_products=[])

@app.route('/products/unarchive/<int:product_id>', methods=['POST'])
def unarchive_product(product_id):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('UPDATE products SET is_archived = FALSE WHERE id = %s', (product_id,))
                conn.commit()
                flash('Product unarchived successfully.', 'success')
    except Exception as e:
        print(f"Error unarchiving product: {str(e)}")
        flash('Error unarchiving product.', 'error')
    return redirect(url_for('product_archive'))

@app.route('/products/delete/<int:product_id>', methods=['POST'])
def permanent_delete_product(product_id):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('DELETE FROM products WHERE id = %s', (product_id,))
                conn.commit()
                flash('Product deleted successfully.', 'success')
    except Exception as e:
        print(f"Error deleting product: {str(e)}")
        flash('Error deleting product.', 'error')
    return redirect(url_for('admin_product_archive'))
        
                
@app.route('/account_settings')
def account_settings():
    return render_template('account_settings.html')

@app.route('/register', methods=['GET'])
def register():
    countries = load_countries()
    return render_template('register.html', countries=countries)

@app.route('/register_seller', methods=['GET'])
def register_seller():
    countries = load_countries()
    return render_template('register_seller.html', countries=countries)

@app.route('/submit_form', methods=['POST'])
def submit_form():
    name = request.form['name']
    email = request.form['email']
    password = request.form['password']
    gender = request.form['gender']
    country = request.form['country']
    street_address = request.form['street_address']
    city = request.form['city']
    province = request.form['province']
    zip_code = request.form['zip_code']
    phone = request.form['phone']
    role = 'user'  # Default role to 'user'

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                logging.info("Checking if user exists...")
                cur.execute('SELECT * FROM users WHERE email = %s', (email,))
                existing_user = cur.fetchone()

                if existing_user:
                    flash("Email already exists! Please use a different email.")
                    return redirect(url_for('register'))

                logging.info("Inserting new user into the database...")
                cur.execute('''
                    INSERT INTO users (name, email, password, gender, country, street_address, city, province, zip_code, phone, role, is_archived, otp_verified)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', (name, email, password, gender, country, street_address, city, province, zip_code, phone, role, False, False))
                conn.commit()
                logging.info("User inserted successfully.")

                # Generate and send OTP
                otp = generate_otp()
                send_otp(email, otp)

                # Save OTP and user ID in session for verification
                session['otp'] = otp
                session['user_id'] = cur.lastrowid  # Assuming the database generates a unique user ID

                flash("OTP sent to your email. Please verify.", 'info')
                return redirect(url_for('verify_otp'))

    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        flash(f"An error occurred: {str(e)}")

    return redirect(url_for('register'))

@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    if session.get('role') != 'user':  # Ensure only users can verify OTP
        flash("OTP verification is not applicable for your role.", 'error')
        return redirect(url_for('index'))

    if request.method == 'POST':
        entered_otp = request.form['otp']
        stored_otp = session.get('otp')

        if entered_otp == str(stored_otp):  # Compare entered OTP with stored OTP
            session['otp_verified'] = True  # Mark OTP as verified

            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute('UPDATE users SET otp_verified = TRUE WHERE email = %s', (session['email'],))
                    conn.commit()

            flash('OTP verified successfully!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid OTP. Please try again.', 'error')

    return render_template('verify_otp.html')


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/submit_seller_form', methods=['POST'])
def submit_seller_form():
    name = request.form['name']
    email = request.form['email']
    password = request.form['password']
    gender = request.form['gender']
    country = request.form['country']
    street_address = request.form['street_address']
    city = request.form['city']
    province = request.form['province']
    zip_code = request.form['zip_code']
    phone = request.form['phone']
    role = 'seller'

    business_permit_file = request.files['business_permit']
    valid_id_file = request.files['valid_id']

    if business_permit_file and allowed_file(business_permit_file.filename):
        filename = secure_filename(business_permit_file.filename)
        permit_folder = app.config['BUSINESS_PERMIT_UPLOAD_FOLDER']
        os.makedirs(permit_folder, exist_ok=True)
        file_path = os.path.join(permit_folder, filename)
        business_permit_file.save(file_path)
    else:
        flash("Invalid file format for business permit. Please upload an image file.")
        return redirect(url_for('register_seller'))

    if valid_id_file and allowed_file(valid_id_file.filename):
        id_filename = secure_filename(valid_id_file.filename)
        id_folder = app.config['VALID_ID_UPLOAD_FOLDER']
        os.makedirs(id_folder, exist_ok=True)
        id_file_path = os.path.join(id_folder, id_filename)
        valid_id_file.save(id_file_path)
    else:
        flash("Invalid file format for valid ID. Please upload a valid image or PDF.")
        return redirect(url_for('register_seller'))

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Check for existing email
                cur.execute('SELECT * FROM users WHERE email = %s', (email,))
                if cur.fetchone():
                    flash("Email already exists! Please use a different email.")
                    return redirect(url_for('register_seller'))

                # Insert seller into database
                cur.execute('''
                    INSERT INTO users (
                        name, email, password, gender, country, street_address, city, province, zip_code, phone, role, is_archived, business_permit, valid_id
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', (name, email, password, gender, country, street_address, city, province, zip_code, phone, role, False, filename, id_filename))
                conn.commit()

                # Create notifications
                cur.execute('SELECT id FROM users WHERE email = %s', (email,))
                seller_id = cur.fetchone()[0]
                admin_user_id = 28  # Replace with your admin user ID

                create_notification(admin_user_id, f'New seller registered: {name} ({email})', 'seller_registration')
                create_notification(seller_id, f'Thank you for registering as a seller, {name}. Your application is under review.', 'seller_registration_confirmation')

                flash("Registration successful! Please wait for Admin Approval.")
                return redirect(url_for('login'))

    except Exception as e:
        flash(f"An error occurred: {str(e)}")
        return redirect(url_for('register_seller'))



@app.route('/index')
def index():
    if 'email' not in session:
        return redirect(url_for('login'))
    
    messages = get_flashed_messages(with_categories=True)
    response = make_response(render_template('index.html', email=session['email'], messages=messages))
    response.headers['Cache-Control'] = 'no-store'
    return response

@app.route('/logout')
def logout():
    session.pop('email', None)
    session.pop('role', None)
    flash('You have been logged out.')
    response = make_response(redirect(url_for('login')))
    response.headers['Cache-Control'] = 'no-store'
    return response

@app.route('/prevent_back_navigation')
def prevent_back_navigation():
    if 'email' in session:
        return render_template('prevent_back.html')
    return redirect(url_for('login'))

@app.route('/admin/users', methods=['GET'])
@admin_required
def admin_users():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Fetch users, excluding admins and users with 'user' role, and without the 'role' field
            cur.execute('''
                SELECT id, name, email, gender, country, business_permit, valid_id, approval_status
                FROM users
                WHERE is_archived = FALSE AND role != 'admin' AND role != 'user'
            ''')
            users = cur.fetchall()

            # Fetch notifications for the admin user
            cur.execute('''
                SELECT id, message, is_read, created_at
                FROM notifications
                WHERE user_id = %s
                ORDER BY created_at DESC
            ''', (session['user_id'],))  # Corrected the syntax here
            notifications = cur.fetchall()

    return render_template('admin_users.html', users=users, notifications=notifications)

@app.route('/uploads/<path:subpath>')
def serve_uploads(subpath):
    uploads_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    return send_from_directory(uploads_folder, subpath)


@app.route('/admin/accounts', methods=['GET'])
@admin_required
def accounts():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('''
                SELECT id, name, email, phone, street_address, city, province, zip_code, approval_status
                FROM users
                WHERE is_archived = FALSE AND role = %s
            ''', ('user',))
            
            users = cur.fetchall()
            
    return render_template('accounts.html', users=users)

@app.route('/admin/accounts/<int:user_id>', methods=['POST'])
@admin_required
def approve_user(user_id):
    """Approve a user by updating their approval_status in the database."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Update the user approval status
            cur.execute('''
                UPDATE users 
                SET approval_status = %s 
                WHERE id = %s 
            ''', ('approved', user_id))
            conn.commit()

            # Create a notification for the admin
            cur.execute('''
                INSERT INTO notifications (user_id, message, type) 
                VALUES (%s, %s, %s)
            ''', (session['user_id'], f'User  {user_id} has been approved.', 'admin'))
            conn.commit()

    flash('User  has been approved successfully! ', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/approve_user2/<int:user_id>', methods=['POST'])
@admin_required
def approve_user2(user_id):
    """Approve a seller by updating their approval_status and role in the database."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Debugging - Check if the user exists
                cur.execute('SELECT * FROM users WHERE id = %s', (user_id,))
                user = cur.fetchone()
                print(f"User  before update: {user}")  # Add a debug print statement

                # Update both approval_status and role to ensure the seller role is retained
                cur.execute('''
                    UPDATE users
                    SET approval_status = %s, approved = %s, role = %s
                    WHERE id = %s
                ''', ('approved', True, 'seller', user_id))
                conn.commit()  # Commit the changes to the database

                # Debugging - Check the result after update
                cur.execute('SELECT * FROM users WHERE id = %s', (user_id,))
                user = cur.fetchone()
                print(f"User  after update: {user}")  # Add a debug print statement
        
        # Create a notification message
        notification_message = f'Seller {user[1]} (ID: {user_id}) has been approved.'  # Assuming user[1] is the name
        create_notification(user_id, notification_message, 'user_approval')  # Notify the seller
        # Optionally, you can notify the admin as well
        create_notification(28, f'You have approved seller {user[1]} (ID: {user_id}).', 'admin_notification')  # Assuming admin ID is 4

        flash('Seller has been approved successfully!', 'success')
    except Exception as e:
        flash(f"An error occurred: {str(e)}", 'error')
    
    return redirect(url_for('admin_users'))

@app.route('/admin/users/add', methods=['GET', 'POST'])
@admin_required
def admin_add_user():
    countries = load_countries()

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        gender = request.form['gender']
        country = request.form['country']
        role = request.form.get('role', 'user')

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute('INSERT INTO users (name, email, password, gender, country, role) VALUES (%s, %s, %s, %s, %s, %s)',
                                (name, email, password, gender, country, role))
                    conn.commit()
                    flash('User added successfully!')
                    return redirect(url_for('admin_users'))
        except Exception as e:
            flash(f"An error occurred: {str(e)}")

    return render_template('admin_add_user.html', countries=countries)

@app.route('/admin/users/edit/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_user(user_id):
    countries = load_countries()
    conn = get_db_connection()

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        gender = request.form['gender']
        country = request.form['country']
        role = request.form.get('role', 'user')  # Default to 'user'

        try:
            with conn.cursor() as cur:
                cur.execute('UPDATE users SET name=%s, email=%s, password=%s, gender=%s, country=%s, role=%s WHERE id=%s',
                            (name, email, (password), gender, country, role, user_id))
                conn.commit()
                flash('User updated successfully!')
                return redirect(url_for('admin_users'))

        except Exception as e:
            flash(f"An error occurred: {str(e)}")
    
    with conn.cursor() as cur:
        cur.execute('SELECT * FROM users WHERE id=%s', (user_id,))
        user = cur.fetchone()
    return render_template('admin_edit_user.html', user=user, countries=countries)

@app.route('/admin/users/delete/<int:user_id>', methods=['POST'])
@admin_required
def admin_delete_user(user_id):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('DELETE FROM users WHERE id=%s', (user_id,))
                conn.commit()
                flash('User deleted successfully!')
    except Exception as e:
        flash(f"An error occurred: {str(e)}")
    return redirect(url_for('admin_users'))

@app.route('/admin/archive_user/<int:user_id>', methods=['POST'])
@admin_required
def admin_archive_user(user_id):
    """Archive a user by setting their is_archived field to True and notify them via email."""
    try:
        user_email = None
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Retrieve the user's email address
                cur.execute('''
                    SELECT email
                    FROM users
                    WHERE id = %s
                ''', (user_id,))
                user = cur.fetchone()
                if not user:
                    flash('User not found.', 'error')
                    return redirect(url_for('admin_users'))
                
                user_email = user[0]

                # Update the user's archive status
                cur.execute('''
                    UPDATE users
                    SET is_archived = TRUE
                    WHERE id = %s
                ''', (user_id,))
                conn.commit()  # Commit the changes to the database

                # Create a notification for the admin
                notification_message = f'User ID {user_id} has been archived.'
                create_notification(session['user_id'], notification_message, 'user_archive')  # Assuming admin ID is stored in session

        # Send an email notification to the user
        if user_email:
            subject = "Your Account Has Been Archived"
            body = f"""
            Dear User,

            Your account with ID {user_id} has been archived by an administrator. If you believe this was done in error, please contact our support team.

            Best regards,
            The Admin Team
            """
            send_email(user_email, subject, body)

        flash('User has been archived successfully, and an email notification was sent.', 'success')
    except Exception as e:
        flash(f"An error occurred: {str(e)}", 'error')
    
    return redirect(url_for('admin_users'))

@app.route('/admin/users/archive', methods=['GET'])
@admin_required
def admin_user_archive():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM users WHERE is_archived = TRUE')
            archived_users = cur.fetchall()
    return render_template('archive.html', archived_users=archived_users)

@app.route('/admin/users/unarchive/<int:user_id>', methods=['POST'])
@admin_required
def admin_unarchive_user(user_id):
    try:
        user_email = None
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Retrieve the user's email address
                cur.execute('''
                    SELECT email
                    FROM users
                    WHERE id = %s
                ''', (user_id,))
                user = cur.fetchone()
                if not user:
                    flash('User not found.', 'error')
                    return redirect(url_for('admin_user_archive'))

                user_email = user[0]

                # Unarchive the user
                cur.execute('UPDATE users SET is_archived = FALSE WHERE id = %s', (user_id,))
                conn.commit()

                # Create a notification for the admin
                notification_message = f'User ID {user_id} has been unarchived.'
                create_notification(session['user_id'], notification_message, 'user_unarchive')

        # Send an email notification to the user
        if user_email:
            subject = "Your Account Has Been Unarchived"
            body = f"""
            Dear User,

            Your account with ID {user_id} has been unarchived and is now active. Welcome back!

            Best regards,
            The Admin Team
            """
            send_email(user_email, subject, body)

        flash('User unarchived successfully, and an email notification was sent.', 'success')
    except Exception as e:
        flash(f"An error occurred: {str(e)}", 'error')
    return redirect(url_for('admin_user_archive'))

@app.route('/admin/users/delete/<int:user_id>', methods=['POST'])
@admin_required
def admin_permanent_delete_user(user_id):
    try:
        user_email = None
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Retrieve the user's email address
                cur.execute('''
                    SELECT email
                    FROM users
                    WHERE id = %s
                ''', (user_id,))
                user = cur.fetchone()
                if not user:
                    flash('User not found.', 'error')
                    return redirect(url_for('admin_user_archive'))

                user_email = user[0]

                # Delete the user permanently
                cur.execute('DELETE FROM users WHERE id = %s', (user_id,))
                conn.commit()

                # Create a notification for the admin
                notification_message = f'User ID {user_id} has been permanently deleted.'
                create_notification(session['user_id'], notification_message, 'user_delete')

        # Send an email notification to the user
        if user_email:
            subject = "Your Account Has Been Permanently Deleted"
            body = f"""
            Dear User,

            Your account with ID {user_id} has been permanently deleted from our system. If you have any questions or concerns, please contact our support team.

            Best regards,
            The Admin Team
            """
            send_email(user_email, subject, body)

        flash('User permanently deleted successfully, and an email notification was sent.', 'success')
    except Exception as e:
        flash(f"An error occurred: {str(e)}", 'error')
    return redirect(url_for('admin_user_archive'))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    print(f"Current session: {session}")

    if 'email' not in session:
        flash('You need to be logged in to add a product.', 'error')
        return redirect(url_for('login'))

    if session.get('role') != 'seller':
        flash('You need to have a seller account to add products.', 'error')
        return redirect(url_for('dashboard'))

    print(f"Attempting to fetch user with email: {session['email']}")

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT id FROM users WHERE email = %s', (session['email'],))
                user = cur.fetchone()
                print(f"Database query result: {user}")

        if not user:
            print(f"No user found for email: {session['email']}")
            flash('User  not found. Please try logging in again.', 'error')
            session.clear()
            return redirect(url_for('login'))

        seller_id = user[0]
        print(f"Seller ID: {seller_id}")

    except Exception as e:
        print(f"Error fetching user: {str(e)}")
        flash('An error occurred while fetching user data. Please try again.', 'error')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        try:
            # Handle image upload
            image_url = ''
            additional_images = []
            file_upload_failed = False  

            if 'image_upload' in request.files:
                file = request.files['image_upload']
                if file.filename != '' and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(app.config['PRODUCT_UPLOAD_FOLDER'], filename)
                    try:
                        file.save(file_path)
                        if os.path.exists(file_path):
                            file_size = os.path.getsize(file_path)
                            if file_size > 0:
                                image_url = f'uploads/products/{filename}'
                            else:
                                file_upload_failed = True
                                flash('Error: Uploaded file is empty')
                        else:
                            file_upload_failed = True
                            flash('Error: File not saved')
                    except Exception as e:
                        file_upload_failed = True
                        flash(f'Error saving file: {str(e)}')
                else:
                    file_upload_failed = True
                    flash('Invalid file type or no file selected')

            # If no file is uploaded, check for the URL
            if not image_url:
                image_url = request.form.get('image_url', '').strip()
            
            if not image_url:
                if file_upload_failed:
                    flash('File upload failed. Please either upload a valid image or provide an image URL.')
                else:
                    flash('Please either upload an image or provide an image URL.')
                return redirect(request.url)

            # Process additional images
            for i in range(3):
                url_key = f'additional_image_url_{i}'
                if url_key in request.form:
                    url = request.form[url_key].strip()
                    if url:
                        additional_images.append(url)

            # Handle additional image files
            if 'additional_image_files' in request.files:
                additional_files = request.files.getlist('additional_image_files')
                for file in additional_files[:3]:
                    if file and file.filename and allowed_file(file.filename):
                        try:
                            filename = secure_filename(file.filename)
                            file_path = os.path.join(app.config['PRODUCT_UPLOAD_FOLDER'], filename)
                            file.save(file_path)
                            additional_image_url = url_for('static', filename=f'uploads/{filename}')
                            additional_images.append(additional_image_url)
                        except Exception as e:
                            print(f"Error saving additional file {file.filename}: {str(e)}")

            # Convert additional images to JSON
            additional_images_json = json.dumps(additional_images[:3])

            # Get product details from form
            product_data = {
                'name': request.form['name'],
                'price': float(request.form['price']),
                'description': request.form['description'],
                'stock': int(request.form['stock']),
                'sku': str(uuid.uuid4()),
                'category': request.form['category'],
                'subcategory': request.form['subcategory'],
                'variant': request.form.get('variant', ''),
                'material': request.form.get('material', ''),
                'dimensions': request.form.get('dimensions', ''),
                'weight': float(request.form.get('weight', 0)),
                'shipping_weight': float(request.form.get('shipping_weight', 0)),
                'shipping_dimensions': request.form.get('shipping_dimensions', ''),
                'indoor_outdoor': request.form['indoor_outdoor'],
                'color': request.form.get('color', ''),
                'brand': request.form.get('brand', ''),
                'warranty': request.form.get('warranty', ''),
                'seller_id': seller_id,
                'image_url': image_url,
                'additional_images': additional_images_json,
                'tags': "{" + ",".join(request.form.get('tags', '').split(',')) + "}" if request.form.get('tags') else '{}',
                'is_on_sale': request.form.get('is_on_sale', 'false') == 'true',
                'approval_status': 'pending',
                'display_status': 'hidden',
                'admin_comments': request.form.get('admin_comments', ''),
                'approval_date': None  # Explicitly set to None
            }

            # Calculate discounted price if discount percentage provided
            discount_percentage = request.form.get('discount_percentage')
            if discount_percentage:
                discount_percentage = float(discount_percentage)
                product_data['discounted_price'] = product_data['price'] - (product_data['price'] * (discount_percentage / 100))
            else:
                product_data['discounted_price'] = product_data['price']

            # Insert into database
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute('''
                        INSERT INTO products (
                            name, price, discounted_price, description, stock, sku, 
                            category, subcategory, variant, image_url, 
                            additional_images, material, dimensions, weight, 
                            shipping_weight, shipping_dimensions, indoor_outdoor, 
                            color, brand, warranty, seller_id, tags, 
                            is_on_sale, approval_status, admin_comments, display_status,
                            approval_date
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                            %s, %s, %s, %s, %s, %s
                        )''',
                        (
                            product_data['name'], product_data['price'], product_data['discounted_price'],
                            product_data['description'], product_data['stock'], product_data['sku'],
                            product_data['category'], product_data['subcategory'], product_data['variant'],
                            product_data['image_url'], product_data['additional_images'], product_data['material'],
                            product_data['dimensions'], product_data['weight'], product_data['shipping_weight'],
                            product_data['shipping_dimensions'], product_data['indoor_outdoor'], product_data['color'],
                            product_data['brand'], product_data['warranty'], product_data['seller_id'], product_data['tags'],
                            product_data['is_on_sale'], product_data['approval_status'], product_data['admin_comments'],
                            product_data['display_status'], product_data['approval_date']
                        ))
                    conn.commit()

                    # Create notifications
                    admin_message = f'Seller ID {seller_id} is waiting for product approval for "{product_data["name"]}".'
                    create_notification(4, admin_message, 'product_approval')

                    seller_message = f'Your product "{product_data["name"]}" has been submitted for approval. Please wait for admin approval.'
                    create_notification(seller_id, seller_message, 'product_submission')

                    flash('Product added successfully and is pending approval!')
                    return redirect(url_for('manage_products'))
                
        except Exception as e:
            flash(f"An error occurred: {str(e)}")

    return render_template('add_product.html')
    
@app.route('/edit_product/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):

    # Fetch the product details from the database
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM products WHERE id = %s", (product_id,))
            product = cur.fetchone()

    if request.method == 'POST':
        # Extract updated product details from the form
        product_name = request.form['name']
        product_price = float(request.form['price'])
        product_description = request.form['description']
        discount_percentage = float(request.form.get('discount_percentage', 0))
        stock_quantity = int(request.form['stock'])
        sku = request.form['sku']
        category = request.form['category']
        subcategory = request.form['subcategory']
        variant = request.form.get('variant', '')
        image_url = request.form.get('image_url', '')
        additional_images = request.form.get('additional_images', '')
        material = request.form.get('material', '')
        dimensions = request.form.get('dimensions', '')
        weight = float(request.form.get('weight', 0))
        shipping_weight = float(request.form.get('shipping_weight', 0))
        shipping_dimensions = request.form.get('shipping_dimensions', '')
        indoor_outdoor = request.form['indoor_outdoor']
        color = request.form.get('color', '')
        brand = request.form.get('brand', '')
        warranty = request.form.get('warranty', '')
        seller_id = int(request.form['seller_id'])
        
        # Handle tags input and format as a PostgreSQL array
        tags_input = request.form.get('tags', '')
        tags_array = "{" + ",".join(tags_input.split(',')) + "}" if tags_input else '{}'
        
        is_on_sale = request.form.get('is_on_sale', 'false') == 'true'
        approval_status = request.form['approval_status']
        admin_comments = request.form.get('admin_comments', '')
        display_status = request.form['display_status']

        # Calculate discounted price
        discounted_price = product_price - (product_price * (discount_percentage / 100))

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute('''UPDATE products SET
                        name = %s, price = %s, discounted_price = %s,
                        description = %s, stock = %s, sku = %s,
                        category = %s, subcategory = %s, variant = %s,
                        image_url = %s, additional_images = %s,
                        material = %s, dimensions = %s, weight = %s,
                        shipping_weight = %s, shipping_dimensions = %s,
                        indoor_outdoor = %s, color = %s, brand = %s,
                        warranty = %s, seller_id = %s, tags = %s,
                        is_on_sale = %s, approval_status = %s,
                        admin_comments = %s, display_status = %s
                        WHERE id = %s''',
                        (product_name, product_price, discounted_price,
                         product_description, stock_quantity, sku,
                         category, subcategory, variant, image_url,
                         additional_images, material, dimensions, weight,
                         shipping_weight, shipping_dimensions, indoor_outdoor,
                         color, brand, warranty, seller_id, tags_array,
                         is_on_sale, approval_status, admin_comments,
                         display_status, product_id))
                    conn.commit()
                    flash('Product updated successfully!')
                    return redirect(url_for('manage_products'))  # Redirect to the manage products page
        except Exception as e:
            flash(f"An error occurred: {str(e)}")

    # Render the edit form with existing product data
    return render_template('edit_product.html', product=product)


@app.route('/delete_product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM products WHERE id = %s", (product_id,))
                conn.commit()
        flash('Product deleted successfully!')
    except Exception as e:
        flash(f"An error occurred while deleting the product: {str(e)}")

    return redirect(url_for('manage_products'))

@app.route('/create-notification', methods=['POST'])
def create_notification_api():
    data = request.get_json()
    user_id = data.get('user_id')
    message = data.get('message')
    notification_type = data.get('type', 'general')  # Default to 'general' if not provided

    try:
        # Call the database function to create a notification
        create_notification(user_id, message, notification_type)
        return jsonify({'success': True, 'message': 'Notification created successfully'}), 201
    except Exception as e:
        logging.error(f"Error creating notification: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

def create_notification(user_id, message, notification_type):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('''
                    INSERT INTO notifications (user_id, message, type) 
                    VALUES (%s, %s, %s)
                ''', (user_id, message, notification_type))
                conn.commit()
    except Exception as e:
        logging.error(f"Error creating notification: {str(e)}")

@app.route('/notifications', methods=['GET'])
def get_notifications():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized access'}), 403

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('''
                    SELECT id, message, is_read, created_at 
                    FROM notifications 
                    WHERE user_id = %s 
                    ORDER BY created_at DESC
                ''', (session['user_id'],))
                notifications = cur.fetchall()
                return jsonify({'success': True, 'notifications': notifications}), 200
    except Exception as e:
        logging.error(f"Error fetching notifications: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500        
        
@app.route('/notifications/delete', methods=['POST'])
def delete_notifications():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized access'}), 403

    # Get the list of notification IDs from the request
    data = request.get_json()
    notification_ids = data.get('ids', [])

    if not notification_ids:
        return jsonify({'success': False, 'message': 'No notifications selected for deletion'}), 400

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Delete notifications for the logged-in user
                cur.execute('''
                    DELETE FROM notifications 
                    WHERE id IN %s AND user_id = %s
                ''', (tuple(notification_ids), session['user_id']))  # Use tuple for IN clause
                conn.commit()

        return jsonify({'success': True, 'message': 'Selected notifications deleted successfully'})

    except Exception as e:
        logging.error(f"Error deleting notifications: {str(e)}")
        return jsonify({'success': False, 'message': 'An error occurred while deleting notifications'}), 500
        
def get_notifications_for_user(user_id, role):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            if role == 'buyer':
                cur.execute('''
                    SELECT id, message, created_at FROM notifications
                    WHERE user_id = %s AND type IN ('order_update', 'promotion')
                    ORDER BY created_at DESC
                ''', (user_id,))
            elif role == 'seller':
                cur.execute('''
                    SELECT id, message, created_at FROM notifications
                    WHERE user_id = %s AND type IN ('new_order', 'order_update',)
                    ORDER BY created_at DESC
                ''', (user_id,))
            return cur.fetchall()
        
@app.route('/send_message', methods=['POST'])
def send_message():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized access'}), 403

    sender_id = session['user_id']
    receiver_id = request.form.get('receiver_id')
    message = request.form.get('message')

    if not receiver_id or not message:
        return jsonify({'success': False, 'message': 'Receiver ID and message are required.'}), 400

    # Check if the receiver exists
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT id FROM users WHERE id = %s', (receiver_id,))
                if not cur.fetchone():
                    return jsonify({'success': False, 'message': 'Receiver does not exist.'}), 400

                cur.execute('''
                    INSERT INTO chat_messages (sender_id, receiver_id, message)
                    VALUES (%s, %s, %s)
                ''', (sender_id, receiver_id, message))
                conn.commit()

        return jsonify({'success': True, 'message': 'Message sent successfully.'})

    except Exception as e:
        print(f"Error sending message: {str(e)}")
        return jsonify({'success': False, 'message': 'An error occurred while sending the message.'}), 500
        
@app.route('/get_messages/<int:other_user_id>', methods=['GET'])
def get_messages(other_user_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized access'}), 403

    user_id = session['user_id']
    messages = []

    # Check if the other user exists
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT id FROM users WHERE id = %s', (other_user_id,))
                if not cur.fetchone():
                    return jsonify({'success': False, 'message': 'User  does not exist.'}), 400

                cur.execute('''
                    SELECT sender_id, receiver_id, message, created_at, is_read
                    FROM chat_messages
                    WHERE (sender_id = %s AND receiver_id = %s) OR (sender_id = %s AND receiver_id = %s)
                    ORDER BY created_at ASC
                ''', (user_id, other_user_id, other_user_id, user_id))

                messages = [
                    {
                        'sender_id': msg[0],
                        'receiver_id': msg[1],
                        'message': msg[2],
                        'created_at': msg[3].strftime('%Y-%m-%d %H:%M:%S'),
                        'is_read': msg[4],
                        'is_sender': msg[0] == user_id  # Add a flag for sender identification
                    }
                    for msg in cur.fetchall()
                ]
            return jsonify({'success': True, 'messages': messages})

    except Exception as e:
        print(f"Error fetching messages: {str(e)}")
        return jsonify({'success': False, 'message': 'An error occurred while fetching messages.'}), 500
        
@app.route('/get_users', methods=['GET'])
def get_users():
    try:
        # Retrieve the logged-in user's ID from the session
        current_user_id = session.get('user_id')

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Modify the query to exclude the logged-in user's ID
                cur.execute('SELECT id, name FROM users WHERE is_archived = FALSE AND id != %s', (current_user_id,))
                users = [{'id': user[0], 'name': user[1]} for user in cur.fetchall()]  # Convert to dicts
                print(f"Fetched users: {users}")  # Debug output
                return jsonify(users)
    except Exception as e:
        print(f"Error fetching users: {str(e)}")  # Debug output
        return jsonify({'error': str(e)}), 500
    
@app.route('/typing', methods=['POST'])
def typing():
    data = request.get_json()
    receiver_id = data.get('receiver_id')

    # Logic to broadcast typing status to the receiver
    # This could involve storing the typing status in a database or using WebSockets
    return jsonify({'success': True})
                                    
@app.route('/item/<int:product_id>')
def item(product_id):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Fetch the product details by ID
                cur.execute("""
                    SELECT id, name, description, price, image_url, category, subcategory, stock, sku, tags, dimensions, material, weight, rating, reviews, 
                        is_on_sale, sale_price, variant, color, power_source, warranty, availability_status 
                    FROM products 
                    WHERE id = %s AND approval_status = 'approved' AND display_status = 'visible' AND is_archived = FALSE
                """, (product_id,))
                product_data = cur.fetchone()
                
                if not product_data:
                    flash("Product not found or unavailable.", "error")
                    return redirect(url_for('shop'))

                # Map product data to a dictionary for ease of use in templates
                product = {
                    'id': product_data[0],
                    'name': product_data[1],
                    'description': product_data[2],
                    'price': product_data[3],
                    'image_url': product_data[4],
                    'category': product_data[5],
                    'subcategory': product_data[6],
                    'stock': product_data[7],
                    'sku': product_data[8],
                    'tags': product_data[9],
                    'dimensions': product_data[10],
                    'material': product_data[11],
                    'weight': product_data[12],
                    'rating': product_data[13],
                    'reviews': product_data[14] if product_data[14] is not None else [],  # Ensure it's a list
                    'is_on_sale': product_data[15],
                    'sale_price': product_data[16],
                    'variant': product_data[17],
                    'color': product_data[18],
                    'power_source': product_data[19],
                    'warranty': product_data[20],
                    'availability_status': product_data[21],
                }

    except Exception as e:
            flash(f"Error fetching product details: {str(e)}", "error")
            return redirect(url_for('shop'))

    return render_template('item.html', product=product)

@app.route('/search-users', methods=['GET'])
def search_users():
    # Setup logging
    logger = logging.getLogger(__name__)
    
    try:
        # Get search query from request arguments
        query = request.args.get('query', '').strip().lower()
        users = []

        # Example logic to search users from a data source
        # Ensure `db` is the instance of SQLAlchemy initialized properly in your app
        from models import db, User  # Import db and User model correctly
        if query:
            users = db.session.query(User).filter(User.name.ilike(f"%{query}%")).all()
        
        # Return users in JSON format
        return jsonify([user.to_dict() for user in users])
    except Exception as e:
        logger.error(f"Error searching users: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/confirm-receipt/<int:order_id>', methods=['POST'])
def confirm_receipt(order_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized access'}), 403

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Fetch the user's role
                cur.execute('SELECT role FROM users WHERE id = %s', (session['user_id'],))
                user = cur.fetchone()
                if user is None:
                    return jsonify({'success': False, 'message': 'User not found'}), 404
                user_role = user[0]

                # Check the order and its status
                cur.execute('SELECT status, user_id FROM orders WHERE id = %s', (order_id,))
                order = cur.fetchone()
                if order is None:
                    return jsonify({'success': False, 'message': 'Order not found'}), 404

                current_status, order_user_id = order

                # Only buyers can confirm receipt
                if user_role != 'user' or order_user_id != session['user_id']:
                    return jsonify({'success': False, 'message': 'Only the buyer can confirm receipt'}), 403
                if current_status != 'DELIVERED':
                    return jsonify({'success': False, 'message': 'Order must be DELIVERED to confirm receipt'}), 400

                # Update confirmed_receipt
                cur.execute('''
                    UPDATE orders 
                    SET confirmed_receipt = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                ''', (1, order_id))

                conn.commit()

        return jsonify({'success': True, 'message': 'Receipt confirmed successfully'})
    except Exception as e:
        logging.error(f"Error confirming receipt: {str(e)}")
        return jsonify({'success': False, 'message': 'An error occurred while confirming receipt.'}), 500
        
@app.route('/api/rateProduct', methods=['POST'])
def rate_product():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized access'}), 403
    data = request.get_json()
    product_id = data.get('productId')
    order_id = data.get('orderId')
    rating = data.get('rating')
    review = data.get('review')
    if not product_id or not order_id:
        return jsonify({'success': False, 'message': 'Product ID and Order ID are required.'}), 400
    if not isinstance(rating, int) or rating < 1 or rating > 5:
        return jsonify({'success': False, 'message': 'Rating must be an integer between 1 and 5.'}), 400
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Verify the order belongs to the user
                cur.execute('SELECT user_id FROM orders WHERE id = %s', (order_id,))
                order = cur.fetchone()
                if order is None:
                    return jsonify({'success': False, 'message': 'Order not found'}), 404
                if order[0] != session['user_id']:
                    return jsonify({'success': False, 'message': 'Unauthorized to rate this order'}), 403
                # Check if already rated
                cur.execute('''
                    SELECT has_rated FROM order_items 
                    WHERE order_id = %s AND product_id = %s
                ''', (order_id, product_id))
                result = cur.fetchone()
                if result and result[0] == 1:
                    return jsonify({'success': False, 'message': 'Product already rated for this order.'}), 400
                # Use transaction for atomicity
                cur.execute('BEGIN')
                cur.execute('''
                    UPDATE products
                    SET rating = (rating * review_count + %s) / (review_count + 1),
                        review_count = review_count + 1,
                        reviews = COALESCE(reviews, '') || %s || '; '
                    WHERE id = %s
                ''', (rating, review, product_id))
                cur.execute('''
                    UPDATE order_items
                    SET has_rated = 1
                    WHERE order_id = %s AND product_id = %s
                ''', (order_id, product_id))
                cur.execute('''
                    SELECT COUNT(*) as total, SUM(has_rated) as rated
                    FROM order_items
                    WHERE order_id = %s
                ''', (order_id,))
                counts = cur.fetchone()
                if counts[0] == counts[1]:
                    cur.execute('UPDATE orders SET has_rated = 1 WHERE id = %s', (order_id,))
                conn.commit()
                return jsonify({'success': True, 'message': 'Rating submitted successfully!'})
    except Exception as e:
        conn.rollback()  # Rollback on error
        return jsonify({'success': False, 'message': str(e)}), 500
            
@app.route('/api/order-items/<int:order_id>', methods=['GET'])
def get_order_items(order_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'User not authenticated'}), 401

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Verify the order belongs to the user
                cur.execute('SELECT user_id FROM orders WHERE id = %s', (order_id,))
                order = cur.fetchone()
                if order is None:
                    return jsonify({'success': False, 'message': 'Order not found'}), 404
                if order[0] != session['user_id']:
                    return jsonify({'success': False, 'message': 'Unauthorized access to order'}), 403
                # Fetch order items
                cur.execute('''
                    SELECT oi.product_id, oi.quantity, oi.has_rated, p.name
                    FROM order_items oi
                    JOIN products p ON oi.product_id = p.id
                    WHERE oi.order_id = %s
                ''', (order_id,))
                items = cur.fetchall()
                items_list = [
                    {
                        'product_id': item[0],
                        'quantity': item[1],
                        'has_rated': item[2] == 1,
                        'name': item[3]
                    } for item in items
                ]
        return jsonify({'success': True, 'items': items_list})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
                
def generate_otp():
    return random.randint(100000, 999999)

def send_otp(email, otp):
    subject = "Your OTP Code"
    body = f"Your OTP code is: {otp}"
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = "ravsangaspar@gmail.com"  # Your Gmail address
    msg['To'] = email

    try:
        print(f"Sending OTP to {email}...")
        # Connect to Gmail's SMTP server
        with smtplib.SMTP('smtp.gmail.com', 587) as server:  
            server.starttls()  # Start TLS encryption
            # Log in with Gmail address and App Password
            server.login("ravsangaspar@gmail.com", "zlzongxfunmalzmt")  
            server.send_message(msg)  # Send the email
            print("OTP sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        
@app.route('/dashboard', methods=['POST'])
def filter_sales():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    data = request.get_json()
    start_date = data.get('start_date')
    end_date = data.get('end_date')

    if not start_date or not end_date:
        flash("Invalid date range.")
        return redirect(url_for('dashboard'))

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('''
                    SELECT 
                        o.id AS order_id, 
                        o.created_at AS order_created_at,
                        u.name AS buyer_name, 
                        SUM(oi.price * oi.quantity) AS total_amount
                    FROM orders o 
                    JOIN order_items oi ON o.id = oi.order_id 
                    JOIN products p ON oi.product_id = p.id  
                    JOIN users u ON o.user_id = u.id 
                    WHERE p.seller_id = %s AND o.status = 'DELIVERED' 
                    AND o.created_at BETWEEN %s AND %s
                    GROUP BY o.id, o.created_at, u.name 
                    ORDER BY o.created_at DESC;
                ''', (session['user_id'], start_date, end_date))
                
                sales_data = cur.fetchall()

        return render_template('dashboard.html', sales_data=sales_data)

    except Exception as e:
        print(f"Filter error: {str(e)}")
        flash('Error filtering data.')
        return redirect(url_for('dashboard'))
        
@app.route('/dashboard/export_report')
def export_report():
    if 'user_id' not in session:
        flash("You must be logged in to view this report.")
        return redirect(url_for('login'))
    
    # Parse the dates
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if not start_date or not end_date:
        flash("Invalid date range.")
        return redirect(url_for('dashboard'))

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('''
                    SELECT 
                        o.id AS order_id, 
                        o.created_at AS order_created_at, 
                        u.name AS buyer_name, 
                        SUM(oi.price * oi.quantity) AS total_amount
                    FROM orders o 
                    JOIN order_items oi ON o.id = oi.order_id 
                    JOIN products p ON oi.product_id = p.id  
                    JOIN users u ON o.user_id = u.id 
                    WHERE p.seller_id = %s AND o.status = 'DELIVERED' 
                    AND o.created_at BETWEEN %s AND %s
                    GROUP BY o.id, o.created_at, u.name;
                ''', (session['user_id'], start_date, end_date))

                data = cur.fetchall()

        if not data:
            flash("No data found for the selected date range.")
            return redirect(url_for('dashboard'))

        # Create an Excel workbook
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Export Report"

        # Set the header row
        headers = ['Order ID', 'Date', 'Buyer Name', 'Total Amount']
        sheet.append(headers)

        # Populate the rows
        for row in data:
            sheet.append([row[0], row[1], row[2], row[3]])

        # Save workbook into a BytesIO stream
        output = io.BytesIO()
        workbook.save(output)
        output.seek(0)  # Reset stream position for sending

        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            attachment_filename='export_report.xlsx'
        )
    except Exception as e:
        print(f"Error during report generation: {str(e)}")
        flash(f"Error generating report. Details: {str(e)}")
        return redirect(url_for('dashboard'))
        
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    notifications = []

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Fetch sales data for the logged-in seller
                cur.execute(''' 
                    SELECT 
                        o.id AS order_id, 
                        o.created_at AS order_created_at,  -- Alias for sales created_at 
                        u.name AS buyer_name, 
                        SUM(oi.price * oi.quantity) AS total_amount, 
                        SUM(oi.price * oi.quantity) * 0.05 AS admin_commission 
                    FROM orders o 
                    JOIN order_items oi ON o.id = oi.order_id 
                    JOIN products p ON oi.product_id = p.id  
                    JOIN users u ON o.user_id = u.id 
                    WHERE p.seller_id = %s AND o.status = 'DELIVERED'  
                    GROUP BY o.id, o.created_at, u.name 
                    ORDER BY o.created_at DESC;
                ''', (session['user_id'],))  
                
                sales_data = cur.fetchall()
                print("Sales Data:", sales_data)  # Debugging line

                # Check the types of the fetched sales data
                for sale in sales_data:
                    print(f"Order ID: {sale[0]}, Created At: {type(sale[1])}, Buyer Name: {sale[2]}, Total Amount: {sale[3]}, Admin Commission: {sale[4]}")

                # Fetch notifications for the logged-in seller
                cur.execute('''
                    SELECT id, message, is_read, created_at 
                    FROM notifications 
                    WHERE user_id = %s 
                    ORDER BY created_at DESC
                ''', (session['user_id'],))
                notifications = cur.fetchall()  # Fetch notifications

        if not sales_data:
            sales_data = []  # No sales data found

        return render_template('dashboard.html', sales_data=sales_data, notifications=notifications)

    except Exception as e:
        print(f"Error fetching sales report: {str(e)}")
        flash('An error occurred while fetching the sales report. Please try again later.')
        return redirect(url_for('dashboard'))                            

@app.route('/sales-report')
def sales_report():
    if 'user_id' not in session:
        flash('Please log in to view the sales report.')
        return redirect(url_for('login'))

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Fetch sales report data from the database table
                cur.execute('''
                    SELECT order_id, total_amount, admin_commission, created_at 
                    FROM public.sales_report
                    WHERE order_id IN (
                        SELECT id 
                        FROM orders
                        WHERE buyer_id = %s
                    )
                    ORDER BY created_at DESC;
                ''', (session['user_id'],))
                
                sales_data = cur.fetchall()
                print("Fetched sales data from database table:", sales_data)

        if not sales_data:
            flash('No sales data found for your account.')
            return render_template('sales_report.html', sales_data=[])

        return render_template('sales_report.html', sales_data=sales_data)

    except Exception as e:
        print(f"Error fetching data from sales_report table: {str(e)}")
        flash('An error occurred while fetching the sales report.')
        return redirect(url_for('dashboard'))

                
@app.route('/update-sales-report/<int:order_id>', methods=['POST'])
def update_sales_report(order_id):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Fetch order details
                cur.execute('''
                    SELECT 
                        o.id,
                        SUM(oi.price * oi.quantity) AS total_amount,
                        SUM(oi.price * oi.quantity) * 0.05 AS admin_commission
                    FROM orders o
                    JOIN order_items oi ON o.id = oi.order_id
                    WHERE o.id = %s
                    GROUP BY o.id
                ''', (order_id,))
                order_data = cur.fetchone()

                if order_data:
                    order_id, total_amount, admin_commission = order_data

                    # Insert or update sales report logic here
                    # Assuming you have a sales_report table
                    cur.execute('''
                        INSERT INTO sales_report (order_id, total_amount, admin_commission)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (order_id) DO UPDATE SET 
                        total_amount = EXCLUDED.total_amount,
                        admin_commission = EXCLUDED.admin_commission
                    ''', (order_id, total_amount, admin_commission))

                    conn.commit()

                    return jsonify({'success': True})
                else:
                    return jsonify({'success': False, 'message': 'Order not found'}), 404

    except Exception as e:
        print(f"Error updating sales report: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/orders')
def api_orders():
    if 'user_id' not in session or session.get('role') != 'seller':
        return jsonify({'error': 'Unauthorized access'}), 403

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('''
                    SELECT 
                        o.id, 
                        u.name as buyer_name, 
                        o.status
                    FROM orders o 
                    JOIN users u ON o.user_id = u.id 
                    WHERE u.id = %s
                    ORDER BY o.created_at DESC
                ''', (session['user_id'],))
                
                orders = []
                for row in cur.fetchall():
                    orders.append({
                        'id': row[0],
                        'buyer': row[1],
                        'status': row[2]
                    })
        
        return jsonify(orders)  # Return as JSON
    except Exception as e:
        print(f"Error fetching orders for API: {e}")
        return jsonify({'error': 'Server error'}), 500
    
@app.route('/api/orders', methods=['POST'])
def place_order():
    data = request.get_json()

    # Validate incoming data
    if not data or 'user_id' not in data or 'items' not in data or 'total' not in data:
        return jsonify({'success': False, 'message': 'Missing required fields: user_id, items, total'}), 400

    user_id = data['user_id']
    items_data = data['items']
    total = data['total']
    shipping_address = data.get('shipping_address', '')  # Optional field
    status = data.get('status', 'PENDING')  # Default to PENDING if not provided

    # Validate items data
    if not isinstance(items_data, list) or not items_data:
        return jsonify({'success': False, 'message': 'Items must be a non-empty list'}), 400

    try:
        # Create the Order instance
        new_order = Order(
            user_id=user_id,
            subtotal=total,  # Use total from payload as subtotal (includes shipping)
            status=status,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.session.add(new_order)

        # Process each item and decrement stock
        for item in items_data:
            if 'id' not in item or 'quantity' not in item or 'price' not in item:
                db.session.rollback()
                return jsonify({
                    'success': False,
                    'message': 'Each item must have id, quantity, and price'
                }), 400

            product_id = int(item['id'])
            quantity = item['quantity']

            # Check and decrement stock using SQLAlchemy
            product = Product.query.get(product_id)
            if not product or product.stock < quantity:
                db.session.rollback()
                return jsonify({'success': False, 'message': f'Insufficient stock for Product ID {product_id}'}), 400
            product.stock -= quantity  # Decrement stock
            db.session.flush()  # Ensure stock update is staged

            # Create OrderItem
            order_item = OrderItem(
                order=new_order,
                product_id=product_id,
                quantity=quantity,
                price=item['price']
            )
            db.session.add(order_item)

        # Commit the transaction
        db.session.commit()
        return jsonify({
            'success': True,
            'order_id': new_order.id,
            'message': 'Order placed successfully'
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
            
def send_email(to_email, subject, body):
    """Send an email using smtplib."""
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = "ravsangaspar@gmail.com"  # Your Gmail address
    msg['To'] = to_email

    try:
        print(f"Sending email to {to_email}...")
        # Connect to Gmail's SMTP server
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()  # Start TLS encryption
            # Log in with Gmail address and App Password
            server.login("ravsangaspar@gmail.com", "zlzongxfunmalzmt")
            server.send_message(msg)  # Send the email
            print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {str(e)}")

# API endpoint to fetch all products with all columns
@api.route('/products', methods=['GET'])
def get_products():
    products = Product.query.all()
    return jsonify([p.to_dict() for p in products])

# API endpoint to get a product by ID with all columns
@api.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = Product.query.get_or_404(product_id)
    return jsonify(product.to_dict())

# API endpoint to create a new product (allowing all fields to be set)
@api.route('/products', methods=['POST'])
def create_product():
    data = request.json
    new_product = Product(
        name=data['name'],
        image_url=data['image_url'],
        price=data.get('price'),
        stock=data.get('stock', 0),
        sku=data.get('sku'),
        category=data.get('category'),
        subcategory=data.get('subcategory'),
        variant=data.get('variant'),
        additional_images=data.get('additional_images'),
        material=data.get('material'),
        dimensions=data.get('dimensions'),
        weight=data.get('weight'),
        shipping_weight=data.get('shipping_weight'),
        shipping_dimensions=data.get('shipping_dimensions'),
        indoor_outdoor=data.get('indoor_outdoor'),
        color=data.get('color'),
        brand=data.get('brand'),
        power_source=data.get('power_source'),
        warranty=data.get('warranty'),
        seller_id=data['seller_id'],
        approval_status=data.get('approval_status', 'pending'),
        admin_comments=data.get('admin_comments'),
        display_status=data.get('display_status', 'hidden'),
        rating=data.get('rating', 0.00),
        reviews=data.get('reviews'),
        tags=data.get('tags'),
        sale_price=data.get('sale_price'),
        is_on_sale=data.get('is_on_sale', False),
        availability_status=data.get('availability_status', 'in_stock'),
        discounted_price=data.get('discounted_price'),
        approval_date=data.get('approval_date'),
        is_archived=data.get('is_archived', False),
        review_count=data.get('review_count', 0),
        created_at=data.get('created_at', datetime.utcnow()),
        updated_at=data.get('updated_at', datetime.utcnow())
    )
    db.session.add(new_product)
    db.session.commit()
    return jsonify({'message': 'Product created successfully', 'product': new_product.to_dict()}), 201

# API endpoint to update a product (allowing all fields to be updated)
@api.route('/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    product = Product.query.get_or_404(product_id)
    data = request.json
    product.name = data.get('name', product.name)
    product.image_url = data.get('image_url', product.image_url)
    product.price = data.get('price', product.price)
    product.stock = data.get('stock', product.stock)
    product.sku = data.get('sku', product.sku)
    product.category = data.get('category', product.category)
    product.subcategory = data.get('subcategory', product.subcategory)
    product.variant = data.get('variant', product.variant)
    product.additional_images = data.get('additional_images', product.additional_images)
    product.material = data.get('material', product.material)
    product.dimensions = data.get('dimensions', product.dimensions)
    product.weight = data.get('weight', product.weight)
    product.shipping_weight = data.get('shipping_weight', product.shipping_weight)
    product.shipping_dimensions = data.get('shipping_dimensions', product.shipping_dimensions)
    product.indoor_outdoor = data.get('indoor_outdoor', product.indoor_outdoor)
    product.color = data.get('color', product.color)
    product.brand = data.get('brand', product.brand)
    product.power_source = data.get('power_source', product.power_source)
    product.warranty = data.get('warranty', product.warranty)
    product.seller_id = data.get('seller_id', product.seller_id)
    product.approval_status = data.get('approval_status', product.approval_status)
    product.admin_comments = data.get('admin_comments', product.admin_comments)
    product.display_status = data.get('display_status', product.display_status)
    product.rating = data.get('rating', product.rating)
    product.reviews = data.get('reviews', product.reviews)
    product.tags = data.get('tags', product.tags)
    product.sale_price = data.get('sale_price', product.sale_price)
    product.is_on_sale = data.get('is_on_sale', product.is_on_sale)
    product.availability_status = data.get('availability_status', product.availability_status)
    product.discounted_price = data.get('discounted_price', product.discounted_price)
    product.approval_date = data.get('approval_date', product.approval_date)
    product.is_archived = data.get('is_archived', product.is_archived)
    product.review_count = data.get('review_count', product.review_count)
    db.session.commit()
    return jsonify({'message': 'Product updated successfully', 'product': product.to_dict()})

# API endpoint to delete a product
@api.route('/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    return jsonify({'message': 'Product deleted successfully'})

# API endpoint to fetch all users with all columns and relationships
@api.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([u.to_dict() for u in users])  # Includes products, orders_as_buyer, notifications

# API endpoint to get a user by ID with all columns and relationships
@api.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict())  # Includes products, orders_as_buyer, notifications

# API endpoint to create a new user (allowing all fields to be set)
@api.route('/users', methods=['POST'])
def create_user():
    data = request.json
    new_user = User(
        name=data.get('name'),
        email=data.get('email'),
        password=data.get('password', ''),
        gender=data.get('gender'),
        country=data.get('country'),
        street_address=data.get('street_address'),
        city=data.get('city'),
        province=data.get('province'),
        zip_code=data.get('zip_code'),
        phone=data.get('phone'),
        role=data.get('role', 'user'),
        is_archived=data.get('is_archived', False),
        approval_status=data.get('approval_status', 'pending'),
        approved=data.get('approved', False),
        otp_verified=data.get('otp_verified', False),
        valid_id=data.get('valid_id'),
        business_permit=data.get('business_permit')
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'User created successfully', 'user': new_user.to_dict()}), 201  # Includes relationships (empty initially)

@app.route('/api/user', methods=['GET'])
def get_current_user():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'message': 'Unauthorized, no session found'}), 401
    
    user = User.query.get_or_404(user_id)
    return jsonify({
        'id': user.id,
        'role': user.role,
        'name': user.name,
        'email': user.email,
        'message': 'Success'
    }), 200

@app.route('/api/users/<int:user_id>', methods=['GET', 'PATCH'])
def user_endpoint(user_id):
    user = User.query.get_or_404(user_id)
    if request.method == 'GET':
        if not session.get('user_id') or session['user_id'] != user_id:
            return jsonify({'message': 'Unauthorized'}), 401
        return jsonify({
            'id': user.id,
            'role': user.role,
            'name': user.name,
            'email': user.email,
            'message': 'Success'
        }), 200
    elif request.method == 'PATCH':
        data = request.get_json()
        if 'name' in data:
            user.name = data['name']
        if 'email' in data:
            user.email = data['email']
        if 'password' in data:
            user.password = data['password']
        if 'gender' in data:
            user.gender = data['gender']
        if 'country' in data:
            user.country = data['country']
        if 'street_address' in data:
            user.street_address = data['street_address']
        if 'city' in data:
            user.city = data['city']
        if 'province' in data:
            user.province = data['province']
        if 'zip_code' in data:
            user.zip_code = data['zip_code']
        if 'phone' in data:
            user.phone = data['phone']
        if 'role' in data:
            user.role = data['role']
        if 'is_archived' in data:
            user.is_archived = data['is_archived']
        if 'approval_status' in data:
            user.approval_status = data['approval_status']
        if 'approved' in data:
            user.approved = data['approved']
        if 'otp_verified' in data:
            user.otp_verified = data['otp_verified']
        if 'valid_id' in data:
            user.valid_id = data['valid_id']
        if 'business_permit' in data:
            user.business_permit = data['business_permit']
        db.session.commit()
        return jsonify({'message': 'User updated successfully', 'user': user.to_dict()}), 200
        
# API endpoint to update a user (allowing all fields to be updated)
@api.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.json
    user.name = data.get('name', user.name)
    user.email = data.get('email', user.email)
    user.password = data.get('password', user.password)
    user.gender = data.get('gender', user.gender)
    user.country = data.get('country', user.country)
    user.street_address = data.get('street_address', user.street_address)
    user.city = data.get('city', user.city)
    user.province = data.get('province', user.province)
    user.zip_code = data.get('zip_code', user.zip_code)
    user.phone = data.get('phone', user.phone)
    user.role = data.get('role', user.role)
    user.is_archived = data.get('is_archived', user.is_archived)
    user.approval_status = data.get('approval_status', user.approval_status)
    user.approved = data.get('approved', user.approved)
    user.otp_verified = data.get('otp_verified', user.otp_verified)
    user.valid_id = data.get('valid_id', user.valid_id)
    user.business_permit = data.get('business_permit', user.business_permit)
    db.session.commit()
    return jsonify({'message': 'User updated successfully', 'user': user.to_dict()})  # Includes relationships

# API endpoint to delete a user
@api.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'User deleted successfully'})

# API endpoint to fetch sync data (including all models, with authentication and pagination)
# API endpoint to fetch sync data (including all models, without pagination)
@api.route('/api/data', methods=['GET'])
def get_sync_data():
    try:
        # Fetch all records from each model without pagination
        users = User.query.all()
        products = Product.query.all()
        orders = Order.query.all()
        order_items = OrderItem.query.all()
        notifications = Notification.query.all()
        chat_messages = ChatMessage.query.all()

        # Combine all data into a structured response
        response_data = {
            'users': [u.to_dict() for u in users],
            'products': [p.to_dict() for p in products],
            'orders': [o.to_dict() for o in orders],
            'order_items': [oi.to_dict() for oi in order_items],
            'notifications': [n.to_dict() for n in notifications],
            'chat_messages': [cm.to_dict() for cm in chat_messages]
        }

        # Return the combined data
        return jsonify({
            'data': response_data
        }), 200

    except Exception as e:
        logging.error(f"Error fetching sync data: {str(e)}")
        return jsonify({'error': f"Error fetching sync data: {str(e)}"}), 500

@api.route('/api/data', methods=['POST'])
def send_synced_data():
    try:
        data = request.json
        if not isinstance(data, list):
            return jsonify({'error': 'Request body must be a list'}), 400

        for item in data:
            item_type = item.get('type')
            item_id = item.get('id')

            if item_type == 'user':
                if not all(k in item for k in ['id', 'email']):
                    return jsonify({'error': f'Missing required user fields in item: {item}'}), 400
                existing_user = User.query.get(item_id) if item_id else None
                if existing_user:
                    existing_user.name = item.get('name', existing_user.name)
                    existing_user.email = item.get('email', existing_user.email)
                    if 'password' in item:
                        existing_user.password = item['password'] if item['password'] else existing_user.password
                    existing_user.gender = item.get('gender', existing_user.gender)
                    existing_user.country = item.get('country', existing_user.country)
                    existing_user.street_address = item.get('street_address', existing_user.street_address)
                    existing_user.city = item.get('city', existing_user.city)
                    existing_user.province = item.get('province', existing_user.province)
                    existing_user.zip_code = item.get('zip_code', existing_user.zip_code)
                    existing_user.phone = item.get('phone', existing_user.phone)
                    existing_user.role = item.get('role', existing_user.role)
                    existing_user.is_archived = item.get('is_archived', existing_user.is_archived)
                    existing_user.approval_status = item.get('approval_status', existing_user.approval_status)
                    existing_user.approved = item.get('approved', existing_user.approved)
                    existing_user.otp_verified = item.get('otp_verified', existing_user.otp_verified)
                    existing_user.valid_id = item.get('valid_id', existing_user.valid_id)
                    existing_user.business_permit = item.get('business_permit', existing_user.business_permit)
                else:
                    new_user = User(
                        id=item_id,
                        name=item.get('name'),
                        email=item.get('email'),
                        password=item.get('password', ''),
                        gender=item.get('gender'),
                        country=item.get('country'),
                        street_address=item.get('street_address'),
                        city=item.get('city'),
                        province=item.get('province'),
                        zip_code=item.get('zip_code'),
                        phone=item.get('phone'),
                        role=item.get('role', 'user'),
                        is_archived=item.get('is_archived', False),
                        approval_status=item.get('approval_status', 'pending'),
                        approved=item.get('approved', False),
                        otp_verified=item.get('otp_verified', False),
                        valid_id=item.get('valid_id'),
                        business_permit=item.get('business_permit')
                    )
                    db.session.add(new_user)

            elif item_type == 'product':
                if not all(k in item for k in ['id', 'name', 'image_url', 'seller_id']):
                    return jsonify({'error': f'Missing required product fields in item: {item}'}), 400
                existing_product = Product.query.get(item_id) if item_id else None
                if existing_product:
                    existing_product.name = item.get('name', existing_product.name)
                    existing_product.image_url = item.get('image_url', existing_product.image_url)
                    existing_product.price = item.get('price', existing_product.price)
                    existing_product.stock = item.get('stock', existing_product.stock)
                    existing_product.sku = item.get('sku', existing_product.sku)
                    existing_product.category = item.get('category', existing_product.category)
                    existing_product.subcategory = item.get('subcategory', existing_product.subcategory)
                    existing_product.variant = item.get('variant', existing_product.variant)
                    existing_product.additional_images = item.get('additional_images', existing_product.additional_images)
                    existing_product.material = item.get('material', existing_product.material)
                    existing_product.dimensions = item.get('dimensions', existing_product.dimensions)
                    existing_product.weight = item.get('weight', existing_product.weight)
                    existing_product.shipping_weight = item.get('shipping_weight', existing_product.shipping_weight)
                    existing_product.shipping_dimensions = item.get('shipping_dimensions', existing_product.shipping_dimensions)
                    existing_product.indoor_outdoor = item.get('indoor_outdoor', existing_product.indoor_outdoor)
                    existing_product.color = item.get('color', existing_product.color)
                    existing_product.brand = item.get('brand', existing_product.brand)
                    existing_product.power_source = item.get('power_source', existing_product.power_source)
                    existing_product.warranty = item.get('warranty', existing_product.warranty)
                    existing_product.seller_id = item.get('seller_id', existing_product.seller_id)
                    existing_product.approval_status = item.get('approval_status', existing_product.approval_status)
                    existing_product.admin_comments = item.get('admin_comments', existing_product.admin_comments)
                    existing_product.display_status = item.get('display_status', existing_product.display_status)
                    existing_product.rating = item.get('rating', existing_product.rating)
                    existing_product.reviews = item.get('reviews', existing_product.reviews)
                    existing_product.tags = item.get('tags', existing_product.tags)
                    existing_product.sale_price = item.get('sale_price', existing_product.sale_price)
                    existing_product.is_on_sale = item.get('is_on_sale', existing_product.is_on_sale)
                    existing_product.availability_status = item.get('availability_status', existing_product.availability_status)
                    existing_product.discounted_price = item.get('discounted_price', existing_product.discounted_price)
                    existing_product.approval_date = item.get('approval_date', existing_product.approval_date)
                    existing_product.is_archived = item.get('is_archived', existing_product.is_archived)
                    existing_product.review_count = item.get('review_count', existing_product.review_count)
                else:
                    new_product = Product(
                        id=item_id,
                        name=item.get('name'),
                        image_url=item.get('image_url'),
                        price=item.get('price'),
                        stock=item.get('stock', 0),
                        sku=item.get('sku'),
                        category=item.get('category'),
                        subcategory=item.get('subcategory'),
                        variant=item.get('variant'),
                        additional_images=item.get('additional_images'),
                        material=item.get('material'),
                        dimensions=item.get('dimensions'),
                        weight=item.get('weight'),
                        shipping_weight=item.get('shipping_weight'),
                        shipping_dimensions=item.get('shipping_dimensions'),
                        indoor_outdoor=item.get('indoor_outdoor'),
                        color=item.get('color'),
                        brand=item.get('brand'),
                        power_source=item.get('power_source'),
                        warranty=item.get('warranty'),
                        seller_id=item.get('seller_id'),
                        approval_status=item.get('approval_status', 'pending'),
                        admin_comments=item.get('admin_comments'),
                        display_status=item.get('display_status', 'hidden'),
                        rating=item.get('rating', 0.0),
                        reviews=item.get('reviews'),
                        tags=item.get('tags'),
                        sale_price=item.get('sale_price'),
                        is_on_sale=item.get('is_on_sale', False),
                        availability_status=item.get('availability_status', 'in_stock'),
                        discounted_price=item.get('discounted_price'),
                        approval_date=item.get('approval_date'),
                        is_archived=item.get('is_archived', False),
                        review_count=item.get('review_count', 0)
                    )
                    db.session.add(new_product)

            elif item_type == 'order':
                if not all(k in item for k in ['id', 'user_id']):
                    return jsonify({'error': f'Missing required order fields in item: {item}'}), 400
                if not User.query.get(item.get('user_id')):
                    return jsonify({'error': f'Invalid user_id {item.get("user_id")} in order: {item}'}), 400
                confirmed_receipt = item.get('confirmed_receipt', 0)
                has_rated = item.get('has_rated', 0)  # Added to handle has_rated
                if confirmed_receipt not in [0, 1]:
                    return jsonify({'error': f'Invalid confirmed_receipt value {confirmed_receipt} in order: {item}'}), 400
                if has_rated not in [0, 1]:  # Validate has_rated
                    return jsonify({'error': f'Invalid has_rated value {has_rated} in order: {item}'}), 400
                existing_order = Order.query.get(item_id) if item_id else None
                if existing_order:
                    existing_order.user_id = item.get('user_id', existing_order.user_id)
                    existing_order.status = item.get('status', existing_order.status)
                    existing_order.created_at = datetime.fromisoformat(item.get('created_at').replace('Z', '+00:00')) if item.get('created_at') else existing_order.created_at
                    existing_order.updated_at = datetime.fromisoformat(item.get('updated_at').replace('Z', '+00:00')) if item.get('updated_at') else existing_order.updated_at
                    existing_order.expected_delivery_start = datetime.fromisoformat(item.get('expected_delivery_start').replace('Z', '+00:00')).date() if item.get('expected_delivery_start') else existing_order.expected_delivery_start
                    existing_order.expected_delivery_end = datetime.fromisoformat(item.get('expected_delivery_end').replace('Z', '+00:00')).date() if item.get('expected_delivery_end') else existing_order.expected_delivery_end
                    existing_order.shipped_date = datetime.fromisoformat(item.get('shipped_date').replace('Z', '+00:00')).date() if item.get('shipped_date') else existing_order.shipped_date
                    existing_order.delivered_date = datetime.fromisoformat(item.get('delivered_date').replace('Z', '+00:00')) if item.get('delivered_date') else existing_order.delivered_date
                    existing_order.in_transit_date = datetime.fromisoformat(item.get('in_transit_date').replace('Z', '+00:00')).date() if item.get('in_transit_date') else existing_order.in_transit_date
                    existing_order.subtotal = decimal.Decimal(str(item.get('subtotal'))) if item.get('subtotal') is not None else existing_order.subtotal
                    existing_order.confirmed_receipt = confirmed_receipt
                    existing_order.has_rated = has_rated  # Update has_rated for existing order
                else:
                    new_order = Order(
                        id=item_id,
                        user_id=item.get('user_id'),
                        status=item.get('status', 'PENDING'),
                        created_at=datetime.fromisoformat(item.get('created_at').replace('Z', '+00:00')) if item.get('created_at') else datetime.utcnow(),
                        updated_at=datetime.fromisoformat(item.get('updated_at').replace('Z', '+00:00')) if item.get('updated_at') else datetime.utcnow(),
                        expected_delivery_start=datetime.fromisoformat(item.get('expected_delivery_start').replace('Z', '+00:00')).date() if item.get('expected_delivery_start') else None,
                        expected_delivery_end=datetime.fromisoformat(item.get('expected_delivery_end').replace('Z', '+00:00')).date() if item.get('expected_delivery_end') else None,
                        shipped_date=datetime.fromisoformat(item.get('shipped_date').replace('Z', '+00:00')).date() if item.get('shipped_date') else None,
                        delivered_date=datetime.fromisoformat(item.get('delivered_date').replace('Z', '+00:00')) if item.get('delivered_date') else None,
                        in_transit_date=datetime.fromisoformat(item.get('in_transit_date').replace('Z', '+00:00')).date() if item.get('in_transit_date') else None,
                        subtotal=decimal.Decimal(str(item.get('subtotal'))) if item.get('subtotal') is not None else None,
                        confirmed_receipt=confirmed_receipt,
                        has_rated=has_rated  # Set has_rated for new order
                    )
                    db.session.add(new_order)

            elif item_type == 'order_item':
                required_fields = ['id', 'order_id', 'product_id', 'quantity', 'price']
                missing_fields = [k for k in required_fields if k not in item or item[k] is None]
                if missing_fields:
                    return jsonify({'error': f'Missing or null order_item fields: {missing_fields} in item: {item}'}), 400
                if not isinstance(item['quantity'], int) or item['quantity'] <= 0:
                    return jsonify({'error': f'Invalid quantity, must be a positive integer in item: {item}'}), 400
                try:
                    price = decimal.Decimal(str(item['price']))
                    if price < 0:
                        raise ValueError
                except (ValueError, decimal.InvalidOperation):
                    return jsonify({'error': f'Invalid price, must be a non-negative number in item: {item}'}), 400
                has_rated = item.get('has_rated', 0)  # Handle has_rated for order_item
                if has_rated not in [0, 1]:
                    return jsonify({'error': f'Invalid has_rated value {has_rated} in order_item: {item}'}), 400
                if not Order.query.get(item['order_id']):
                    return jsonify({'error': f'Invalid order_id {item["order_id"]} in order_item: {item}'}), 400
                if not Product.query.get(item['product_id']):
                    return jsonify({'error': f'Invalid product_id {item["product_id"]} in order_item: {item}'}), 400
                existing_order_item = OrderItem.query.get(item_id) if item_id else None
                if existing_order_item:
                    existing_order_item.order_id = item.get('order_id', existing_order_item.order_id)
                    existing_order_item.product_id = item.get('product_id', existing_order_item.product_id)
                    existing_order_item.quantity = item.get('quantity', existing_order_item.quantity)
                    existing_order_item.price = price
                    existing_order_item.has_rated = has_rated  # Update has_rated for existing order_item
                else:
                    new_order_item = OrderItem(
                        id=item_id,
                        order_id=item['order_id'],
                        product_id=item['product_id'],
                        quantity=item['quantity'],
                        price=price,
                        has_rated=has_rated  # Set has_rated for new order_item
                    )
                    db.session.add(new_order_item)

            elif item_type == 'notification':
                if not all(k in item for k in ['id', 'user_id', 'message']):
                    return jsonify({'error': f'Missing required notification fields in item: {item}'}), 400
                existing_notification = Notification.query.get(item_id) if item_id else None
                if existing_notification:
                    existing_notification.user_id = item.get('user_id', existing_notification.user_id)
                    existing_notification.message = item.get('message', existing_notification.message)
                    existing_notification.is_read = item.get('is_read', existing_notification.is_read)
                    existing_notification.created_at = datetime.fromisoformat(item.get('created_at').replace('Z', '+00:00')) if item.get('created_at') else existing_notification.created_at
                else:
                    new_notification = Notification(
                        id=item_id,
                        user_id=item.get('user_id'),
                        message=item.get('message'),
                        is_read=item.get('is_read', False),
                        created_at=datetime.fromisoformat(item.get('created_at').replace('Z', '+00:00')) if item.get('created_at') else datetime.utcnow()
                    )
                    db.session.add(new_notification)

            elif item_type == 'chat_message':
                if not all(k in item for k in ['id', 'sender_id', 'receiver_id', 'message']):
                    return jsonify({'error': f'Missing required chat_message fields in item: {item}'}), 400
                existing_chat_message = ChatMessage.query.get(item_id) if item_id else None
                if existing_chat_message:
                    existing_chat_message.sender_id = item.get('sender_id', existing_chat_message.sender_id)
                    existing_chat_message.receiver_id = item.get('receiver_id', existing_chat_message.receiver_id)
                    existing_chat_message.message = item.get('message', existing_chat_message.message)
                    existing_chat_message.is_read = item.get('is_read', existing_chat_message.is_read)
                    existing_chat_message.created_at = datetime.fromisoformat(item.get('created_at').replace('Z', '+00:00')) if item.get('created_at') else existing_chat_message.created_at
                else:
                    new_chat_message = ChatMessage(
                        id=item_id,
                        sender_id=item.get('sender_id'),
                        receiver_id=item.get('receiver_id'),
                        message=item.get('message'),
                        is_read=item.get('is_read', False),
                        created_at=datetime.fromisoformat(item.get('created_at').replace('Z', '+00:00')) if item.get('created_at') else datetime.utcnow()
                    )
                    db.session.add(new_chat_message)

            else:
                return jsonify({'error': f'Unknown item type: {item_type}'}), 400

        db.session.commit()
        logging.info(f"Successfully synced {len(data)} items")
        return jsonify({'message': 'Data synced successfully'}), 201

    except IntegrityError as e:
        db.session.rollback()
        logging.error(f"Database integrity error syncing data: {str(e)}")
        return jsonify({'error': f'Database integrity error: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error syncing data: {str(e)}")
        return jsonify({'error': f'Failed to sync data: {str(e)}'}), 500
                               
# API endpoint to login (including relationships)
@app.route('/api/auth/login', methods=['POST'])
def api_login():  # Renamed from login to api_login
    email = request.json.get('email')
    password = request.json.get('password')
    
    if not email or not password:
        return jsonify({'message': 'Missing email or password'}), 400
    
    user = User.query.filter_by(email=email).first()
    
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    if user.password == password:
        session['user_id'] = user.id  # Set session for authentication
        return jsonify(user.to_dict()), 200
    else:
        return jsonify({'message': 'Invalid password'}), 401
                    
app.register_blueprint(api)

if __name__ == "__main__":
    app.run(debug=True)
