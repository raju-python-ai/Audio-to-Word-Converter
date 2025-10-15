from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models.user_model import add_user, get_user_by_email

auth_bp = Blueprint("auth", __name__)

# Root → redirect to login
@auth_bp.route("/")
def index():
    return render_template("logo.html")  # Show logo page first

# @auth_bp.route("/")
# def index():
#     return redirect(url_for("auth.login"))

# -------------------------
# LOGIN
# -------------------------
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        # 🔎 Find user by email
        user = get_user_by_email(email)

        if user:
            db_password = user[4]  # password column
            if db_password == password:
                # ✅ Save user in session
                session["user"] = user[1]        # username
                session["user_email"] = user[3]  # email
                return redirect(url_for("main.home"))
            else:
                flash("Incorrect password")
        else:
            flash("Email not registered")

        return render_template("login.html")

    return render_template("login.html")

# -------------------------
# REGISTER
# -------------------------
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        mobile = request.form.get("mobile")
        email = request.form.get("email")
        password = request.form.get("password")

        if not (username and mobile and email and password):
            flash("All fields are required")
            return render_template("register.html")

        try:
            # ✅ Save user in DB
            add_user(username, mobile, email, password)

            # ✅ Auto login after register
            session["user"] = username
            session["user_email"] = email
            return redirect(url_for("main.home"))

        except Exception as e:
            flash("Error: " + str(e))
            return render_template("register.html")

    return render_template("register.html")

# -------------------------
# LOGOUT
# -------------------------
@auth_bp.route("/logout")
def logout():
    session.pop("user", None)
    session.pop("user_email", None)   # ✅ clear email also
    return redirect(url_for("auth.login"))
