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

    # PLAYERS
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

    # ADMINS
    conn.execute("""
    CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        created_at TEXT
    )
    """)

    # PRODUCTS
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

    # PRODUCT VARIANTS
    conn.execute("""
    CREATE TABLE IF NOT EXISTS product_variants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        variant TEXT,
        stock INTEGER,
        price INTEGER
    )
    """)

    # SALES
    conn.execute("""
    CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        total INTEGER,
        payment_method TEXT,
        created_at TEXT
    )
    """)

    # SALE ITEMS
    conn.execute("""
    CREATE TABLE IF NOT EXISTS sale_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sale_id INTEGER,
        product_name TEXT,
        variant TEXT,
        quantity INTEGER,
        price INTEGER,
        subtotal INTEGER
    )
    """)

    # RECEIPTS
    conn.execute("""
    CREATE TABLE IF NOT EXISTS receipts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        player_id INTEGER,
        player_name TEXT,
        amount INTEGER,
        payment_method TEXT,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()


with app.app_context():
    init_db()


# ---------------- HOME ----------------

@app.route("/")
def home():
    return render_template("home.html")


# ---------------- AGE CALCULATOR ----------------

def calculate_age(dob_string):

    if not dob_string:
        return None

    try:
        dob = datetime.strptime(dob_string, "%Y-%m-%d")
        today = datetime.today()

        age = today.year - dob.year - (
            (today.month, today.day) < (dob.month, dob.day)
        )

        return age

    except:
        return None


# ---------------- PLAYER REGISTRATION ----------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        dob = request.form.get("dob")
        age = calculate_age(dob)

        amount = request.form.get("amount")
        amount = int(amount) if amount else 0

        conn = get_db()

        conn.execute("""
        INSERT INTO players (
            full_name,dob,age,gender,school,grade,address,village,position,shirt_size,
            parent_name,relationship,phone1,phone2,email,
            medical,injuries,allergies,
            skill,goals,
            amount,payment_method,reference,payment_plan,payment_status,created_at
        )
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
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


# ---------------- ADMIN LOGIN ----------------

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


# ---------------- ADMIN LOGOUT ----------------

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

    players = conn.execute(
        "SELECT * FROM players ORDER BY created_at DESC"
    ).fetchall()

    total_players = conn.execute(
        "SELECT COUNT(*) FROM players"
    ).fetchone()[0]

    paid_players = conn.execute(
        "SELECT COUNT(*) FROM players WHERE payment_status='Paid'"
    ).fetchone()[0]

    unpaid_players = conn.execute(
        "SELECT COUNT(*) FROM players WHERE payment_status='Pending'"
    ).fetchone()[0]

    conn.close()

    return render_template(
        "admin_dashboard.html",
        players=players,
        total_players=total_players,
        paid_players=paid_players,
        unpaid_players=unpaid_players
    )


# ---------------- MARK PAYMENT ----------------

@app.route("/mark_paid/<int:player_id>")
def mark_paid(player_id):

    if "admin" not in session:
        return redirect("/admin")

    conn = get_db()

    conn.execute(
        "UPDATE players SET payment_status='Paid' WHERE id=?",
        (player_id,)
    )

    conn.commit()
    conn.close()

    return redirect("/dashboard")


# ---------------- SHOP (PUBLIC) ----------------

@app.route("/shop", methods=["GET", "POST"])
def shop():

    conn = get_db()

    if request.method == "POST":

        variants = request.form.getlist("variant")
        qtys = request.form.getlist("qty")
        prices = request.form.getlist("price")
        names = request.form.getlist("name")

        total = 0
        items = []

        for n, v, q, p in zip(names, variants, qtys, prices):

            q = int(q or 0)
            p = int(p or 0)

            if q > 0:

                subtotal = q * p
                total += subtotal

                items.append((n, v, q, p, subtotal))

        cursor = conn.execute(
            "INSERT INTO sales (total,payment_method,created_at) VALUES (?,?,datetime('now'))",
            (total, request.form.get("payment_method"))
        )

        sale_id = cursor.lastrowid

        for i in items:

            conn.execute("""
            INSERT INTO sale_items
            (sale_id,product_name,variant,quantity,price,subtotal)
            VALUES (?,?,?,?,?,?)
            """, (sale_id, *i))

        conn.commit()

        return redirect(f"/shop/receipt/{sale_id}")

    products = conn.execute("""
    SELECT p.name, v.variant, v.price, v.stock
    FROM products p
    JOIN product_variants v
    ON v.product_id=p.id
    """).fetchall()

    conn.close()

    return render_template("shop_pos.html", products=products)


# ---------------- SHOP RECEIPT ----------------

@app.route("/shop/receipt/<int:sale_id>")
def shop_receipt(sale_id):

    conn = get_db()

    sale = conn.execute(
        "SELECT * FROM sales WHERE id=?",
        (sale_id,)
    ).fetchone()

    items = conn.execute(
        "SELECT * FROM sale_items WHERE sale_id=?",
        (sale_id,)
    ).fetchall()

    conn.close()

    html = render_template(
        "shop_receipt.html",
        sale=sale,
        items=items
    )

    pdf = HTML(string=html).write_pdf()

    return send_file(
        io.BytesIO(pdf),
        download_name=f"shop_receipt_{sale_id}.pdf",
        mimetype="application/pdf"
    )


# ---------------- STATIC PAGES ----------------

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


# ---------------- RUN APP ----------------

if __name__ == "__main__":
    app.run(debug=True)
