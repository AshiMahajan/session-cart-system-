from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    make_response,
    session,
)
from sqlalchemy import func

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SECRET_KEY"] = "abczyx"  # Secret key for session management

from model.model import Products, User, db

db.init_app(app)


##### User's view #####


@app.route("/atoz", methods=["GET"])
def user():
    products = Products.query.all()
    total_count = 0

    # Calculate the total count of items in the cart based on cookies
    for cookie in request.cookies:
        if cookie.startswith("product_"):
            product_id = int(cookie.split("_")[1])
            product = db.session.query(Products).filter_by(id=product_id).first()
            if product:
                cart_quant = int(
                    request.cookies.get(f"product_{product.id}_quantity", 0)
                )
                total_count += cart_quant

    if products:
        return render_template(
            "atoz/atoz.html", products=products, total_count=total_count
        )
    return "No products found."


@app.route("/cart/<int:product_id>", methods=["POST"])
def cart(product_id):
    product = db.session.query(Products).filter_by(id=product_id).first()
    if product:
        cart_quant = int(request.cookies.get(f"product_{product.id}_quantity", 0))
        cart_quant += 1

        if cart_quant > product.quantity:
            flash("Sorry, not enough stock available.")
            return redirect(url_for("user"))

        resp = make_response(redirect(url_for("user")))
        resp.set_cookie(f"product_{product.id}_quantity", str(cart_quant))
        flash(f"'{product.name}' added to cart.")
        return resp
    else:
        flash("Product not found.")
        return redirect(url_for("user"))


@app.route("/view_cart", methods=["GET"])
def view_cart():
    product_ids = []
    products_in_cart = []
    total_count = 0

    for cookie in request.cookies.keys():
        if cookie.startswith("product_"):
            product_id = int(cookie.split("_")[1])
            product_ids.append(product_id)
            product = db.session.query(Products).filter_by(id=product_id).first()
            if product:
                cart_quant = int(
                    request.cookies.get(f"product_{product.id}_quantity", 0)
                )
                total_count += cart_quant
                product.calculated_price = product.price * cart_quant
                products_in_cart.append(product)
    return render_template(
        "atoz/view_cart.html",
        products=products_in_cart,
        total_count=total_count,
    )


@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    if "user_mail" in session:
        user = db.session.query(User).filter_by(name=session["user_mail"]).first()
        if user and user.city and user.address:
            return redirect(url_for("view_detail"))
        else:
            return redirect(url_for("address"))
    else:
        if request.method == "POST":
            name = request.form["name"]
            email = request.form["email"]
            if not name or not email:
                flash("Please enter your name and email.")
                return redirect(url_for("checkout"))
            user = db.session.query(User).filter_by(name=name).first()
            if user and user.name == name and user.email == email:
                session["user_mail"] = user.name
                return redirect(url_for("user"))
            else:
                flash("Accound doesn't exist. Create a new one!")
                return render_template("signup.html")

    return render_template("checkout.html")


@app.route("/checkout/address", methods=["GET", "POST"])
def address():
    if "user_mail" in session:
        if request.method == "POST":
            name = session["user_mail"]
            city = request.form["city"]
            address = request.form["address"]
            user = db.session.query(User).filter_by(name=name).first()
            if user:
                user.city = city
                user.address = address
                db.session.commit()
            return redirect(url_for("view_detail"))
        return render_template("atoz/address.html")
    return redirect(url_for("user"))


@app.route("/checkout/details", methods=["GET", "POST"])
def view_detail():
    if "user_mail" in session:
        product_ids = []
        products_in_cart = []
        total_count = 0

        user = db.session.query(User).filter_by(name=session["user_mail"]).first()

        for cookie in request.cookies:
            if cookie.startswith("product_"):
                product_id = int(cookie.split("_")[1])
                product_ids.append(product_id)
                product = db.session.query(Products).filter_by(id=product_id).first()
                if product:
                    cart_quant = int(
                        request.cookies.get(f"product_{product.id}_quantity", 0)
                    )
                    total_count += cart_quant
                    product.calculated_price = product.price * cart_quant
                    products_in_cart.append(product)
        return render_template(
            "atoz/details.html",
            products=products_in_cart,
            total_count=total_count,
            user=user,
        )
    return redirect(url_for("user"))


@app.route("/checkout/pay", methods=["GET", "POST"])
def pay():
    if "user_mail" in session:
        if request.method == "POST":
            otp = request.form["otp"]
            user = db.session.query(User).filter_by(name=session["user_mail"]).first()
            product_details = []
            total_price = 0
            if len(otp) == 6:
                for cookie in request.cookies:
                    if cookie.startswith("product_"):
                        product_id = int(cookie.split("_")[1])
                        product = (
                            db.session.query(Products).filter_by(id=product_id).first()
                        )
                        #
                        product_n = (
                            db.session.query(Products)
                            .filter_by(name=product.name)
                            .first()
                        )
                        product_p = (
                            db.session.query(Products)
                            .filter_by(price=product.price)
                            .first()
                        )
                        if not product_id:
                            flash("Product ID not found in cookies.")
                            return redirect(url_for("user"))
                        if not product.name:
                            flash("Product name not found.")
                            return redirect(url_for("user"))
                        if not product.price:
                            flash("Product price not found.")
                            return redirect(url_for("user"))
                        cart_quant = int(
                            request.cookies.get(f"product_{product.id}_quantity", 0)
                        )
                        user.quantity_id = product_id
                        user.product_name = product.name
                        user.quantity = cart_quant
                        user.price = product.price * cart_quant

                        db.session.commit()
                        #
                        resp = make_response(redirect(url_for("success")))
                        products = db.session.query(Products).all()
                        for product in products:
                            cookie_name = f"product_{product.id}_quantity"
                            if cookie_name in request.cookies:
                                resp.delete_cookie(cookie_name)
                        return resp
                        #
                return redirect(url_for("success"))
            else:
                flash("Invalid OTP. Please enter a 6-digit OTP.")
                return render_template("atoz/pay.html", otp=otp)
        return render_template("atoz/pay.html", otp="")
    return redirect(url_for("user"))


@app.route("/success", methods=["GET", "POST"])
def success():
    if "user_mail" in session:
        return render_template("atoz/success.html")
    return redirect(url_for("user"))


@app.route("/cart/increment/<int:product_id>", methods=["POST"])
def increment_cart(product_id):
    product = db.session.query(Products).filter_by(id=product_id).first()
    if product:
        cart_quant = int(request.cookies.get(f"product_{product.id}_quantity", 0))
        if cart_quant < product.quantity:
            cart_quant += 1
        else:
            flash("Sorry, not enough stock available.")
            return redirect(url_for("view_cart"))
        resp = make_response(redirect(url_for("view_cart")))
        resp.set_cookie(f"product_{product.id}_quantity", str(cart_quant))
        return resp
    else:
        flash("Product not found.")
        return redirect(url_for("view_cart"))


@app.route("/cart/decrement/<int:product_id>", methods=["POST"])
def decrement_cart(product_id):
    product = db.session.query(Products).filter_by(id=product_id).first()
    if product:
        cart_quant = int(request.cookies.get(f"product_{product.id}_quantity", 0))
        if cart_quant > 0:
            cart_quant -= 1
        resp = make_response(redirect(url_for("view_cart")))
        resp.set_cookie(f"product_{product.id}_quantity", str(cart_quant))
        if cart_quant == 0:
            resp.delete_cookie(f"product_{product.id}_quantity")
        return resp
    else:
        flash("Product not found.")
        return redirect(url_for("view_cart"))


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if "user_mail" not in session:
        if request.method == "POST":
            name = request.form.get("name")
            email = request.form.get("email")
            phone = request.form.get("phone")
            password = request.form.get("password")

            # Validate input fields
            if not name or not email or not phone or not password:
                flash("Please enter all the fields.")
                return redirect(url_for("signup"))

            # Check if email already exists in the database
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                flash(
                    "Account with this email is already created, use a different email!"
                )
                return redirect(url_for("signup"))

            existing_phone = User.query.filter_by(phone=phone).first()
            if existing_phone:
                flash(
                    "Account with this phone number is already created, use a different email!"
                )
                return redirect(url_for("signup"))

            if len(password) < 8:
                flash("Password must be at least 8 characters long.")
                return redirect(url_for("signup"))

            # hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

            user = User(
                name=name,
                email=email,
                phone=phone,
                password=password,
                city=None,
                address=None,
                quantity_id=None,
                product_name=None,
                quantity=None,
                price=None,
            )
            db.session.add(user)
            db.session.commit()

            flash("Account created successfully!")
            return redirect(url_for("user"))
        else:
            return render_template("signup.html")
    else:
        return redirect(url_for("user"))


@app.route("/update_details", methods=["GET", "POST"])
def update_user_details():
    if "user_mail" in session:
        user = db.session.query(User).filter_by(name=session["user_mail"]).first()
        if request.method == "POST":
            if user:
                phone = request.form.get("phone")
                city = request.form.get("city")
                address = request.form.get("address")
                if phone and city and address:
                    user.phone = phone
                    user.city = city
                    user.address = address
                    db.session.commit()
                    flash("updated")
                    return redirect(url_for("view_detail"))
                else:
                    flash("Please fill in all the fields!")
                    return redirect(url_for("view_detail"))
        else:
            flash("User not found! Login again")
            return redirect(url_for("user"))
        return redirect(url_for("user"))
    else:
        flash("User not logged in.")
        return redirect(url_for("user"))


@app.route("/logout", methods=["GET", "POST"])
def logout():
    resp = make_response(redirect(url_for("user")))
    session.pop("user_mail", None)
    products = db.session.query(Products).all()
    for product in products:
        cookie_name = f"product_{product.id}_quantity"
        if cookie_name in request.cookies:
            resp.delete_cookie(cookie_name)
    return resp


##### User's view ends here #####


##### Admin's Dashboard #####


@app.route("/dashboard", methods=["GET", "POST"])
def dashboard_products():
    products = db.session.query(Products).all()
    if products:
        return render_template("dash.html", products=products)
    else:
        return render_template("index.html")


@app.route("/add_product", methods=["POST"])
def add_product():
    if request.method == "POST":
        category = request.form["category"]
        name = request.form["name"]
        quantity = request.form["quantity"]
        description = request.form["description"]
        price = request.form["price"]

        if category == "Select a category":
            flash("Please select a category.")
            return redirect(url_for("dashboard_products"))
        try:
            quantity = int(quantity)
        except ValueError:
            flash("Invalid quantity. Enter a valid quantity.")
            return redirect(url_for("dashboard_products"))
        try:
            price = float(price)
        except ValueError:
            flash("Invalid price. Enter a valid number.")
            return redirect(url_for("dashboard_products"))

        if not category or not name or not quantity or not description or not price:
            flash("*Please fill all the required fields!")
            return redirect(url_for("dashboard_products"))
        if price < 0:
            flash("Price cannot be negative.")
            return redirect(url_for("dashboard_products"))
        if quantity < 0:
            flash("Quantity cannot be negative.")
            return redirect(url_for("dashboard_products"))
        else:
            product = Products(
                name=name,
                quantity=quantity,
                description=description,
                price=price,
                category=category,
            )
            db.session.add(product)
            db.session.commit()
            return redirect(url_for("dashboard_products"))


@app.route("/add_category", methods=["GET", "POST"])
def add_category():
    if request.method == "POST":
        category = request.form["category"]
        name = request.form["name"]
        quantity = request.form["quantity"]
        description = request.form["description"]
        price = request.form["price"]
        product = Products(name, quantity, description, price, category)
        db.session.add(product)
        db.session.commit()
        return redirect(url_for("dashboard_products"))
    return render_template("add_category.html")


##### Admin's Dashboard ends here #####

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        app.run()
