# Chairable – E-Commerce Platform for Furniture & Home Decor 🪑🛋️🏡

A full-stack e-commerce platform for browsing, buying, and managing furniture and home & garden products. Chairable supports buyer and seller accounts, category-based browsing, cart and checkout flows, product favorites, and a companion mobile app.

Designed for real-world use, this system prioritizes:

- 🛍️ Smooth browsing and buying experience across desktop and mobile
- 🧾 Clear separation between buyer and seller flows
- 🎨 A warm, home-decor-inspired visual identity
- 📱 Feature parity between the web app and the Flutter mobile app

Current production version: **v1**

🔗 **Live Demo:** _[Add your deployed link if available]_

## 🌍 Project Overview

Chairable is a home decor and furniture marketplace built to give small sellers a simple storefront and give shoppers an easy way to discover pieces for every room — Home Comfort, Garden & Outdoor, Dining, Living, and Bedroom.

The platform helps users:

- Discover furniture and decor by category, with discount badges and "New" tags
- Register as a buyer or a seller, with a dedicated seller dashboard
- Add items to cart, manage favorites, and complete checkout
- Share their own room setups via the **#ShareableChairable** community collage
- Stay in the loop through newsletter subscriptions

## 🧩 Core Features

- 🔐 **User registration and login**, with a forgot-password recovery flow
- 🏪 **Seller registration and seller dashboard** for listing and managing products
- 📂 **Category browsing** across Home Comfort, Garden & Outdoor, Dining, Living, and Bedroom
- 🖼️ **Product showcase** with discount badges, "New" tags, and hover overlays (Add to Cart, Like, Share, Compare)
- 🛒 **Shopping cart and checkout flow**
- 🔎 **Product search**, favorites, and a user profile with logout
- 🎠 **Slideshow/carousel** for featured room collections
- 📸 **#ShareableChairable** — a user-submitted image collage section
- 📧 **Newsletter subscription**
- 📱 **Mobile app** built with Flutter

## 👥 User Roles

| Role | Capabilities |
|------|--------------|
| **Buyer** | Browse products, search, add to cart/favorites, checkout, manage profile |
| **Seller** | Everything a buyer can do, plus register as a seller and manage product listings via the seller dashboard |

## 🛒 Order & Checkout Flow

```
Browse / Search Products
        ↓
   Add to Cart (cart_items)
        ↓
   Review Cart
        ↓
   Checkout → Order Created (orders)
        ↓
   Order Items Recorded (order_items)
        ↓
   Order Confirmation
```

Favorites and "Add to Cart" are both available directly from the product hover overlay, so users can save or purchase items without leaving the shop view.

## 🖼️ Screenshots

> Add your screenshots below to complete this section.

| Landing Page | Login Page |
|--------------|------------|
| `_(add landing page screenshot here)_` | `_(add login page screenshot here)_` |

## 📋 Database Schema Reference

| Table | Description |
|-------|-------------|
| `users` | User accounts (email, password hash, role) |
| `sellers` | Seller profiles linked to users |
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
chairable/
├── static/
│   ├── css/
│   │   ├── navbar.css
│   │   ├── hero.css
│   │   ├── footer.css
│   │   ├── showcaseproduct.css
│   │   ├── slideshow.css
│   │   ├── collage.css
│   │   ├── label.css
│   │   ├── regform.css
│   │   └── custom_style.css
│   ├── js/
│   │   ├── showmore.js
│   │   ├── scripts.js
│   │   └── slideshow.js
│   └── images/
│       ├── logo.png
│       ├── product1.png ... product8.png
│       ├── slideshow1.png ... slideshow6.png
│       ├── homecomfort.png
│       └── gardenoutdoor.png
├── templates/
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── register_seller.html
│   ├── forgot_password.html
│   ├── shop.html
│   ├── cart.html
│   ├── about.html
│   └── contact.html
├── app.py            # Flask routes
├── models.py         # PostgreSQL models
├── requirements.txt
└── README.md
```

## 🛠️ Tech Stack

- **Frontend:** HTML, CSS, JavaScript (vanilla, no framework)
- **Backend:** Python (Flask)
- **Templating:** Jinja2 (Flask templates)
- **Database:** PostgreSQL
- **Mobile:** Flutter (Dart)
- **Styling:** Custom CSS (separate files for navbar, hero, footer, showcase, slideshow, collage, label, regform)
- **Icons:** Font Awesome 5.15.4
- **Version Control:** Git, GitHub

## 📱 Mobile App

Chairable also ships as a native mobile experience built with **Flutter (Dart)**. The mobile app connects to the same Flask backend and PostgreSQL database as the web platform, so:

- Products, categories, and pricing stay in sync across web and mobile
- Cart, favorites, and orders are shared against the same `users`, `cart_items`, and `orders` tables
- Login and seller accounts created on the web work the same way in the app

This lets Chairable share one source of truth while offering both a browser-based storefront and an on-the-go shopping experience.

## ☁️ Cloud Database

_Add details here once deployed — e.g. hosting provider, connection method, and whether a local PostgreSQL instance is required for development._

## ▶️ Running Locally

1. Clone the repo
2. `cd chairable`
3. Create and activate a virtual environment:
   - Windows: `.\venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Set up your PostgreSQL database and configure connection details (e.g. via environment variables)
6. Run database migrations / create tables from `models.py`
7. Start the app: `python app.py`
8. Visit `http://localhost:5000` in your browser

## 🚀 Future Roadmap

- ✅ User registration, login, and forgot-password flow
- ✅ Seller registration and dashboard
- ✅ Category browsing, product showcase, cart, and checkout
- ✅ Favorites, search, and user profile
- ✅ #ShareableChairable collage and newsletter signup
- ✅ Flutter mobile app (initial version)
- 🔜 Payment gateway integration
- 🔜 Order tracking and order history page
- 🔜 Seller analytics dashboard
- 🔜 Product reviews and ratings
- 🔜 Push notifications on the mobile app
- 🔜 Admin panel for platform-wide management

## 🤝 Contributing

Pull requests welcome! Please:

- ✅ Follow the existing CSS file structure (one file per component)
- 🔒 Never commit real user data or credentials
- 📸 Optimize images before adding them to `static/images/`
- 🧪 Test both web and mobile flows when changing shared backend logic

## About

A full-stack e-commerce platform for furniture and home & garden products, featuring seller registration, cart and checkout flows, and a companion Flutter mobile app. 🪑🛋️🏡

### Topics

`flask` `postgresql` `flutter` `ecommerce` `furniture` `python` `javascript`

---

⭐ Stars · 👀 Watchers · 🍴 Forks
