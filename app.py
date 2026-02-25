from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
import os
from datetime import datetime
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
from reportlab.lib.colors import HexColor
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

    conn.commit()
    conn.close()
init_db()
# ------------------------------------


@app.route("/")
def home():
    return render_template("home.html")


# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":

        data = (
            request.form.get("full_name"),
            request.form.get("dob"),
            request.form.get("age"),
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

            request.form.get("amount"),
            request.form.get("payment_plan"),
            request.form.get("reference"),

            "Pending",  # force status controlled by admin

            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

        conn = get_db()
        conn.execute("""
        INSERT INTO players (
            full_name,dob,age,gender,school,grade,address,village,position,shirt_size,
            parent_name,relationship,phone1,phone2,email,
            medical,injuries,allergies,
            skill,goals,
            amount,payment_plan,reference,payment_status,created_at
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
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

#-------Receipt----------
#-------Receipt----------
# ------- Receipt (STABLE VERSION) ----------
@app.route("/receipt/<int:player_id>")
def generate_receipt(file_path, player, parent, amount, phone, receipt_no):

    width, height = landscape(A5)
    c = canvas.Canvas(file_path, pagesize=(width, height))

    # COLORS (from UI)
    primary = HexColor("#0B5ED7")      # Blue header
    accent = HexColor("#20C997")       # Green amount
    light = HexColor("#F8F9FA")        # Card background
    dark = HexColor("#212529")         # Text

    # ================= HEADER =================
    c.setFillColor(primary)
    c.rect(0, height-55, width, 55, fill=1, stroke=0)

    # Academy Name
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(30, height-35, "MIRACLE BASKETBALL ACADEMY")

    c.setFont("Helvetica", 10)
    c.drawString(30, height-50, "Official Payment Receipt")

    # Receipt badge
    c.setFillColor(white)
    c.roundRect(width-170, height-48, 150, 28, 8, fill=1, stroke=0)

    c.setFillColor(primary)
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(width-95, height-32, f"Receipt #{receipt_no}")

    # ================= LOGO =================
    logo_path = "static/logo.png"
    if os.path.exists(logo_path):
        c.drawImage(logo_path, width-80, height-55, 45, 45, mask='auto')

    # ================= PLAYER CARD =================
    c.setFillColor(light)
    c.roundRect(25, height-135, width/2-35, 70, 10, fill=1, stroke=0)

    c.setFillColor(dark)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, height-80, "PLAYER DETAILS")

    c.setFont("Helvetica", 11)
    c.drawString(40, height-100, f"Name: {player}")
    c.drawString(40, height-115, f"Parent: {parent}")
    c.drawString(40, height-130, f"Phone: {phone}")

    # ================= PAYMENT CARD =================
    c.setFillColor(light)
    c.roundRect(width/2+10, height-135, width/2-35, 70, 10, fill=1, stroke=0)

    c.setFillColor(dark)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(width/2+25, height-80, "PAYMENT INFO")

    c.setFont("Helvetica", 11)
    c.drawString(width/2+25, height-100, "Description: Training Fees")

    c.drawString(width/2+25, height-115,
        f"Date: {datetime.now().strftime('%d %b %Y')}")

    # AMOUNT BIG GREEN
    c.setFillColor(accent)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(width/2+25, height-135, f"UGX {amount:,}")

    # ================= TABLE =================
    c.setFillColor(primary)
    c.rect(25, height-180, width-50, 25, fill=1, stroke=0)

    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(35, height-165, "Description")
    c.drawString(width-160, height-165, "Amount")

    # Row
    c.setFillColor(light)
    c.rect(25, height-210, width-50, 30, fill=1, stroke=0)

    c.setFillColor(black)
    c.setFont("Helvetica", 11)
    c.drawString(35, height-195, "Monthly Training Fee")
    c.drawRightString(width-40, height-195, f"UGX {amount:,}")

    # ================= TOTAL =================
    c.setFont("Helvetica-Bold", 14)
    c.drawRightString(width-40, height-225, f"TOTAL: UGX {amount:,}")

    # ================= FOOTER =================
    c.setStrokeColor(primary)
    c.line(40, 55, 200, 55)

    c.setFont("Helvetica", 9)
    c.drawString(40, 40, "Authorized Signature")

    c.drawRightString(width-40, 40, "Thank you for supporting youth development!")

    c.save()
