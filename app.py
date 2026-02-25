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
def build_receipt_pdf(file_path, player, parent, phone, amount, receipt_no):

    width, height = landscape(A5)
    c = canvas.Canvas(file_path, pagesize=(width, height))

    # Colors (UI palette)
    primary = HexColor("#1E63C6")
    accent = HexColor("#1DBE73")
    light = HexColor("#F1F4F8")
    dark = HexColor("#1F2937")

    # ================= PAGE BACKGROUND =================
    c.setFillColor(HexColor("#E9EEF5"))
    c.rect(0, 0, width, height, fill=1, stroke=0)

    # ================= MAIN CARD =================
    card_x = 40
    card_y = 35
    card_w = width - 80
    card_h = height - 70

    c.setFillColor(white)
    c.roundRect(card_x, card_y, card_w, card_h, 14, fill=1, stroke=0)

    # ================= HEADER =================
    header_h = 65
    c.setFillColor(primary)
    c.roundRect(card_x, card_y + card_h - header_h, card_w, header_h, 14, fill=1, stroke=0)

    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(card_x + 20, card_y + card_h - 35, "MIRACLE BASKETBALL ACADEMY")

    c.setFont("Helvetica", 10)
    c.drawString(card_x + 20, card_y + card_h - 50, "Official Payment Receipt")

    # Receipt Badge
    badge_w = 150
    badge_h = 28
    c.setFillColor(white)
    c.roundRect(card_x + card_w - badge_w - 20, card_y + card_h - 45, badge_w, badge_h, 10, fill=1, stroke=0)

    c.setFillColor(primary)
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(card_x + card_w - badge_w/2 - 20, card_y + card_h - 30, f"Receipt #{receipt_no}")

    # Logo
    logo_path = "static/logo.png"
    if os.path.exists(logo_path):
        c.drawImage(logo_path, card_x + card_w - 55, card_y + card_h - 58, 38, 38, mask='auto')

    # ================= INFO CARDS =================
    section_top = card_y + card_h - header_h - 25
    card_height = 70
    gap = 18

    left_x = card_x + 20
    left_y = section_top - card_height
    left_w = (card_w - 60) / 2

    right_x = left_x + left_w + gap
    right_y = left_y
    right_w = left_w

    # Player Card
    c.setFillColor(light)
    c.roundRect(left_x, left_y, left_w, card_height, 10, fill=1, stroke=0)

    c.setFillColor(dark)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(left_x + 15, left_y + 50, "PLAYER DETAILS")

    c.setFont("Helvetica", 10)
    c.drawString(left_x + 15, left_y + 35, f"Name: {player}")
    c.drawString(left_x + 15, left_y + 22, f"Parent: {parent}")
    c.drawString(left_x + 15, left_y + 9, f"Phone: {phone}")

    # Payment Card
    c.setFillColor(light)
    c.roundRect(right_x, right_y, right_w, card_height, 10, fill=1, stroke=0)

    c.setFillColor(dark)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(right_x + 15, right_y + 50, "PAYMENT INFO")

    c.setFont("Helvetica", 10)
    c.drawString(right_x + 15, right_y + 35, "Description: Training Fees")
    c.drawString(right_x + 15, right_y + 22, f"Date: {datetime.now().strftime('%d %b %Y')}")

    c.setFillColor(accent)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(right_x + 15, right_y + 7, f"UGX {amount:,}")

    # ================= TABLE =================
    table_x = card_x + 20
    table_w = card_w - 40
    table_y = left_y - 95

    # Header
    c.setFillColor(primary)
    c.rect(table_x, table_y + 35, table_w, 25, fill=1, stroke=0)

    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(table_x + 10, table_y + 45, "Description")
    c.drawRightString(table_x + table_w - 10, table_y + 45, "Amount")

    # Row
    c.setFillColor(light)
    c.rect(table_x, table_y + 5, table_w, 30, fill=1, stroke=0)

    c.setFillColor(black)
    c.setFont("Helvetica", 11)
    c.drawString(table_x + 10, table_y + 15, "Monthly Training Fee")
    c.drawRightString(table_x + table_w - 10, table_y + 15, f"UGX {amount:,}")

    # Total
    c.setFont("Helvetica-Bold", 14)
    c.drawRightString(card_x + card_w - 20, table_y - 10, f"TOTAL: UGX {amount:,}")

    # ================= FOOTER =================
    footer_y = card_y + 25

    c.setStrokeColor(primary)
    c.line(card_x + 20, footer_y + 15, card_x + 180, footer_y + 15)

    c.setFont("Helvetica", 9)
    c.drawString(card_x + 20, footer_y, "Authorized Signature")
    c.drawRightString(card_x + card_w - 20, footer_y, "Thank you for supporting youth development!")

    c.save()

@app.route("/receipt/<int:player_id>")
def generate_receipt(player_id):

    conn = get_db()
    player = conn.execute(
        "SELECT * FROM players WHERE id=?",
        (player_id,)
    ).fetchone()
    conn.close()

    if not player:
        return "Player not found", 404

    buffer = io.BytesIO()

    build_receipt_pdf(
        buffer,
        player["full_name"],
        player["parent_name"],
        int(player["amount"]),
        player["phone1"] or "-",
        f"MBA-{player['id']:05d}"
    )

    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=False,
        download_name=f"receipt_{player_id}.pdf",
        mimetype="application/pdf"
    )
