from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from datetime import datetime

# ---------------- APP SETUP ----------------
app = Flask(__name__)

# ---------------- CONFIG ----------------
app.config["SQLALCHEMY_DATABASE_URI"] = (
    "mysql+mysqlconnector://root:sqlMari$22@localhost/ecommerce_api"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
ma = Marshmallow(app)

# ---------------- MODELS ----------------
class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    orders = db.relationship("Order", backref="user", cascade="all, delete")


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    items = db.relationship(
        "OrderProduct",
        cascade="all, delete-orphan"
    )

    @property
    def total_price(self):
        return sum(item.product.price * item.quantity for item in self.items)


class OrderProduct(db.Model):
    __tablename__ = "order_product"

    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), primary_key=True)
    quantity = db.Column(db.Integer, nullable=False, default=1)

    product = db.relationship("Product")

# ---------------- SCHEMAS ----------------
class ProductSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Product


class OrderProductSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = OrderProduct

    product = ma.Nested(ProductSchema)


class OrderSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Order
        include_fk = True

    items = ma.Nested(OrderProductSchema, many=True)
    total_price = ma.Float(dump_only=True)


class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User

    orders = ma.Nested(OrderSchema, many=True)


user_schema = UserSchema()
users_schema = UserSchema(many=True)
product_schema = ProductSchema()
products_schema = ProductSchema(many=True)
order_schema = OrderSchema()
orders_schema = OrderSchema(many=True)

# ---------------- USER ROUTES ----------------
@app.route("/users", methods=["GET"])
def get_users():
    users = User.query.all()
    return users_schema.jsonify(users)


@app.route("/users/<int:id>", methods=["GET"])
def get_user(id):
    user = User.query.get_or_404(id)
    return user_schema.jsonify(user)


@app.route("/users", methods=["POST"])
def create_user():
    data = request.json

    if not all(k in data for k in ("name", "address", "email")):
        return jsonify({"error": "Missing required fields"}), 400

    user = User(
        name=data["name"],
        address=data["address"],
        email=data["email"]
    )
    db.session.add(user)
    db.session.commit()
    return user_schema.jsonify(user), 201


@app.route("/users/<int:id>", methods=["PUT"])
def update_user(id):
    user = User.query.get_or_404(id)
    data = request.json

    user.name = data.get("name", user.name)
    user.address = data.get("address", user.address)

    db.session.commit()
    return user_schema.jsonify(user)


@app.route("/users/<int:id>", methods=["DELETE"])
def delete_user(id):
    user = User.query.get_or_404(id)
    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "User deleted"})


# ---------------- PRODUCT ROUTES ----------------
@app.route("/products", methods=["GET"])
def get_products():
    return products_schema.jsonify(Product.query.all())


@app.route("/products/<int:id>", methods=["GET"])
def get_product(id):
    return product_schema.jsonify(Product.query.get_or_404(id))


@app.route("/products", methods=["POST"])
def create_product():
    data = request.json

    if not all(k in data for k in ("product_name", "price")):
        return jsonify({"error": "Missing required fields"}), 400

    product = Product(
        product_name=data["product_name"],
        price=data["price"]
    )
    db.session.add(product)
    db.session.commit()
    return product_schema.jsonify(product), 201


@app.route("/products/<int:id>", methods=["PUT"])
def update_product(id):
    product = Product.query.get_or_404(id)
    data = request.json

    product.product_name = data.get("product_name", product.product_name)
    product.price = data.get("price", product.price)

    db.session.commit()
    return product_schema.jsonify(product)


@app.route("/products/<int:id>", methods=["DELETE"])
def delete_product(id):
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    return jsonify({"message": "Product deleted"})


# ---------------- ORDER ROUTES ----------------
@app.route("/orders", methods=["POST"])
def create_order():
    data = request.json

    if "user_id" not in data:
        return jsonify({"error": "user_id required"}), 400

    order = Order(
        user_id=data["user_id"],
        order_date=datetime.strptime(
            data.get("order_date", datetime.utcnow().strftime("%Y-%m-%d")),
            "%Y-%m-%d"
        )
    )
    db.session.add(order)
    db.session.commit()
    return order_schema.jsonify(order), 201


@app.route("/orders/<int:order_id>/add_product/<int:product_id>", methods=["PUT"])
def add_product(order_id, product_id):
    quantity = request.json.get("quantity", 1)

    order = Order.query.get_or_404(order_id)
    product = Product.query.get_or_404(product_id)

    item = OrderProduct.query.filter_by(
        order_id=order.id,
        product_id=product.id
    ).first()

    if item:
        item.quantity += quantity
    else:
        item = OrderProduct(
            order_id=order.id,
            product_id=product.id,
            quantity=quantity
        )
        db.session.add(item)

    db.session.commit()
    return order_schema.jsonify(order)


@app.route("/orders/<int:order_id>/remove_product/<int:product_id>", methods=["DELETE"])
def remove_product(order_id, product_id):
    item = OrderProduct.query.filter_by(
        order_id=order_id,
        product_id=product_id
    ).first_or_404()

    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": "Product removed from order"})


@app.route("/orders/user/<int:user_id>", methods=["GET"])
def get_orders_for_user(user_id):
    orders = Order.query.filter_by(user_id=user_id).all()
    return orders_schema.jsonify(orders)


# ---------------- INIT ----------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)