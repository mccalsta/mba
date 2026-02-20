
from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3, os

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY","devsecret")

DB="database.db"

def init_db():
    conn=sqlite3.connect(DB)
    conn.execute("""CREATE TABLE IF NOT EXISTS registrations(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,email TEXT,phone TEXT,gender TEXT,dob TEXT,guardian TEXT,medical TEXT
    )""")
    conn.commit(); conn.close()

init_db()

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/register",methods=["GET","POST"])
def register():
    if request.method=="POST":
        data=(request.form.get("name"),request.form.get("email"),request.form.get("phone"),
              request.form.get("gender"),request.form.get("dob"),request.form.get("guardian"),
              request.form.get("medical"))
        conn=sqlite3.connect(DB)
        conn.execute("INSERT INTO registrations(name,email,phone,gender,dob,guardian,medical) VALUES(?,?,?,?,?,?,?)",data)
        conn.commit(); conn.close()
        return redirect("/")
    return render_template("register.html")

@app.route("/admin",methods=["GET","POST"])
def admin():
    if request.method=="POST":
        if request.form.get("username")=="admin" and request.form.get("password")=="admin123":
            session["admin"]=True
            return redirect("/dashboard")
    return render_template("admin.html")

@app.route("/dashboard")
def dashboard():
    if not session.get("admin"): return redirect("/admin")
    conn=sqlite3.connect(DB)
    rows=conn.execute("SELECT * FROM registrations").fetchall()
    conn.close()
    return render_template("dashboard.html",rows=rows)

if __name__=="__main__":
    app.run()
