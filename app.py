from flask import Flask, render_template, request, redirect, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "secret123"


# ======================
# สร้าง database อัตโนมัติ
# ======================

def init_db():

    conn = sqlite3.connect("orders.db")
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        total INTEGER,
        status TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER,
        drink TEXT,
        sweetness TEXT,
        table_no TEXT,
        price INTEGER,
        quantity INTEGER
    )
    """)

    conn.commit()
    conn.close()

init_db()


# ======================
# หน้าเว็บหลัก
# ======================

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/reason")
def reason():
    return render_template("reason.html")


@app.route("/code")
def code():
    return render_template("code.html")


@app.route("/menu")
def menu():
    return render_template("menu.html")


@app.route("/team")
def team():
    return render_template("team.html")


# ======================
# เพิ่มสินค้าเข้าตะกร้า
# ======================

@app.route("/add_to_cart", methods=["POST"])
def add_to_cart():

    drink = request.form["drink"]
    sweetness = request.form["sweetness"]
    table = request.form["table"]
    price = int(request.form["price"])

    if "cart" not in session:
        session["cart"] = []

    session["cart"].append({
        "drink": drink,
        "sweetness": sweetness,
        "table": table,
        "price": price
    })

    session.modified = True

    return redirect("/cart")


# ======================
# หน้า cart
# ======================

@app.route("/cart")
def cart():

    cart = session.get("cart", [])

    grouped = {}

    for item in cart:

        key = (item["drink"], item["sweetness"], item["price"], item["table"])

        if key not in grouped:
            grouped[key] = {
                "drink": item["drink"],
                "sweetness": item["sweetness"],
                "table": item["table"],
                "price": item["price"],
                "quantity": 1
            }
        else:
            grouped[key]["quantity"] += 1

    items = list(grouped.values())

    total = sum(item["price"] * item["quantity"] for item in items)

    return render_template("cart.html", items=items, total=total)


# ======================
# ลบรายการ
# ======================

@app.route("/remove_group", methods=["POST"])
def remove_group():

    drink = request.form["drink"]
    sweetness = request.form["sweetness"]
    table = request.form["table"]

    cart = session.get("cart", [])

    cart = [item for item in cart
            if not (item["drink"] == drink and
                    item["sweetness"] == sweetness and
                    item["table"] == table)]

    session["cart"] = cart
    session.modified = True

    return redirect("/cart")


# ======================
# ยืนยันคำสั่งซื้อ
# ======================

@app.route("/confirm", methods=["POST"])
def confirm():

    cart = session.get("cart", [])

    if not cart:
        return redirect("/menu")

    conn = sqlite3.connect("orders.db")
    c = conn.cursor()

    total = sum(item["price"] for item in cart)

    c.execute(
        "INSERT INTO orders (total,status) VALUES (?,?)",
        (total, "waiting")
    )

    order_id = c.lastrowid

    for item in cart:

        c.execute("""
        INSERT INTO order_items
        (order_id, drink, sweetness, table_no, price, quantity)
        VALUES (?, ?, ?, ?, ?, ?)
        """,(
        order_id,
        item["drink"],
        item["sweetness"],
        item["table"],
        item["price"],
        1
        ))

    conn.commit()
    conn.close()

    session["cart"] = []

    return render_template(
        "success.html",
        order_id=order_id,
        total=total
    )


# ======================
# Admin Panel
# ======================

@app.route("/admin")
def admin():

    conn = sqlite3.connect("orders.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("SELECT * FROM orders ORDER BY id DESC")

    orders = c.fetchall()

    conn.close()

    return render_template("admin.html", orders=orders)


# ======================
# รายละเอียด order
# ======================

@app.route("/order/<int:order_id>")
def order_detail(order_id):

    conn = sqlite3.connect("orders.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("SELECT * FROM order_items WHERE order_id=?", (order_id,))

    items = c.fetchall()

    conn.close()

    return render_template(
        "order_detail.html",
        items=items,
        order_id=order_id
    )


# ======================
# กราฟยอดขาย
# ======================

@app.route("/sales")
def sales():

    conn = sqlite3.connect("orders.db")
    c = conn.cursor()

    c.execute("""
    SELECT drink, SUM(quantity)
    FROM order_items
    GROUP BY drink
    """)

    data = c.fetchall()

    conn.close()

    drinks = [row[0] for row in data]
    quantities = [row[1] for row in data]

    return render_template(
        "sales.html",
        drinks=drinks,
        quantities=quantities
    )


# ======================
# Reset ยอดขาย
# ======================

@app.route("/reset_sales", methods=["GET","POST"])
def reset_sales():

    conn = sqlite3.connect("orders.db")
    c = conn.cursor()

    c.execute("DELETE FROM orders")
    c.execute("DELETE FROM order_items")

    conn.commit()
    conn.close()

    return redirect("/sales")


# ======================
# Queue
# ======================

@app.route("/queue")
def queue():

    conn = sqlite3.connect("orders.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("SELECT * FROM orders WHERE status='waiting'")
    waiting = c.fetchall()

    c.execute("SELECT * FROM orders WHERE status='ready'")
    ready = c.fetchall()

    conn.close()

    return render_template(
        "queue.html",
        waiting=waiting,
        ready=ready
    )


# ======================

if __name__ == "__main__":
    port = int(os.environ.get("PORT",5000))
    app.run(host="0.0.0.0",port=port)