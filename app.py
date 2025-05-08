from flask import Flask, render_template, request, redirect, url_for, session

import sqlite3
from pathlib import Path

app= Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Replace with something secure

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/produkti")
def products():
    category_id = request.args.get("category", "all")
    conn = get_db_connection()

    if category_id != "all":
        products = conn.execute("""
            SELECT products.*, categories.name AS category_name
            FROM products
            JOIN categories ON products.category_id = categories.id
            WHERE category_id = ?
        """, (category_id,)).fetchall()
    else:
        products = conn.execute("""
            SELECT products.*, categories.name AS category_name
            FROM products
            JOIN categories ON products.category_id = categories.id
        """).fetchall()

    categories = conn.execute("SELECT * FROM categories").fetchall()
    conn.close()
    
    return render_template("products.html", products=products, categories=categories, selected_category=category_id)

@app.route("/par-mums")
def about():
    return render_template("about.html")

@app.route("/produkti/<int:product_id>")
def products_show(product_id):
    conn = get_db_connection()
    
    # Main product + description data
    product = conn.execute("""
        SELECT 
            p.*, 
            d.pieejamiba, 
            d.svars
        FROM products p
        LEFT JOIN product_description d ON p.id = d.product_id
        WHERE p.id = ?
    """, (product_id,)).fetchone()

    if product is None:
        conn.close()
        return "<h2>Produkts nav atrasts</h2>", 404

    # Get additional images from product_images table
    images = conn.execute("""
        SELECT image FROM product_images
        WHERE product_id = ?
    """, (product_id,)).fetchall()

    conn.close()

    return render_template("product_detail.html", product=product, images=images)

@app.route("/add_to_cart/<int:product_id>", methods=["POST"])
def add_to_cart(product_id):
    quantity = int(request.form.get("quantity", 1))
    cart = session.get("cart", {})

    if str(product_id) in cart:
        cart[str(product_id)] += quantity
    else:
        cart[str(product_id)] = quantity

    session["cart"] = cart
    return redirect(url_for("view_cart"))

@app.route("/cart")
def view_cart():
    cart = session.get("cart", {})
    conn = get_db_connection()

    cart_items = []
    total = 0

    for product_id, quantity in cart.items():
        product = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
        if product:
            item_total = product["cena"] * quantity
            total += item_total
            cart_items.append({
                "id": product["id"],
                "name": product["name"],
                "cena": product["cena"],
                "quantity": quantity,
                "total": item_total
            })

    conn.close()
    return render_template("cart.html", cart_items=cart_items, total=total)

@app.route("/update_cart", methods=["POST"])
def update_cart():
    cart = session.get("cart", {})

    for key, value in request.form.items():
        if key.startswith("quantity_"):
            product_id = key.split("_")[1]
            new_quantity = int(value)
            if new_quantity <= 0:
                cart.pop(product_id, None)
            else:
                cart[product_id] = new_quantity

    session["cart"] = cart
    return redirect(url_for("view_cart"))

def get_db_connection():
    """
    Izveido un atgriež savienojumu ar SQLite datubāzi.
    """

    db = Path(__file__).parent / "project.db"

    conn = sqlite3.connect(db)

    conn.row_factory = sqlite3.Row

    return conn


if __name__== "__main__":
    app.run(debug=True)


