from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
import os
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
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS players (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        full_name TEXT,
        dob TEXT,
        age TEXT,
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

        amount TEXT,
        payment_method TEXT,
        reference TEXT,

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
            request.form.get("payment_method"),
            request.form.get("reference"),

            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

        conn = get_db()
        conn.execute("""
        INSERT INTO players (
            full_name,dob,age,gender,school,grade,address,village,position,shirt_size,
            parent_name,relationship,phone1,phone2,email,
            medical,injuries,allergies,
            skill,goals,
            amount,payment_method,reference,created_at
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, data)

        conn.commit()
        conn.close()

        flash("Registration saved successfully!")
        return redirect("/register")

    return render_template("register.html")


# ---------------- ADMIN LOGIN ----------------
@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        if request.form["username"] == "admin" and request.form["password"] == "admin123":
            session["admin"] = True
            return redirect("/dashboard")
        else:
            flash("Invalid credentials")

    return render_template("admin_login.html")


# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if not session.get("admin"):
        return redirect("/admin")

    conn = get_db()
    players = conn.execute("SELECT * FROM players ORDER BY id DESC").fetchall()
    conn.close()

    return render_template("admin_dashboard.html", players=players)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/admin")


if __name__ == "__main__":
    app.run(debug=True)
