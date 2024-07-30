from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Products(db.Model):
    __tablename__ = "products"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String, nullable=False)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String, nullable=False)

    def __init__(self, name, quantity, description, price, category):
        self.name = name
        self.quantity = quantity
        self.description = description
        self.price = price
        self.category = category


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    phone = db.Column(db.Integer, nullable=False)
    password = db.Column(db.String, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    city = db.Column(db.String, nullable=True)
    address = db.Column(db.String, nullable=True)
    quantity_id = db.Column(db.String, nullable=True)
    product_name = db.Column(db.String, nullable=True)
    quantity = db.Column(db.Integer, nullable=True)
    price = db.Column(db.String, nullable=True)

    def __init__(
        self,
        name,
        phone,
        password,
        email,
        city,
        address,
        quantity_id,
        product_name,
        quantity,
        price,
    ):
        self.name = name
        self.email = email
        self.phone = phone
        self.password = password
        self.city = city
        self.address = address
        self.quantity_id = quantity_id
        self.product_name = product_name
        self.quantity = quantity
        self.price = price
