from datetime 
import timedelta 
import os 
import sqlite3 
import subprocess from functools import wraps 

from flask import Flask from flask import render_template from flask import request from flask import redirect from flask import url_for from flask import session from flask import jsonify 

from werkzeug.security import check_password_hash from werkzeug.security import generate_password_hash 

# BASE_DIR = "/home/awx/sensor_reboot_panel" DB_PATH = os.path.join(BASE_DIR, "sensor_panel.db")  #This must be changed as per your path

BASE_DIR="/home/world/Documents/sensor_reboot_panel"
DB_PATH=os.path.join(BASE_DIR,"sensor_panel.db")


ANSIBLE_DIR = os.path.join(BASE_DIR, "ansible") 
INVENTORY = os.path.join(ANSIBLE_DIR, "inventory.ini") 
VAULT_PASS_FILE = os.path.join(ANSIBLE_DIR, ".vault_pass.txt") 

app = Flask(name) 
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "CHANGE_THIS") 
app.permanent_session_lifetime = timedelta(minutes=15) 

def get_db(): 
    conn = sqlite3.connect(DB_PATH) 
    conn.row_factory = sqlite3.Row 
    return conn 

def login_required(func): @wraps(func) def wrapped(*args, **kwargs): if "user" not in session: return redirect(url_for("login")) return func(*args, **kwargs) return wrapped 

def superadmin_required(func): @wraps(func) def wrapped(*args, **kwargs): user = session.get("user", {}) if user.get("role") != "superadmin": return "Forbidden", 403 return func(*args, **kwargs) return wrapped 

@app.route("/") def root(): return redirect(url_for("login")) 

@app.route("/login", methods=["GET", "POST"]) def login(): error = None 

if request.method == "POST": 
    username = request.form["username"] 
    password = request.form["password"] 
 
    db = get_db() 
    user = db.execute( 
        "SELECT * FROM users WHERE username = ?", 
        (username,) 
    ).fetchone() 
 
    if user and check_password_hash(user["password_hash"], password): 
        session.permanent = True 
        session["user"] = { 
            "id": user["id"], 
            "username": user["username"], 
            "role": user["role"] 
        } 
        return redirect(url_for("panel")) 
 
    error = "Invalid credentials" 
 
return render_template("login.html", error=error) 
  

@app.route("/logout") def logout(): session.clear() return redirect(url_for("login")) 

@app.route("/panel") @login_required def panel(): db = get_db() sensors = db.execute("SELECT * FROM sensors").fetchall() return render_template("index.html", sensors=sensors) 

@app.route("/reboot/int:sensor_id", methods=["POST"]) @login_required def reboot(sensor_id): db = get_db() sensor = db.execute( "SELECT * FROM sensors WHERE id = ?", (sensor_id,) ).fetchone() 

command = [ 
    "ansible-playbook", 
    sensor["playbook_path"], 
    "-i", 
    INVENTORY, 
    "--limit", 
    sensor["ansible_host_name"], 
    "--vault-password-file", 
    VAULT_PASS_FILE 
] 
 
result = subprocess.run( 
    command, 
    capture_output=True, 
    text=True 
) 
 
if result.returncode != 0: 
    return jsonify( 
        {"status": "error", "details": result.stderr} 
    ), 500 
 
return jsonify({"status": "ok"}) 
  

@app.route("/admin/users", methods=["GET", "POST"]) @superadmin_required def manage_users(): db = get_db() 

if request.method == "POST": 
    delete_id = request.form.get("delete_id") 
 
    if delete_id: 
        db.execute( 
            "DELETE FROM users WHERE id = ? AND role != 'superadmin'", 
            (delete_id,) 
        ) 
    else: 
        db.execute( 
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", 
            ( 
                request.form["username"], 
                generate_password_hash(request.form["password"]), 
                request.form["role"] 
            ) 
        ) 
 
    db.commit() 
 
users = db.execute("SELECT * FROM users").fetchall() 
return render_template("users.html", users=users) 
  

if name == "main": app.run(host="0.0.0.0", port=5000)
