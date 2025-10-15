# main_routes.py
from flask import Blueprint, render_template, session, redirect, url_for, request, flash

main_bp = Blueprint("main", __name__)

@main_bp.route("/home")
def home():
    if "user" not in session:
        return redirect(url_for("auth.login"))

    if "lang" not in session:
        return redirect(url_for("main.select_language"))

    translations = {
        "english": {
            # "back":"back",
            "title": "Tamil Audio File",
            "convert": "Convert to Word",
            "select_format": "Select Download Format",
            "menu": "Menu",
            "dashboard": "Dashboard",
            "history": "History",
            "home": "Home",
            "files": "Files",
            "settings": "Settings",
            "help": "Help",
            "logout": "Logout",
            "back": "Back",
            "account": "Account",
            "language": "Language",
            "version": "Version",
            "privacy": "Privacy",
            "Clear":"Clear",
            "choose_file": "Choose File",
            "transcribed_placeholder":"Transcribed Tamil text will appear here....",
            "alerts": {
                "no_file": "Please select or record a file first!",
                "mic_error": "Microphone access denied or not available.",
                "processing": "Processing...",
                "done": "Conversion complete!",
                "error": "An error occurred."
            }
        },
        "tamil": {
            # "back":
            "title": "தமிழ் ஒலிக் கோப்பு",
            "convert": " மாற்றவும்",
            "select_format": "பதிவிறக்க வடிவத்தைத் தேர்ந்தெடுக்கவும்",
            "menu": "மெனு",
            "dashboard": "கண்காணிப்பு பலகை",
            "history": "வரலாறு",
            "home": "முகப்பு",
            "files": "கோப்புகள்",
            "settings": "அமைப்புகள்",
            "help": "உதவி",
            "logout": "வெளியேறு",
            # "back": "பின்னோக்கு",
            "account": "கணக்கு",
            "language": "மொழி",
            "version": "பதிப்பு",
            "privacy": "தனியுரிமை",
            "Clear":"அழித்தல்",
            "choose_file": "கோப்பை தேர்ந்தெடுக்கவும்",
            "transcribed_placeholder":"மாற்றிய தமிழ் உரை இங்கே தோன்றும்...",
            "alerts": {
                "no_file": "முதலில் ஒரு கோப்பை தேர்வு செய்யவும் அல்லது பதிவு செய்யவும்!",
                "mic_error": "மைக்க்ரோஃபோன் அணுகல் மறுக்கப்பட்டது அல்லது கிடைக்கவில்லை.",
                "processing": "செயலாக்கப்படுகிறது...",
                "done": "மாற்றம் முடிந்தது!",
                "error": "ஒரு பிழை ஏற்பட்டது."
            }
        }
    }

    lang = session["lang"]
    return render_template("home.html", user=session["user"], lang=lang, t=translations[lang])

@main_bp.route("/select-language", methods=["GET", "POST"])
def select_language():
    if "user" not in session:
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        lang = request.form.get("language")
        if lang not in ["tamil", "english"]:
            flash("Please select a valid language")
            return render_template("lang_select.html")
        session["lang"] = lang
        return redirect(url_for("main.home"))

    return render_template("lang_select.html")
