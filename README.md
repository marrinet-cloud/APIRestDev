This project is a RESTful E-Commerce API built with **Flask**, **SQLAlchemy**, and **MySQL**. It supports users, products, and orders, including **order quantities**, **automatic order totals**, and clean relational modeling.

The API is designed to demonstrate:

* Proper relational database modeling
* Many-to-many relationships with extra fields
* RESTful API design
* Error handling & validation
* Practical API testing with Postman

 Tech Stack

* Python 3
* Flask
* Flask-SQLAlchemy
* Flask-Marshmallow
* MySQL
* Postman (for testing)


Database Models

User

* id
* name
* email (unique)
* address

Product

* id
* product_name
* price

 order

* id
* order_date
* user_id
* items (relationship)
* total_price (calculated property)

OrderProduct (Association Table)

This table enables **quantity per product per order**.

* order_id (FK)
* product_id (FK)
* quantity

 Key Features

Order Quantities

Products added to an order include a quantity. Adding the same product again increases quantity instead of duplicating rows.

Automatic Order Totals

Order totals are calculated dynamically using a model property:


@property
def total_price(self):
    return sum(item.product.price * item.quantity for item in self.items)

 Error Handling

* Duplicate emails return `409 Conflict`
* Missing or invalid JSON returns `400 Bad Request`
* Not found resources return `404 Not Found`

How to Run the Project (Start to Finish)

Clone & Set Up Environment


python -m venv venv
venv\Scripts\activate
pip install flask flask-sqlalchemy flask-marshmallow mysql-connector-python


Configure Database

Create a MySQL database (example: `ecommerce_db`).

Update `app.py` with your DB credentials:

mysql+mysqlconnector://user:password@localhost/ecommerce_db


Run the Server

python app.py

Server runs at:

http://127.0.0.1:5000

 API Testing (Postman)

Important Postman Rules

* Body → raw → JSON
* Header: `Content-Type: application/json`

### Recommended Test Order

1. Create User
2. Create Product(s)
3. Create Order
4. Add Product to Order (with quantity)
5. Get Orders for User

 Sample API Response

{
  "id": 1,
  "user_id": 2,
  "order_date": "2026-01-25",
  "total_price": 89.97,
  "items": [
    {
      "quantity": 3,
      "product": {
        "id": 1,
        "product_name": "Keyboard",
        "price": 29.99
      }
    }
  ]
}


Design Decisions

* **Association Object Pattern** used for quantities
* **Calculated fields** handled at the model layer
* **No authentication** to reduce complexity and highlight ORM design
* **Schema nesting** for clean JSON responses
