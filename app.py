from flask import Flask, render_template, request, redirect, url_for, session, flash
import hashlib
import sqlite3
import requests
def hash_word(word):
    hashed_word = hashlib.sha224(word.encode()).hexdigest()
    return hashed_word
def init_db():
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()

    # Enable foreign keys
    cur.execute("PRAGMA foreign_keys = ON;")

    # Create users table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT NOT NULL,
        password TEXT NOT NULL,
        bio TEXT
    );
    """)

    # Create books table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL,
        title TEXT NOT NULL,
        author TEXT NOT NULL,
        cover_id TEXT NOT NULL,
        ebook_access TEXT NOT NULL,
        first_publish_year TEXT NOT NULL,
        FOREIGN KEY(email) REFERENCES users(email)
    );
    """)

    conn.commit()
    conn.close()
    print("Database initialized successfully!")
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn
app = Flask(__name__)
app.secret_key = "your_secret_key_here"
@app.route('/')
def index():
    return render_template('index.html')
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        hashed = hash_word(str(password))
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cur.fetchone()
        conn.close()

        if user is None:
            # User not found
            error = "Invalid username or password"
            return render_template("login.html", error=error)

        # Check hashed password
        if user['password'] == hashed:
            session["email"] = email
            return redirect(url_for("account"))
        else:
            error = "Invalid username or password"
            return render_template("login.html", error=error)
    return render_template('login.html')
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == "POST":
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        c_password = request.form.get('c_password')
        if c_password == password :
            hashed = hash_word(str(password))
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)", (name,  email, hashed))
            conn.commit()
            conn.close()
            return redirect(url_for("login"))
    return render_template('signup.html')
@app.route('/category', methods=['GET', 'POST'])
def category():
    url = "https://openlibrary.org/search.json"
    if request.method == "POST":
        conn = sqlite3.connect('database.db')
        cur = conn.cursor()
        cur.execute("DELETE FROM books")
        conn.commit()
        conn.close()
        search = request.form["search"]
        search = str(search)
        words = [word.strip() for word in search.split(',')]
        headers = {
        "User-Agent": "OpenTomes/1.0 (paulndeh86@gmail.com)"
        }
        m = len(words)
        if m <= 1:
            params = {
                    "q" : f"title: {words[0]}",
                     }
        else:
            params = {
                   "q" : f"title: {words[0]}, author:{words[1]}",
                     }
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        data1 = data['docs']
        size = len(data1)
        for i in range(size):
            author_name = data1[i]['author_name']
            s = ", ".join(author_name)
            print(s)
            title = str(data1[i]['title'])
            cover_id = str(data1[i].get("cover_i", "Paul"))
            ebook_access = str(data1[i]['ebook_access'])
            ebook_access = ebook_access.capitalize()
            first_publish_year = str(data1[i]['first_publish_year'])
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("INSERT INTO books (email, title, author, cover_id, ebook_access, first_publish_year) VALUES (?, ?, ?, ?, ?, ?)", (session["email"], title, s, cover_id, ebook_access, first_publish_year))
            conn.commit()
            conn.close()
        # Fetch user's search results
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM books WHERE email = ? ORDER BY first_publish_year", (session["email"],))
    results = cur.fetchall()
    conn.close()
    return render_template('library.html', results = results)
@app.route('/about')
def about():
    return render_template('about.html')
@app.route("/logout")
def logout():
    session.pop("email", None)
    return redirect(url_for("login"))
@app.route("/account", methods=['GET', 'POST'])
def account():
    if "email" not in session:
        return redirect(url_for("login"))
    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == "POST":
        bio = request.form["bio"]
        contact = request.form["contact"]
        cur.execute("UPDATE users SET bio = ?, username = ? WHERE email = ?",
                    (bio, contact, session["email"]))
        conn.commit()
        flash("Profile updated successfully!")

    cur.execute("SELECT username, bio, email FROM users WHERE email = ?", (session["email"],))
    user = cur.fetchone()
    conn.close()
    return render_template('account.html', user = user)
if __name__ == "__main__":
    init_db()
    app.run(debug=True)