from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
import os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask import send_file
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import io
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from datetime import datetime




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
    pdf = canvas.Canvas(buffer, pagesize=A4)

    width, height = A4

    # ================= HEADER =================
    # Logo
    try:
        pdf.drawImage("static/logo.png", 40, height-120, width=90, preserveAspectRatio=True, mask='auto')
    except:
        pass

    # Academy Name
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(150, height-70, "MIRACLE BASKETBALL ACADEMY")

    pdf.setFont("Helvetica", 11)
    pdf.drawString(150, height-90, "Official Payment Receipt")
    pdf.drawString(150, height-105, "Developing Skills • Building Character • Creating Champions")

    # ================= RECEIPT BOX =================
    pdf.setStrokeColor(colors.black)
    pdf.rect(width-200, height-120, 160, 80)

    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(width-185, height-60, "RECEIPT NO:")
    pdf.drawString(width-185, height-90, "DATE:")

    pdf.setFont("Helvetica", 11)
    pdf.drawString(width-110, height-60, f"MBA-{player['id']:05d}")
    pdf.drawString(width-110, height-90, datetime.now().strftime("%d/%m/%Y"))

    # ================= RECEIVED FROM =================
    y = height - 180

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(40, y, "Received With Thanks From:")

    pdf.rect(40, y-25, width-80, 25)
    pdf.setFont("Helvetica", 11)
    pdf.drawString(50, y-18, player["parent_name"])

    # ================= PLAYER DETAILS =================
    y -= 70

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(40, y, "Player Name:")
    pdf.setFont("Helvetica", 11)
    pdf.drawString(150, y, player["full_name"])

    y -= 25
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(40, y, "Payment Plan:")
    pdf.setFont("Helvetica", 11)
    pdf.drawString(150, y, player["payment_plan"])

    # ================= PAYMENT TABLE =================
    y -= 60

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(40, y, "Payment Details")

    y -= 20
    pdf.rect(40, y-80, width-80, 80)

    pdf.line(40, y-40, width-40, y-40)

    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(50, y-25, "Description")
    pdf.drawString(width-200, y-25, "Amount (UGX)")

    pdf.setFont("Helvetica", 11)
    pdf.drawString(50, y-65, "Basketball Training Fees")
    pdf.drawString(width-200, y-65, f"{int(player['amount']):,}")

    # ================= SIGNATURE =================
    y -= 120

    pdf.line(width-250, y, width-60, y)
    pdf.setFont("Helvetica", 11)
    pdf.drawString(width-230, y-15, "Authorized Signature")

    # ================= FOOTER =================
    pdf.setFont("Helvetica-Oblique", 10)
    pdf.drawCentredString(width/2, 60, "Thank you for being part of Miracle Basketball Academy")

    pdf.showPage()
    pdf.save()

    buffer.seek(0)

    return send_file(buffer, as_attachment=False, download_name="receipt.pdf", mimetype="application/pdf")
