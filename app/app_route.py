import os
import sqlite3
from flask import Flask, json, request, session, g, redirect, render_template, send_from_directory
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required
from graph import calculator_feelings

# Configure application
app = Flask(__name__)


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


# a connection to the SQLite database is created and stored in g (Flask's global object).
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect("data.db", check_same_thread=False)
    return g.db

# After the request is completed (either successfully or with an error),
# Flask automatically calls the close_db() function
@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()


# Tell Flask to call the after_request function (@app <- use flask)
@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Home page
@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    db = get_db()
    cursor = db.cursor()
    user_id = session["user_id"]
    cursor.execute("SELECT username FROM users WHERE id = ?", (user_id,))
    username = cursor.fetchall()
    username = username[0][0]

    getData(user_id)

    if request.method == "GET":
        return render_template("main.html", username=username)

    if request.method == "POST":
        date = request.form.get("date")
        feeling = request.form.get("feeling")
        description = request.form.get("description")

        if len(date) != 10:
            return apology("must provide correct year")

        cursor.execute("SELECT date FROM journals WHERE user_id = ?", (user_id,))
        check_date = cursor.fetchall()

        for dates in check_date:
            if date in dates[0]:
                cursor.execute(
                    "UPDATE journals SET feeling = ?, description = ? WHERE user_id = ? AND date = ?"
                    ,(feeling, description, user_id, date))
                db.commit()
                return redirect("/")

        cursor.execute("INSERT INTO journals (user_id, date, feeling, description) VALUES(?, ?, ?, ?)",
                    (user_id, date, feeling, description))
        db.commit()

    return redirect("/")

# Make JSON file for weekly report
# json_directory: to determine the absolute path to the parent directory of the current Python script file
# send_from_directory(): to send a file from a specific directory to the client
@app.route('/weekly_feeling.json')
def weekly_feeling_data():
    json_directory = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    return send_from_directory(json_directory, 'weekly_feeling.json')

# Make JSON file for all report
@app.route('/all_feeling.json')
def all_feeling_data():
    json_directory = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    return send_from_directory(json_directory, 'all_feeling.json')


@app.route("/history")
@login_required
def calendar():
    user_id = session["user_id"]

    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT username FROM users WHERE id = ?", (user_id,))
    username = cursor.fetchall()
    username = username[0]

    cursor.execute("SELECT date, feeling, description FROM journals WHERE user_id = ? ORDER BY date desc", (user_id,))
    data = cursor.fetchall()

    return render_template("history.html", data=data, username=username)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    session.clear()

    # User reached route via GET (as by clicking a link or via redirect)
    if request.method == "GET":
        return render_template("login.html")

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        # Query database for username
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = cursor.fetchall()

        # Ensure username exists
        if len(row) != 1:
            return apology("invalid username", 403)

        #check whether password is correct
        hash = row[0][5]
        if not check_password_hash(hash, password):
            return apology("invalid password", 403)

        # Remember which user has logged in
        session["user_id"] = row[0][0]
        user_id = session["user_id"]
        getData(user_id)

        # Redirect user to home page
        return render_template("main.html", username=username)


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "GET":
        return render_template("register.html")

    if request.method == "POST":

        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        birth = request.form.get("birth")
        username = request.form.get("username")
        password = request.form.get("password")
        confirm = request.form.get("confirm")

        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        check = cursor.fetchall()

        if len(check) != 0:
            return apology("username is already taken")

        if password != confirm:
            return apology("could not confirm password")

        if len(birth) != 10:
            return apology("must provide correct birth year")

        hash = generate_password_hash(password)

        cursor.execute("INSERT INTO users (first_name, last_name, birth, username, hash) VALUES(?, ?, ?, ?, ?)",
                    (first_name, last_name, birth, username, hash))
        db.commit()

        return redirect("/login")


@app.route("/reset_password", methods=["GET", "POST"])
def reset_password():
    if request.method == "GET":
        return render_template("forget.html")

    if request.method == "POST":
        username = request.form.get("username")
        old_password = request.form.get("old_password")
        new_password = request.form.get("new_password")
        confirm = request.form.get("confirm")

        if new_password != confirm:
            return apology("could not confirm password")

        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT username, hash FROM users WHERE username = ?", (username,))
        check = cursor.fetchall()

        if len(check) != 1:
            return apology("username does not exist")

        hash = check[0][1]
        if not check_password_hash(hash, old_password) or username in check:
            return apology("user does not exist. is your information correct?")

        hash = generate_password_hash(new_password)

        cursor.execute("UPDATE users SET hash = ? WHERE username = ?",
                    (hash, username))
        db.commit()

        return redirect("/login")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


def getData(user_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT feeling FROM journals WHERE user_id = ? ORDER BY date desc"
                    ,(user_id,))
    weekly_feelings = cursor.fetchall()

    cursor.execute("SELECT feeling FROM journals WHERE user_id = ? ORDER BY date desc LIMIT 7"
                    ,(user_id,))
    all_feelings = cursor.fetchall()

    weekly_feelings = calculator_feelings(weekly_feelings)
    all_feelings = calculator_feelings(all_feelings)

    with open('weekly_feeling.json', 'w') as weekly_file:
        json.dump(weekly_feelings, weekly_file)

    with open('all_feeling.json', 'w') as all_file:
        json.dump(all_feelings, all_file)
