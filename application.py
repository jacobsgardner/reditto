from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from flask_socketio import SocketIO, emit
import hashlib
from flask_session import Session

app = Flask(__name__)
app.secret_key = "ThisIsASecretKey"
app.config.from_pyfile("config.cfg")
Session(app)
socketio = SocketIO(app)
con = sqlite3.connect("redditto.db")
db = con.cursor()

with open('init.sql') as f:
    db.executescript(f.read())


def authenticate():
    if "username" in session:
        return True
    else:
        return False
@app.route("/")
def redir():
    return redirect("/0")

@app.route("/<int:page>")
def frontpage(page):
    """ Front page of the site where user posts are displayed """
    con = sqlite3.connect("redditto.db")
    db = con.cursor()
    posts = db.execute("SELECT * FROM posts ORDER BY votes DESC, created ASC").fetchall()
    posts = posts[(page*10): (page*10 + 10)]
    if authenticate():
        username = session["username"]
        loggedin = True
    else:
        username = ""
        loggedin = False
    return render_template("index.html", posts=posts, username=username, loggedin=loggedin, page=page)

@app.route("/makepost", methods=['POST'])
def makepost():
    """ Storing the data from a user post """
    con = sqlite3.connect("redditto.db")
    db = con.cursor()
    title = request.form.get("title")
    body = request.form.get("body")
    prevideo_link = request.form.get("video_link")
    video_link = prevideo_link.replace("watch?v=","embed/")
    image_link = request.form.get("image_link")
    db.execute(f"INSERT INTO posts (author_id, title, body, video, image, votes, username) VALUES ('{session.get('userid')}', '{title}', '{body}', '{video_link}', '{image_link}', '0', '{session.get('username')}')")
    con.commit()
    return redirect("/0")

@socketio.on("postvote")
def postvote(data):
    """ Tallying post votes """
    con = sqlite3.connect("redditto.db")
    db = con.cursor()
    db.execute(f"UPDATE posts SET votes = votes + {data['dir']} WHERE id = {data['id']}")
    con.commit()

@socketio.on("commentvote")
def commentvote(data):
    """ Tallying comment votes """
    con = sqlite3.connect("redditto.db")
    db = con.cursor()
    db.execute(f"UPDATE comments SET votes = votes + {data['dir']} WHERE id = {data['id']}")
    con.commit()

@app.route("/login", methods=["POST"])
def login():
    """ Logging the user in """
    con = sqlite3.connect("redditto.db")
    db = con.cursor()
    username = request.form.get("username")
    password = request.form.get("password")
    page = request.form.get("currentpage")
    if db.execute(f"SELECT * FROM users WHERE username = '{username}'").fetchall() == []:
        message = "Incorrect username and password combination!"
        return redirect(page)
    elif db.execute(f"SELECT password FROM users WHERE username = '{username}'").fetchone()[0] != hashlib.sha256(password.encode()).hexdigest():
        message = "Incorrect username and password combination!"
        return redirect(page)
    else:
        userid = db.execute(f"SELECT id FROM users WHERE username = '{username}'").fetchone()[0]
        session["username"] = username
        session["userid"] = userid
        page = request.form.get("currentpage")
        return redirect(page)


@app.route("/logout", methods=["GET"])
def logout():
    """logging the user out"""
    session.pop("username", None)
    session.pop("userid", None)
    return redirect("/0")

@app.route("/register", methods=["GET"])
def register():
    """ Page with form to create new users """
    return render_template("register.html")

@app.route("/checkregister", methods=["POST"])
def checkregister():
    """ Registering new users """
    con = sqlite3.connect("redditto.db")
    db = con.cursor()
    username = request.form.get("username")
    password1 = request.form.get("password1")
    password2 = request.form.get("password2")
    if db.execute(f"SELECT * FROM users WHERE username = '{username}'").fetchall() != []:
        message = "The username entered is already in use"
        return render_template("register.html", message = message)
    if password1 != password2 and password1 != "":
        message = "The passwords entered do not match!"
        return render_template("register.html", message = message)
    hashed = hashlib.sha256(password1.encode()).hexdigest()
    db.execute(f"INSERT INTO users (username, password) VALUES ('{username}', '{hashed}')")
    con.commit()
    userid = db.execute(f"SELECT id FROM users WHERE username = '{username}'").fetchone()[0]
    session["userid"] = userid
    session["username"] = username
    session["loggedin"] = True
    return redirect("/0")

@app.route("/comments/<int:id>")
def comments(id):
    """diplaying the comment page"""
    con = sqlite3.connect("redditto.db")
    db = con.cursor()
    post = db.execute(f"SELECT * FROM posts WHERE id = {id}").fetchone()
    comments = db.execute(f"SELECT * FROM comments WHERE post = {post[0]}").fetchall()
    comments = commentSort(post)
    if authenticate():
        username = session["username"]
        loggedin = True
    else:
        username = ""
        loggedin = False
    return render_template("comments.html", post=post, comments=comments, username=username, loggedin=loggedin)

@app.route("/makecomment", methods=["post"])
def makecomment():
    """ Making a user comment """
    con = sqlite3.connect("redditto.db")
    db = con.cursor()
    body = request.form.get("body")
    post = request.form.get("post")
    level = request.form.get("level")
    parent = request.form.get("parent")
    db.execute(f"INSERT INTO comments (author_id, body, post, votes, level, parent, username) VALUES ('{session.get('userid')}', '{body}', '{post}', '0', '{level}', '{parent}', '{session.get('username')}')")
    con.commit()
    return redirect(url_for("comments", id = post))

def commentSort(post):
    """function to sort comments"""
    con = sqlite3.connect("redditto.db")
    db = con.cursor()
    zero = db.execute(f"SELECT * FROM comments WHERE post = {post[0]} AND level = 0 ORDER BY votes DESC").fetchall()
    nexts = db.execute(f"SELECT * FROM comments WHERE post = {post[0]} AND level = 1 ORDER BY votes DESC").fetchall()
    rest = []
    i = 1
    while (nexts != []):
        i += 1
        rest.append(nexts)
        nexts = db.execute(f"SELECT * FROM comments WHERE post = {post[0]} AND level = {i} ORDER BY votes DESC").fetchall()
    return {"zero": zero, "rest": rest}



