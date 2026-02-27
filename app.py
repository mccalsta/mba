from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
import os
from datetime import datetime
from weasyprint import HTML
from werkzeug.security import generate_password_hash, check_password_hash
from flask import send_file
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A5, landscape
import io
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from datetime import datetime
from reportlab.lib.enums import TA_RIGHT, TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor, white, black
PRIMARY = HexColor("#0f172a")
ACCENT = HexColor("#f97316")
LIGHT = HexColor("#f1f5f9")




app = Flask(__name__)
app.secret_key = "miracle_secret_key"

DB = "database.db"


# ---------------- DB ----------------
def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()

    # PLAYERS TABLE
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

    # ADMINS TABLE  ← ADD HERE (NOT AFTER CLOSE)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at TEXT
    )
    """)


    # PRODUCTS (shop items)
conn.execute("""
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT,
    price INTEGER NOT NULL,
    stock INTEGER DEFAULT 0,
    image TEXT,
    created_at TEXT
)
""")

# ORDERS (one receipt)
conn.execute("""
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_name TEXT,
    phone TEXT,
    total INTEGER,
    payment_method TEXT,
    status TEXT DEFAULT 'Paid',
    created_at TEXT
)
""")

# ORDER ITEMS (items inside receipt)
conn.execute("""
CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER,
    product_id INTEGER,
    quantity INTEGER,
    price INTEGER,
    FOREIGN KEY(order_id) REFERENCES orders(id),
    FOREIGN KEY(product_id) REFERENCES products(id)
)
""")



    conn.commit()
    conn.close()
init_db()
# ------------------------------------


@app.route("/")
def home():
    return render_template("home.html")

# -------- AGE CALCULATOR (TRUTH SOURCE) --------
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

# ---------------- REGISTER ----------------
# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":

        dob = request.form.get("dob")
        age = calculate_age(dob)   # ← REAL AGE FROM DOB

        amount = request.form.get("amount")
        if not amount or amount.strip() == "":
            amount = 0
        else:
            amount = int(amount)

        data = (
            request.form.get("full_name"),
            dob,
            age,  # ← STORED AGE (NOT USER INPUT)
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
        )

        conn = get_db()
        conn.execute("""
        INSERT INTO players (
            full_name,dob,age,gender,school,grade,address,village,position,shirt_size,
            parent_name,relationship,phone1,phone2,email,
            medical,injuries,allergies,
            skill,goals,
            amount,payment_method,reference,payment_plan,payment_status,created_at
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, data)

        conn.commit()
        conn.close()

        flash("Registration saved successfully!")
        return redirect("/register")

    return render_template("register.html")
# ---------------- ADMIN LOGIN ----------------



# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if "admin" not in session:
        return redirect("/admin")
    conn = get_db()
    players = conn.execute("SELECT * FROM players ORDER BY created_at DESC").fetchall()

    # stats
    total_players = conn.execute("SELECT COUNT(*) FROM players").fetchone()[0]
    paid_players = conn.execute("SELECT COUNT(*) FROM players WHERE payment_status='Paid'").fetchone()[0]
    unpaid_players = conn.execute("SELECT COUNT(*) FROM players WHERE payment_status='Pending'").fetchone()[0]

    weekly_income = conn.execute(
        "SELECT COALESCE(SUM(amount),0) FROM players WHERE payment_plan='Weekly' AND payment_status='Paid'"
    ).fetchone()[0]

    monthly_income = conn.execute(
        "SELECT COALESCE(SUM(amount),0) FROM players WHERE payment_plan='Monthly' AND payment_status='Paid'"
    ).fetchone()[0]

    conn.close()

    return render_template(
        "admin_dashboard.html",
        players=players,
        total_players=total_players,
        paid_players=paid_players,
        unpaid_players=unpaid_players,
        weekly_income=weekly_income,
        monthly_income=monthly_income
    )

if __name__ == "__main__":
    app.run(debug=True)
#mark-paid
@app.route("/mark_paid/<int:player_id>")
def mark_paid(player_id):
    conn = get_db()
    conn.execute(
        "UPDATE players SET payment_status='Paid' WHERE id=?",
        (player_id,)
    )
    conn.commit()
    conn.close()

    return redirect("/dashboard")

#add-admin
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
                "INSERT INTO admins (username,password,created_at) VALUES (?,?,datetime('now'))", a
            )
        except:
            pass

    conn.commit()
    conn.close()

    return "Admins created"

#--------admin login---------
@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        conn = get_db()
        admin = conn.execute(
            "SELECT * FROM admins WHERE username = ?",
            (username,)
        ).fetchone()
        conn.close()

        if admin and check_password_hash(admin["password"], password):
            session["admin"] = username
            return redirect("/dashboard")
        else:
            flash("Invalid credentials")

    return render_template("admin_login.html")

#------Admin log out-------
@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect("/admin")

# ================= RECEIPT (FINAL STABLE UI VERSION) =================
def build_receipt_pdf(buffer, player):

    amount = int(player["amount"] or 0)
    parent = player["parent_name"] or "N/A"
    phone = player["phone1"] or "N/A"
    receipt_no = f"MBA-{int(player['id']):05d}"

    width, height = landscape(A5)
    c = canvas.Canvas(buffer, pagesize=(width, height))

    # UI COLORS
    primary = HexColor("#2F69BF")
    accent = HexColor("#22C55E")
    light = HexColor("#F3F4F6")
    border = HexColor("#E5E7EB")
    text = HexColor("#111827")
    subtext = HexColor("#6B7280")

    # ================= HEADER =================
    c.setFillColor(primary)
    c.rect(0, height-60, width, 60, fill=1, stroke=0)

    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(30, height-32, "MIRACLE BASKETBALL ACADEMY")

    c.setFont("Helvetica", 10)
    c.drawString(30, height-48, "Official Payment Receipt")

    # receipt badge
    c.setFillColor(white)
    c.roundRect(width-210, height-45, 160, 26, 8, fill=1, stroke=0)

    c.setFillColor(primary)
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(width-130, height-30, f"Receipt #{receipt_no}")

    # logo
    logo_path = os.path.join("static", "logo.png")
    if os.path.exists(logo_path):
        c.drawImage(logo_path, width-60, height-58, 40, 40, mask='auto')

    # ================= CARDS =================
    card_y = height - 145
    card_h = 78
    card_w = width/2 - 50

    # left card
    c.setFillColor(light)
    c.roundRect(30, card_y, card_w, card_h, 10, fill=1, stroke=0)

    c.setFillColor(subtext)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(45, card_y+58, "PLAYER DETAILS")

    c.setFillColor(text)
    c.setFont("Helvetica", 11)
    c.drawString(45, card_y+38, f"Name: {player['full_name']}")
    c.drawString(45, card_y+23, f"Parent: {parent}")
    c.drawString(45, card_y+8, f"Phone: {phone}")

    # right card
    right_x = width/2 + 10
    c.setFillColor(light)
    c.roundRect(right_x, card_y, card_w, card_h, 10, fill=1, stroke=0)

    c.setFillColor(subtext)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(right_x+15, card_y+58, "PAYMENT INFO")

    c.setFillColor(text)
    c.setFont("Helvetica", 11)
    c.drawString(right_x+15, card_y+38, "Description: Training Fees")
    c.drawString(right_x+15, card_y+23, f"Date: {datetime.now().strftime('%d %b %Y')}")

    c.setFillColor(accent)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(right_x+15, card_y+6, f"UGX {amount:,}")

    # ================= PAYMENT SUMMARY =================
    table_y = card_y - 40

    c.setFillColor(text)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(30, table_y+25, "Training Payment Summary")

    # header line
    c.setStrokeColor(border)
    c.line(30, table_y+20, width-30, table_y+20)

    # row
    c.setFont("Helvetica", 11)
    c.setFillColor(text)
    c.drawString(35, table_y-5, f"{player['payment_plan']} Training Fee")
    c.drawRightString(width-40, table_y-5, f"UGX {amount:,}")

    # divider
    c.setStrokeColor(border)
    c.line(30, table_y-15, width-30, table_y-15)

    # total
    c.setFont("Helvetica-Bold", 13)
    c.drawString(width-220, table_y-35, "Total Amount")
    c.drawRightString(width-40, table_y-35, f"UGX {amount:,}")

    # ================= FOOTER =================
    c.setStrokeColor(border)
    c.line(40, 60, 220, 60)

    c.setFont("Helvetica", 9)
    c.setFillColor(subtext)
    c.drawString(40, 45, "Authorized Signature")
    c.drawRightString(width-40, 45, "Thank you for supporting youth development!")

    c.save()


# ================= ROUTE =================
@app.route("/receipt/<int:player_id>")
def generate_receipt(player_id):

    conn = get_db()

    player = conn.execute("""
        SELECT
            id,
            full_name,
            parent_name,
            phone1,
            amount
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
