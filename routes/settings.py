from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from models.user_model import get_user_by_email, update_user

settings_bp = Blueprint("settings", __name__, template_folder="templates/settings")

# 🈯 Inline translation dictionary
translations = {
    "english": {
        "menu": "Menu",
        "account": "Account",
        "username": "Username",
        "email": "Email ID",
        "phone": "Phone Number",
        "password": "Password",
        "update": "Update",
        "success": "Account updated successfully!"
    },
    "tamil": {
        "menu": "மெனு",
        "account": "கணக்கு",
        "username": "பயனாளர் பெயர்",
        "email": "மின்னஞ்சல் ",
        "phone": "தொலைபேசி எண்",
        "password": "கடவுச்சொல்",
        "update": "புதுப்பிக்கவும்",
        "success": "கணக்கு வெற்றிகரமாக புதுப்பிக்கப்பட்டது!"
    }
}

@settings_bp.route("/settings/<page>", methods=["GET", "POST"])
def settings_page(page):
    allowed = ["account", "lang_select", "version", "help", "privacy"]
    if page not in allowed:
        return "Page not found", 404

    if page == "account":
        user_email = session.get("user_email")
        if not user_email:
            return redirect(url_for("main.home"))

        user = get_user_by_email(user_email)
        if not user:
            return redirect(url_for("main.home"))

        # 🈯 get selected language
        lang = session.get("lang", "english")
        t = translations[lang]

        if request.method == "POST":
            username = request.form.get("username")
            phone = request.form.get("phone")
            password = request.form.get("password")
            update_user(user_email, username, phone, password)
            flash(t["success"])  # ✅ flash in correct language
            user = get_user_by_email(user_email)  # refresh data

        return render_template("account.html", user=user, t=t)

    return render_template(f"{page}.html")

# --- Language selection page (unchanged) ---
@settings_bp.route("/settings/lang_select", methods=["GET", "POST"])
def settings_language():
    if "user" not in session:
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        lang = request.form.get("language")
        if lang not in ["tamil", "english"]:
            flash("Please select a valid language")
            return render_template("lang_select.html", t=session.get("t", {}))
        session["lang"] = lang  # ✅ update session with new language
        return redirect(url_for("main.home"))

    return render_template("lang_select.html", t=session.get("t", {}))
