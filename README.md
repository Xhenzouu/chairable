# Chairable – E-Commerce Platform for Furniture & Home Decor 🪑🛋️🏡

A full-stack e-commerce platform for browsing, buying, and managing furniture and home & garden products. Chairable supports buyer and seller accounts, category-based browsing, cart and checkout flows, product favorites, and a companion mobile app.

Designed for real-world use, this system prioritizes:

- 🛍️ Smooth browsing and buying experience across desktop and mobile
- 🧾 Clear separation between buyer and seller flows
- 🎨 A warm, home-decor-inspired visual identity
- 📱 Feature parity between the web app and the Flutter mobile app

Current production version: **v1**

🔗 **Live Demo:** _Not deployed yet — currently runs locally._

## 🌍 Project Overview

Chairable is a home decor and furniture marketplace built to give small sellers a simple storefront and give shoppers an easy way to discover pieces for every room — Home Comfort, Garden & Outdoor, Dining, Living, and Bedroom.

The platform helps users:

- Discover furniture and decor by category, with discount badges and "New" tags
- Register as a buyer or a seller, with a dedicated seller dashboard and admin/commission tools
- Add items to cart, compare products, manage favorites, and complete checkout
- Track current orders and view purchase/order history
- Share their own room setups via the **#ShareableChairable** community collage
- Chat and get notified in real time (chat + notification support)
- Stay in the loop through newsletter subscriptions

## 🧩 Core Features

- 🔐 **User registration and login**, with forgot-password + OTP verification flow
- 🏪 **Seller registration and seller dashboard**, including business permit and valid ID upload for verification
- 🛡️ **Admin tools** — manage users, approvals, and commissions
- 📂 **Category browsing** across Home Comfort, Garden & Outdoor, Dining, Living, and Bedroom
- 🖼️ **Product showcase** with discount badges, "New" tags, and hover overlays (Add to Cart, Like, Share, Compare)
- ⚖️ **Product comparison** tool
- 🛒 **Shopping cart and checkout flow**, with cart notifications
- 🔎 **Product search & filtering**, sorting, and pagination
- ❤️ **Favorites** and a user profile with account settings and logout
- 📦 **Order management** — current orders, purchases, and order history with filtering
- 💬 **Live chat** and in-app notifications
- 🎠 **Slideshow/carousel** for featured room collections
- 📸 **#ShareableChairable** — a user-submitted image collage section
- 📧 **Newsletter subscription**
- 📱 **Mobile app** built with Flutter

## 👥 User Roles

| Role | Capabilities |
|------|--------------|
| **Buyer** | Browse products, search/filter, add to cart/favorites/comparison, checkout, track orders and purchases, manage profile |
| **Seller** | Everything a buyer can do, plus register as a seller (with business permit & valid ID verification), and manage products via the seller dashboard |
| **Admin** | Manage users, review seller approvals, and configure commissions |

## 🛒 Order & Checkout Flow

```
Browse / Search / Filter Products
        ↓
   Add to Cart (cart_items) → Cart Notification
        ↓
   Review Cart / Compare Items
        ↓
   Checkout → Order Created (orders)
        ↓
   Order Items Recorded (order_items)
        ↓
   Current Orders → Purchases (order history)
```

Favorites, comparison, and "Add to Cart" are all available directly from the product hover overlay, so users can save, compare, or purchase items without leaving the shop view.

## 📋 Database Schema Reference

| Table | Description |
|-------|-------------|
| `users` | User accounts (email, password hash, role) |
| `sellers` | Seller profiles linked to users (business permit, valid ID) |
| `products` | Product listings (name, description, price, category, image, discount, is_new) |
| `categories` | Product categories |
| `cart_items` | Cart entries (user_id, product_id, quantity) |
| `orders` | Order records |
| `order_items` | Individual items per order |
| `favorites` | User favorites |
| `newsletter_subscribers` | Email signups |

## 🧱 System Architecture

```
Browser (HTML/CSS/JS)
        ↓
   Flask Backend (Jinja2 templates + routes)
        ↓
   PostgreSQL Database
        ↓
   Mobile App (Flutter/Dart)
```

## 📁 Project Structure

```
ecommerceflask--28-/
├── ecommerceflask/
│   ├── app/
│   │   ├── static/
│   │   │   ├── css/
│   │   │   │   ├── navbar.css
│   │   │   │   ├── hero.css / hero2.css
│   │   │   │   ├── footer.css
│   │   │   │   ├── showcaseproduct.css
│   │   │   │   ├── product.css
│   │   │   │   ├── comparison.css
│   │   │   │   ├── cartmessage.css
│   │   │   │   ├── chat.css
│   │   │   │   ├── notification.css
│   │   │   │   ├── dashboard.css / seller.css / seller_styles.css
│   │   │   │   ├── manage_products.css
│   │   │   │   ├── filter.css / pagination.css / popover.css
│   │   │   │   ├── slideshow.css / collage.css / label.css
│   │   │   │   ├── regform.css / contact.css
│   │   │   │   ├── custom_style.css / styles.css
│   │   │   │   └── all.css / all.min.css
│   │   │   ├── images/
│   │   │   │   ├── logo.png
│   │   │   │   ├── hero.png
│   │   │   │   ├── product1.png ... product8.png
│   │   │   │   ├── slideshow1.png ... slideshow6.png
│   │   │   │   ├── homecomfort.png / gardenoutdoor.png
│   │   │   │   ├── trophy.png / guarantee.png / shipping.png / support.png
│   │   │   │   └── facebook.png / twitter.png
│   │   │   ├── js/
│   │   │   │   ├── cart.js / fetchCart.js / checkout.js
│   │   │   │   ├── item.js / orders.js / orders_filter.js
│   │   │   │   ├── filter.js / productfilter.js / seller_filter.js / sortby.js
│   │   │   │   ├── dashboard.js / manage_products.js
│   │   │   │   ├── chat.js / notification.js / popover.js
│   │   │   │   ├── pagination.js / preventback.js / shop.js / showmore.js / slideshow.js
│   │   │   │   └── min.js / popper.min.js / slim.min.js / scripts.js
│   │   │   └── uploads/
│   │   │       ├── business_permit/
│   │   │       └── valid_id/
│   │   ├── templates/
│   │   │   ├── index.html / shop.html / item.html / inner-productpage.html
│   │   │   ├── cart.html / checkout.html / comparison.html
│   │   │   ├── login.html / register.html / register_seller.html
│   │   │   ├── forgotpassword.html / forgotpassword_otp.html / verify_otp.html
│   │   │   ├── profile.html / account_settings.html / accounts.html
│   │   │   ├── dashboard.html / add_product.html / edit_product.html
│   │   │   ├── manage_products.html / archive.html / archived_products.html
│   │   │   ├── approvals.html / admin_users.html / admin_add_user.html / admin_edit_user.html / admin_commissions.html
│   │   │   ├── orders.html / current_orders.html / purchases.html
│   │   │   ├── contact.html / prevent_back.html
│   │   │   └── uploads/
│   │   │       ├── business_permit/
│   │   │       ├── products/
│   │   │       └── valid_id/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   └── routes.py
│   ├── data/
│   │   ├── countries.json
│   │   └── products.json
│   ├── cert.pem
│   ├── config.py
│   ├── key.pem
│   ├── openssl.cnf
│   └── run.py
└── README.md
```

## 🛠️ Tech Stack

- **Frontend:** HTML, CSS, JavaScript (vanilla, no framework)
- **Backend:** Python (Flask)
- **Templating:** Jinja2 (Flask templates)
- **Database:** PostgreSQL
- **Mobile:** Flutter (Dart)
- **Styling:** Custom CSS (separate files per component — navbar, hero, footer, showcase, dashboard, chat, notifications, etc.)
- **Icons:** Font Awesome 5.15.4
- **Local HTTPS:** self-signed cert (`cert.pem` / `key.pem`, generated via `openssl.cnf`)
- **Version Control:** Git, GitHub

## 📱 Mobile App

Chairable also ships as a native mobile experience built with **Flutter (Dart)**. The mobile app connects to the same Flask backend and PostgreSQL database as the web platform, so:

- Products, categories, and pricing stay in sync across web and mobile
- Cart, favorites, and orders are shared against the same `users`, `cart_items`, and `orders` tables
- Login and seller accounts created on the web work the same way in the app

This lets Chairable share one source of truth while offering both a browser-based storefront and an on-the-go shopping experience.

## ▶️ Running Locally

1. Clone the repo
2. `cd ecommerceflask--28-/ecommerceflask`
3. Create and activate a virtual environment:
   - Windows: `.\venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Set up your PostgreSQL database and configure connection details in `config.py` (or environment variables)
6. Run database migrations / create tables from `app/models.py`
7. Start the app: `python run.py`
   - The app is configured for local HTTPS using `cert.pem` and `key.pem` — if you haven't generated your own, regenerate them with `openssl.cnf` or adjust `run.py` to run over plain HTTP for local development
8. Visit `https://localhost:5000` (or the port set in `run.py`) in your browser

## 🚀 Future Roadmap

- ✅ User registration, login, forgot-password, and OTP verification
- ✅ Seller registration with business permit / valid ID verification
- ✅ Admin approvals and commission management
- ✅ Category browsing, product showcase, comparison, cart, and checkout
- ✅ Favorites, search, filtering, sorting, and pagination
- ✅ Order tracking (current orders + purchase history)
- ✅ Live chat and notifications
- ✅ #ShareableChairable collage and newsletter signup
- ✅ Flutter mobile app (initial version)
- 🔜 Live production deployment
- 🔜 Payment gateway integration
- 🔜 Seller analytics dashboard
- 🔜 Product reviews and ratings
- 🔜 Push notifications on the mobile app

## 🤝 Contributing

Pull requests welcome! Please:

- ✅ Follow the existing CSS file structure (one file per component)
- 🔒 Never commit real user data, business permits, valid IDs, or credentials (`cert.pem` / `key.pem` should stay out of production repos)
- 📸 Optimize images before adding them to `static/images/`
- 🧪 Test both web and mobile flows when changing shared backend logic

## About

A full-stack e-commerce platform for furniture and home & garden products, featuring seller verification, cart and checkout flows, order tracking, live chat, and a companion Flutter mobile app. 🪑🛋️🏡

### Topics

`flask` `postgresql` `flutter` `ecommerce` `furniture` `python` `javascript`

---

⭐ Stars · 👀 Watchers · 🍴 Forks
