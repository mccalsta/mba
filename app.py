from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
import sqlite3
import os
from datetime import datetime
from weasyprint import HTML
from werkzeug.security import generate_password_hash, check_password_hash
import io

app = Flask(__name__)
app.secret_key = "miracle_secret_key"

DB = "database.db"


# ---------------- DATABASE ----------------

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()

    conn.execute("""
    CREATE TABLE IF NOT EXISTS players (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT,
        dob TEXT,
        age INTEGER,
        gender TEXT,
        school TEXT,
        grade TEXT,
        address TEXT,
        village TEXT,
        position TEXT,
        shirt_size TEXT,
        parent_name TEXT,
        relationship TEXT,
        phone1 TEXT,
        phone2 TEXT,
        email TEXT,
        medical TEXT,
        injuries TEXT,
        allergies TEXT,
        skill TEXT,
        goals TEXT,
        amount INTEGER,
        payment_method TEXT,
        reference TEXT,
        payment_plan TEXT,
        payment_status TEXT DEFAULT 'Pending',
        created_at TEXT
    )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        created_at TEXT
    )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        category TEXT,
        base_price INTEGER,
        image TEXT,
        created_at TEXT
    )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS product_variants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        variant TEXT,
        stock INTEGER DEFAULT 0,
        price INTEGER,
        FOREIGN KEY(product_id) REFERENCES products(id)
    )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        total INTEGER,
        payment_method TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS sale_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sale_id INTEGER,
        product_name TEXT,
        variant TEXT,
        quantity INTEGER,
        price INTEGER,
        subtotal INTEGER,
        FOREIGN KEY(sale_id) REFERENCES sales(id)
    )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS receipts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        player_id INTEGER,
        player_name TEXT,
        amount INTEGER,
        payment_method TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)
    # TEAM REGISTRATIONS
conn.execute("""
CREATE TABLE IF NOT EXISTS team_registrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_name TEXT,
    coach_name TEXT,
    phone TEXT,
    email TEXT,
    category TEXT,
    age_group TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
)
""")

# HOLIDAY CAMP REGISTRATIONS
conn.execute("""
CREATE TABLE IF NOT EXISTS camp_registrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT,
    dob TEXT,
    gender TEXT,
    school TEXT,
    parent_name TEXT,
    phone TEXT,
    email TEXT,
    shirt_size TEXT,
    medical TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
)
""")

    conn.commit()
    conn.close()


with app.app_context():
    init_db()


# ---------------- HELPERS ----------------

def calculate_age(dob_string):
    if not dob_string:
        return None
    try:
        dob = datetime.strptime(dob_string, "%Y-%m-%d")
        today = datetime.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        return age
    except:
        return None


def get_cart():
    return session.get("cart", [])


def save_cart(cart):
    session["cart"] = cart
    session.modified = True


def cart_count():
    return sum(item["quantity"] for item in get_cart())


def cart_total():
    return sum(item["subtotal"] for item in get_cart())


@app.context_processor
def inject_cart_data():
    return {
        "cart_count": cart_count()
    }


# ---------------- PUBLIC PAGES ----------------

@app.route("/")
def home():
    return render_template("home.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/programs")
def programs():
    return render_template("programs.html")


@app.route("/teams")
def teams():
    return render_template("teams.html")


@app.route("/impact")
def impact():
    return render_template("impact.html")


@app.route("/gallery")
def gallery():
    return render_template("gallery.html")


@app.route("/join")
def join():
    return render_template("join.html")


# ---------------- REGISTER ----------------

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        dob = request.form.get("dob")
        age = calculate_age(dob)

        amount = request.form.get("amount")
        amount = int(amount) if amount and amount.strip() else 0

        conn = get_db()
        conn.execute("""
        INSERT INTO players (
            full_name,dob,age,gender,school,grade,address,village,position,shirt_size,
            parent_name,relationship,phone1,phone2,email,
            medical,injuries,allergies,
            skill,goals,
            amount,payment_method,reference,payment_plan,payment_status,created_at
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            request.form.get("full_name"),
            dob,
            age,
            request.form.get("gender"),
            request.form.get("school"),
            request.form.get("grade"),
            request.form.get("address"),
            request.form.get("village"),
            request.form.get("position"),
            request.form.get("shirt_size"),
            request.form.get("parent_name"),
            request.form.get("relationship"),
            request.form.get("phone1"),
            request.form.get("phone2"),
            request.form.get("email"),
            request.form.get("medical"),
            request.form.get("injuries"),
            request.form.get("allergies"),
            request.form.get("skill"),
            request.form.get("goals"),
            amount,
            request.form.get("payment_method"),
            request.form.get("reference"),
            request.form.get("payment_plan"),
            "Pending",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        conn.commit()
        conn.close()

        flash("Registration saved successfully!")
        return redirect("/register")

    return render_template("register.html")


# ---------------- ADMIN AUTH ----------------

@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        conn = get_db()
        admin = conn.execute(
            "SELECT * FROM admins WHERE username=?",
            (username,)
        ).fetchone()
        conn.close()

        if admin and check_password_hash(admin["password"], password):
            session["admin"] = username
            return redirect("/dashboard")
        else:
            flash("Invalid credentials")

    return render_template("admin_login.html")


@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect("/admin")


# ---------------- DASHBOARD ----------------

@app.route("/dashboard")
def dashboard():
    if "admin" not in session:
        return redirect("/admin")

    conn = get_db()
    players = conn.execute("SELECT * FROM players ORDER BY created_at DESC").fetchall()
    total_players = conn.execute("SELECT COUNT(*) FROM players").fetchone()[0]
    paid_players = conn.execute("SELECT COUNT(*) FROM players WHERE payment_status='Paid'").fetchone()[0]
    unpaid_players = conn.execute("SELECT COUNT(*) FROM players WHERE payment_status='Pending'").fetchone()[0]
    conn.close()

    return render_template(
        "admin_dashboard.html",
        players=players,
        total_players=total_players,
        paid_players=paid_players,
        unpaid_players=unpaid_players
    )


@app.route("/mark_paid/<int:player_id>")
def mark_paid(player_id):
    if "admin" not in session:
        return redirect("/admin")

    conn = get_db()
    conn.execute("UPDATE players SET payment_status='Paid' WHERE id=?", (player_id,))
    conn.commit()
    conn.close()

    return redirect("/dashboard")


@app.route("/create_admin")
def create_admin():
    conn = get_db()

    admins = [
        ("henry", generate_password_hash("1234")),
        ("coach_mike", generate_password_hash("basketball")),
        ("manager_sarah", generate_password_hash("academy2026")),
        ("finance_john", generate_password_hash("payments"))
    ]

    for a in admins:
        try:
            conn.execute(
                "INSERT INTO admins (username,password,created_at) VALUES (?,?,datetime('now'))",
                a
            )
        except:
            pass

    conn.commit()
    conn.close()

    return "Admins created"


# ---------------- PLAYER RECEIPT ----------------

@app.route("/receipt/<int:player_id>")
def generate_receipt(player_id):
    conn = get_db()

    player = conn.execute("""
        SELECT id, full_name, parent_name, phone1, amount
        FROM players
        WHERE id = ?
    """, (player_id,)).fetchone()

    conn.close()

    if not player:
        return "Player not found", 404

    formatted_amount = f"{int(player['amount']):,}"

    html = render_template(
        "receipt_ui.html",
        player=player,
        receipt_no=f"MBA-{player['id']:05d}",
        amount=formatted_amount,
        date=datetime.now().strftime("%d %b %Y")
    )

    pdf = HTML(string=html, base_url=request.base_url).write_pdf()

    return send_file(
        io.BytesIO(pdf),
        download_name=f"receipt_{player_id}.pdf",
        mimetype="application/pdf"
    )


# ---------------- ADMIN PRODUCT PAGES ----------------

@app.route("/admin/products/add", methods=["GET", "POST"])
def add_product():
    if "admin" not in session:
        return redirect("/admin")

    if request.method == "POST":
        name = request.form.get("name")
        category = request.form.get("category")
        base_price = request.form.get("base_price")
        image = request.form.get("image")

        conn = get_db()

        cursor = conn.execute("""
            INSERT INTO products (name, category, base_price, image, created_at)
            VALUES (?,?,?,?,datetime('now'))
        """, (name, category, base_price, image))

        product_id = cursor.lastrowid

        variants = request.form.getlist("variant[]")
        stocks = request.form.getlist("stock[]")
        prices = request.form.getlist("price[]")

        for v, s, p in zip(variants, stocks, prices):
            if v.strip():
                conn.execute("""
                    INSERT INTO product_variants (product_id, variant, stock, price)
                    VALUES (?,?,?,?)
                """, (product_id, v, int(s or 0), int(p or base_price or 0)))

        conn.commit()
        conn.close()

        flash("Product added successfully!")
        return redirect("/admin/products/add")

    return render_template("add_product.html")


@app.route("/admin/orders")
def admin_orders():
    if "admin" not in session:
        return redirect("/admin")

    conn = get_db()
    orders = conn.execute("SELECT * FROM sales ORDER BY created_at DESC").fetchall()
    conn.close()

    return render_template("admin_orders.html", orders=orders)


@app.route("/admin/receipts")
def admin_receipts():
    if "admin" not in session:
        return redirect("/admin")

    conn = get_db()
    receipts = conn.execute("SELECT * FROM receipts ORDER BY created_at DESC").fetchall()
    conn.close()

    return render_template("admin_receipts.html", receipts=receipts)


@app.route("/admin/players")
def admin_players():
    if "admin" not in session:
        return redirect("/admin")

    conn = get_db()
    players = conn.execute("SELECT * FROM players ORDER BY created_at DESC").fetchall()
    conn.close()

    return render_template("admin_players.html", players=players)


# ---------------- PUBLIC SHOP ----------------

@app.route("/shop")
def shop():
    conn = get_db()
    products = conn.execute("""
        SELECT 
            v.id AS variant_id,
            p.id AS product_id,
            p.name,
            p.category,
            p.image,
            v.variant,
            v.price,
            v.stock
        FROM products p
        JOIN product_variants v ON v.product_id = p.id
        WHERE v.stock > 0
        ORDER BY p.name, v.variant
    """).fetchall()
    conn.close()

    return render_template("shop.html", products=products)


@app.route("/cart/add", methods=["POST"])
def add_to_cart():
    variant_id = request.form.get("variant_id")
    quantity = int(request.form.get("quantity", 1))

    conn = get_db()
    item = conn.execute("""
        SELECT 
            v.id AS variant_id,
            p.name,
            p.image,
            v.variant,
            v.price,
            v.stock
        FROM product_variants v
        JOIN products p ON p.id = v.product_id
        WHERE v.id = ?
    """, (variant_id,)).fetchone()
    conn.close()

    if not item:
        flash("Product not found.")
        return redirect("/shop")

    if quantity < 1:
        quantity = 1

    if quantity > item["stock"]:
        flash("Requested quantity exceeds available stock.")
        return redirect("/shop")

    cart = get_cart()
    found = False

    for cart_item in cart:
        if cart_item["variant_id"] == int(item["variant_id"]):
            new_qty = cart_item["quantity"] + quantity
            if new_qty > item["stock"]:
                flash("Cannot add more than available stock.")
                return redirect("/shop")
            cart_item["quantity"] = new_qty
            cart_item["subtotal"] = new_qty * cart_item["price"]
            found = True
            break

    if not found:
        cart.append({
            "variant_id": int(item["variant_id"]),
            "name": item["name"],
            "image": item["image"],
            "variant": item["variant"],
            "price": int(item["price"]),
            "quantity": quantity,
            "subtotal": int(item["price"]) * quantity
        })

    save_cart(cart)
    flash("Item added to cart.")
    return redirect("/shop")


@app.route("/cart")
def view_cart():
    cart = get_cart()
    total = cart_total()
    return render_template("cart.html", cart=cart, total=total)


@app.route("/cart/update", methods=["POST"])
def update_cart():
    cart = get_cart()
    conn = get_db()

    for item in cart:
        qty_key = f"qty_{item['variant_id']}"
        new_qty = request.form.get(qty_key)

        if new_qty is not None:
            try:
                new_qty = int(new_qty)
            except:
                new_qty = item["quantity"]

            if new_qty < 1:
                new_qty = 1

            db_item = conn.execute(
                "SELECT stock FROM product_variants WHERE id = ?",
                (item["variant_id"],)
            ).fetchone()

            if db_item and new_qty > db_item["stock"]:
                new_qty = db_item["stock"]
                flash(f"Quantity for {item['name']} was adjusted to available stock.")

            item["quantity"] = new_qty
            item["subtotal"] = item["quantity"] * item["price"]

    conn.close()
    save_cart(cart)
    flash("Cart updated.")
    return redirect("/cart")


@app.route("/cart/remove/<int:variant_id>")
def remove_from_cart(variant_id):
    cart = get_cart()
    cart = [item for item in cart if item["variant_id"] != variant_id]
    save_cart(cart)
    flash("Item removed from cart.")
    return redirect("/cart")


@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    cart = get_cart()

    if not cart:
        flash("Your cart is empty.")
        return redirect("/shop")

    if request.method == "POST":
        payment_method = request.form.get("payment_method")

        conn = get_db()

        for item in cart:
            db_item = conn.execute("""
                SELECT stock FROM product_variants WHERE id = ?
            """, (item["variant_id"],)).fetchone()

            if not db_item or item["quantity"] > db_item["stock"]:
                conn.close()
                flash(f"Not enough stock for {item['name']} ({item['variant']}).")
                return redirect("/cart")

        total = cart_total()

        cursor = conn.execute("""
            INSERT INTO sales (total, payment_method, created_at)
            VALUES (?, ?, datetime('now'))
        """, (total, payment_method))

        sale_id = cursor.lastrowid

        for item in cart:
            conn.execute("""
                INSERT INTO sale_items (sale_id, product_name, variant, quantity, price, subtotal)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                sale_id,
                item["name"],
                item["variant"],
                item["quantity"],
                item["price"],
                item["subtotal"]
            ))

            conn.execute("""
                UPDATE product_variants
                SET stock = stock - ?
                WHERE id = ?
            """, (item["quantity"], item["variant_id"]))

        conn.commit()
        conn.close()

        session["cart"] = []
        return redirect(f"/shop/receipt/{sale_id}")

    total = cart_total()
    return render_template("checkout.html", cart=cart, total=total)


@app.route("/shop/receipt/<int:sale_id>")
def shop_receipt(sale_id):
    conn = get_db()

    sale = conn.execute("SELECT * FROM sales WHERE id=?", (sale_id,)).fetchone()
    items = conn.execute("SELECT * FROM sale_items WHERE sale_id=?", (sale_id,)).fetchall()

    conn.close()

    html = render_template(
        "shop_receipt.html",
        sale=sale,
        items=items
    )

    pdf = HTML(string=html, base_url=request.base_url).write_pdf()

    return send_file(
        io.BytesIO(pdf),
        download_name=f"shop_receipt_{sale_id}.pdf",
        mimetype="application/pdf"
    )


if __name__ == "__main__":
    app.run(debug=True)

# ---------------- TEAM REGISTRATION ----------------

@app.route("/register-team", methods=["GET", "POST"])
def register_team():
    if request.method == "POST":
        conn = get_db()
        conn.execute("""
            INSERT INTO team_registrations
            (team_name, coach_name, phone, email, category, age_group)
            VALUES (?,?,?,?,?,?)
        """, (
            request.form.get("team_name"),
            request.form.get("coach_name"),
            request.form.get("phone"),
            request.form.get("email"),
            request.form.get("category"),
            request.form.get("age_group")
        ))
        conn.commit()
        conn.close()

        flash("Team registration submitted successfully!")
        return redirect("/register-team")

    return render_template("register_team.html")

# ---------------- HOLIDAY CAMP REGISTRATION ----------------

@app.route("/register-camp", methods=["GET", "POST"])
def register_camp():
    if request.method == "POST":
        conn = get_db()
        conn.execute("""
            INSERT INTO camp_registrations
            (full_name, dob, gender, school, parent_name, phone, email, shirt_size, medical)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (
            request.form.get("full_name"),
            request.form.get("dob"),
            request.form.get("gender"),
            request.form.get("school"),
            request.form.get("parent_name"),
            request.form.get("phone"),
            request.form.get("email"),
            request.form.get("shirt_size"),
            request.form.get("medical")
        ))
        conn.commit()
        conn.close()

        flash("Holiday camp registration submitted successfully!")
        return redirect("/register-camp")

    return render_template("register_camp.html")

@app.route("/admin/teams")
def admin_teams():
    if "admin" not in session:
        return redirect("/admin")

    conn = get_db()
    teams = conn.execute("""
        SELECT * FROM team_registrations
        ORDER BY created_at DESC
    """).fetchall()
    conn.close()

    return render_template("admin_teams.html", teams=teams)

@app.route("/admin/teams")
def admin_teams():
    if "admin" not in session:
        return redirect("/admin")

    conn = get_db()
    teams = conn.execute("""
        SELECT * FROM team_registrations
        ORDER BY created_at DESC
    """).fetchall()
    conn.close()

    return render_template("admin_teams.html", teams=teams)

