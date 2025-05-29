# app/models.py
from app import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import ENUM

# Define the order_status enum based on your database constraint
OrderStatus = ENUM(
    'PENDING', 'APPROVED', 'SHIPPED', 'IN_TRANSIT', 'DELIVERED', 'CANCELLED',
    name='order_status', create_type=False  # Set to False if the type already exists in the DB
)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    gender = db.Column(db.String(50))
    country = db.Column(db.String(100))
    street_address = db.Column(db.String(255))
    city = db.Column(db.String(100))
    province = db.Column(db.String(100))
    zip_code = db.Column(db.String(20))
    phone = db.Column(db.String(20))
    role = db.Column(db.String(10), nullable=False, default='user')
    is_archived = db.Column(db.Boolean, nullable=False, default=False)
    approval_status = db.Column(db.String(50), nullable=False, default='pending')
    approved = db.Column(db.Boolean, nullable=False, default=False)
    otp_verified = db.Column(db.Boolean, default=False)
    valid_id = db.Column(db.String(20))
    business_permit = db.Column(db.String(1000))

    # Relationships with explicit foreign keys
    products = db.relationship('Product', backref='seller', lazy='dynamic', foreign_keys='Product.seller_id')
    orders_as_buyer = db.relationship('Order', backref='user', lazy='dynamic', foreign_keys='Order.user_id')
    notifications = db.relationship("Notification", back_populates="user")

    def __repr__(self):
        return f"<User {self.name}>"

    def to_dict(self):
        return {
            "type": "user",
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "password": self.password,  # Note: Consider removing this in production
            "gender": self.gender,
            "country": self.country,
            "street_address": self.street_address,
            "city": self.city,
            "province": self.province,
            "zip_code": self.zip_code,
            "phone": self.phone,
            "role": self.role,
            "is_archived": self.is_archived,
            "approval_status": self.approval_status,
            "approved": self.approved,
            "otp_verified": self.otp_verified,
            "valid_id": self.valid_id,
            "business_permit": self.business_permit
        }

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(OrderStatus, nullable=False, default='PENDING')
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    expected_delivery_start = db.Column(db.Date)
    expected_delivery_end = db.Column(db.Date)
    shipped_date = db.Column(db.Date)
    delivered_date = db.Column(db.DateTime)
    in_transit_date = db.Column(db.Date)
    subtotal = db.Column(db.Numeric(10, 2))
    confirmed_receipt = db.Column(db.Integer, nullable=False, default=0)  # Matches schema: integer, default 0
    has_rated = db.Column(db.Integer, nullable=False, default=0)

    items = db.relationship('OrderItem', backref='order', lazy='dynamic')

    def __repr__(self):
        return f"<Order {self.id}>"

    def to_dict(self):
        return {
            'type': 'order',
            'id': self.id,
            'user_id': self.user_id,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'expected_delivery_start': self.expected_delivery_start.isoformat() if self.expected_delivery_start else None,
            'expected_delivery_end': self.expected_delivery_end.isoformat() if self.expected_delivery_end else None,
            'shipped_date': self.shipped_date.isoformat() if self.shipped_date else None,
            'delivered_date': self.delivered_date.isoformat() if self.delivered_date else None,
            'in_transit_date': self.in_transit_date.isoformat() if self.in_transit_date else None,
            'subtotal': float(self.subtotal) if self.subtotal is not None else None,
            'confirmed_receipt': self.confirmed_receipt,
            'has_rated': self.has_rated
        }

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    image_url = db.Column(db.String(1000), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2))
    stock = db.Column(db.Integer, default=0)
    sku = db.Column(db.String(100), unique=True)
    category = db.Column(db.String(50))
    subcategory = db.Column(db.String(255))
    variant = db.Column(db.String(255))
    additional_images = db.Column(db.String)
    material = db.Column(db.String(255))
    dimensions = db.Column(db.String(255))
    weight = db.Column(db.Numeric(6, 2))
    shipping_weight = db.Column(db.Numeric(6, 2))
    shipping_dimensions = db.Column(db.String(255))
    indoor_outdoor = db.Column(db.String(20))
    color = db.Column(db.String(100))
    brand = db.Column(db.String(100))
    power_source = db.Column(db.String(100))
    warranty = db.Column(db.String(100))
    seller_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    approval_status = db.Column(db.String(20), default='pending')
    admin_comments = db.Column(db.Text)
    display_status = db.Column(db.String(20), default='hidden')
    rating = db.Column(db.Numeric(3, 2), default=0.00)
    reviews = db.Column(db.Text)
    tags = db.Column(db.ARRAY(db.String))
    sale_price = db.Column(db.Numeric(10, 2))
    is_on_sale = db.Column(db.Boolean, default=False)
    availability_status = db.Column(db.String(20), default='in_stock')
    discounted_price = db.Column(db.Numeric(10, 2))
    approval_date = db.Column(db.DateTime(timezone=True), default=db.func.now())
    is_archived = db.Column(db.Boolean, default=False)
    review_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Product {self.name}>"

    def to_dict(self):
        return {
            'type': 'product',
            'id': self.id,
            'name': self.name,
            'image_url': self.image_url,
            'description': self.description,
            'price': float(self.price) if self.price is not None else None,
            'stock': self.stock,
            'sku': self.sku,
            'category': self.category,
            'subcategory': self.subcategory,
            'variant': self.variant,
            'additional_images': self.additional_images,
            'material': self.material,
            'dimensions': self.dimensions,
            'weight': float(self.weight) if self.weight is not None else None,
            'shipping_weight': float(self.shipping_weight) if self.shipping_weight is not None else None,
            'shipping_dimensions': self.shipping_dimensions,
            'indoor_outdoor': self.indoor_outdoor,
            'color': self.color,
            'brand': self.brand,
            'power_source': self.power_source,
            'warranty': self.warranty,
            'seller_id': self.seller_id,
            'approval_status': self.approval_status,
            'admin_comments': self.admin_comments,
            'display_status': self.display_status,
            'rating': float(self.rating) if self.rating is not None else 0.0,
            'reviews': self.reviews,
            'tags': self.tags if self.tags is not None else [],
            'sale_price': float(self.sale_price) if self.sale_price is not None else None,
            'is_on_sale': self.is_on_sale,
            'availability_status': self.availability_status,
            'discounted_price': float(self.discounted_price) if self.discounted_price is not None else None,
            'approval_date': self.approval_date.isoformat() if self.approval_date else None,
            'is_archived': self.is_archived,
            'review_count': self.review_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class ProductApproval(db.Model):
    __tablename__ = 'product_approvals'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    approval_status = db.Column(db.String(20), nullable=False)
    approval_date = db.Column(db.DateTime(timezone=True), default=db.func.now())
    comments = db.Column(db.Text)
    product_name = db.Column(db.String(255))
    product_description = db.Column(db.Text)
    seller_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    category = db.Column(db.String(50))
    subcategory = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    admin = db.relationship('User', foreign_keys=[admin_id])
    seller = db.relationship('User', foreign_keys=[seller_id])
    product = db.relationship('Product', backref='approvals')

    def __repr__(self):
        return f"<ProductApproval {self.id}, Status: {self.approval_status}>"

    def to_dict(self):
        return {
            'type': 'product_approval',
            'id': self.id,
            'product_id': self.product_id,
            'admin_id': self.admin_id,
            'approval_status': self.approval_status,
            'approval_date': self.approval_date.isoformat() if self.approval_date else None,
            'comments': self.comments,
            'product_name': self.product_name,
            'product_description': self.product_description,
            'seller_id': self.seller_id,
            'category': self.category,
            'subcategory': self.subcategory,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    has_rated = db.Column(db.Integer, nullable=False, default=0)  # Added to match schema: integer, default 0

    product = db.relationship('Product', backref='order_items')

    def __repr__(self):
        return f"<OrderItem {self.id}, Order {self.order_id}, Product {self.product_id}>"

    def to_dict(self):
        return {
            'type': 'order_item',
            'id': self.id,
            'order_id': self.order_id,
            'product_id': self.product_id,
            'quantity': self.quantity,
            'price': float(self.price) if self.price is not None else None,
            'has_rated': self.has_rated  # Added to serialization
        }

class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="notifications")

    def to_dict(self):
        return {
            'type': 'notification',
            'id': self.id,
            'user_id': self.user_id,
            'message': self.message,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)

    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_messages')

    def __repr__(self):
        return f"<ChatMessage from {self.sender_id} to {self.receiver_id}: {self.message}>"

    def to_dict(self):
        return {
            'type': 'chat_message',
            'id': self.id,
            'sender_id': self.sender_id,
            'receiver_id': self.receiver_id,
            'message': self.message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_read': self.is_read
        }