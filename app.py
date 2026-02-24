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
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()
    elements = []

    # ---------------- HEADER ----------------
    logo_path = os.path.join(app.root_path, "static", "logo.png")

    try:
        logo = Image(logo_path, width=70, height=70)
    except:
        logo = Spacer(1, 70)

    title = Paragraph("<b>MIRACLE BASKETBALL ACADEMY</b>", styles["Title"])
    subtitle = Paragraph("Official Payment Receipt", styles["Normal"])
    motto = Paragraph(
        "<i>Developing Skills • Building Character • Creating Champions</i>",
        styles["Normal"]
    )

    header_table = Table([
        [logo, [title, subtitle, motto]]
    ], colWidths=[80, 400])

    elements.append(header_table)
    elements.append(Spacer(1, 20))

    # ---------------- RECEIPT INFO ----------------
    receipt_info = Table([
        ["Receipt No:", f"MBA-{player['id']:05d}"],
        ["Date:", datetime.now().strftime("%d/%m/%Y")]
    ], colWidths=[120, 200])

    receipt_info.setStyle(TableStyle([
        ("BOX", (0,0), (-1,-1), 1, colors.black),
        ("INNERGRID", (0,0), (-1,-1), 0.5, colors.grey),
        ("FONTNAME", (0,0), (-1,-1), "Helvetica-Bold")
    ]))

    elements.append(receipt_info)
    elements.append(Spacer(1, 20))

    # ---------------- RECEIVED FROM ----------------
    received = Table([
        ["Received From:", player["parent_name"]],
        ["Player Name:", player["full_name"]],
        ["Payment Plan:", player["payment_plan"]]
    ], colWidths=[150, 300])

    received.setStyle(TableStyle([
        ("BOX", (0,0), (-1,-1), 1, colors.black),
        ("INNERGRID", (0,0), (-1,-1), 0.5, colors.grey),
    ]))

    elements.append(received)
    elements.append(Spacer(1, 20))

    # ---------------- PAYMENT TABLE ----------------
    amount = int(player["amount"])

    payment_table = Table([
        ["Description", "Amount (UGX)"],
        ["Basketball Training Fees", f"{amount:,}"],
        ["", ""],
        ["TOTAL", f"UGX {amount:,}"]
    ], colWidths=[350, 150])

    payment_table.setStyle(TableStyle([
        ("BOX", (0,0), (-1,-1), 1, colors.black),
        ("INNERGRID", (0,0), (-1,-1), 0.5, colors.grey),
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTNAME", (0,3), (-1,3), "Helvetica-Bold"),
        ("ALIGN", (1,0), (1,-1), "RIGHT"),
    ]))

    elements.append(payment_table)
    elements.append(Spacer(1, 40))

    # ---------------- SIGNATURE ----------------
    signature = Table([
        ["", "Authorized Signature"],
    ], colWidths=[350,150])

    signature.setStyle(TableStyle([
        ("LINEABOVE", (1,0), (1,0), 1, colors.black),
        ("ALIGN", (1,0), (1,0), "CENTER"),
    ]))

    elements.append(signature)
    elements.append(Spacer(1, 20))

    footer = Paragraph(
        "Thank you for being part of Miracle Basketball Academy",
        styles["Normal"]
    )
    elements.append(footer)

    doc.build(elements)

    buffer.seek(0)
    return send_file(buffer, as_attachment=False, download_name="receipt.pdf", mimetype="application/pdf")
