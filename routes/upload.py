from flask import Blueprint, request, send_file, jsonify, render_template, send_from_directory,session,url_for,redirect
import os, time, re, math, traceback
from werkzeug.utils import secure_filename
from docx import Document
# from reportlab.pdfgen import canvas
# from reportlab.pdfbase import pdfmetrics
# from reportlab.pdfbase.ttfonts import TTFont
# from reportlab.lib.pagesizes import A4
# from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
# from reportlab.lib.styles import getSampleStyleSheet
# from reportlab.pdfbase.ttfonts import TTFont
# from reportlab.pdfbase import pdfmetrics
# from reportlab.lib.units import cm
from weasyprint import HTML
import os
import os
import speech_recognition as sr
from pydub import AudioSegment
import noisereduce as nr
import numpy as np
import soundfile as sf
from spleeter.separator import Separator
from collections import defaultdict

from models.history_model import add_history, get_all_history, init_history_table, get_counts
from models.user_model import get_user_by_email
from models.history_model import get_all_history
from collections import defaultdict

try:
    from tamil.utf8 import get_letters
except ImportError:
    get_letters = None

upload_bp = Blueprint("upload", __name__, template_folder="templates")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
TEMP_FOLDER = os.path.join(BASE_DIR, "temp")
TAMIL_FONT_FILE = os.path.join(BASE_DIR, "NotoSansTamil-Regular.ttf")
TAMIL_FONT_NAME = "NotoTamil"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(TEMP_FOLDER, exist_ok=True)


# initialize DB table (safe to call repeatedly)
init_history_table()

# ---------------- Helpers ---------------- #

def clean_tamil_text(text):
    """
    Clean Tamil text using get_letters and regex.
    If cleaning strips everything, fallback to raw text.
    """
    original = text
    if get_letters:
        text = "".join(get_letters(text))
    cleaned = re.sub(r"[^஀-௿ ]+", "", text).strip()

    if not cleaned:
        # fallback to raw text if no Tamil letters found
        cleaned = original.strip()

    print("Raw transcription:", original)
    print("Cleaned text:", cleaned)
    return cleaned



def separate_vocals(input_path):
    """Spleeter vocal separation"""
    try:
        separator = Separator('spleeter:2stems')
        output_dir = os.path.join(TEMP_FOLDER, f"sep_{int(time.time())}")
        os.makedirs(output_dir, exist_ok=True)
        separator.separate_to_file(input_path, output_dir)
        for root, dirs, files in os.walk(output_dir):
            for file in files:
                if file.endswith("vocals.wav"):
                    return os.path.join(root, file)
    except Exception as e:
        # any failure, return original input path
        print("Spleeter error:", e)
    return input_path

def denoise_audio(input_path):
    """Noise reduction"""
    try:
        data, rate = sf.read(input_path)
        if len(data.shape) > 1:
            data = np.mean(data, axis=1)
        reduced = nr.reduce_noise(y=data, sr=rate)
        temp_path = os.path.join(TEMP_FOLDER, f"clean_{int(time.time())}.wav")
        sf.write(temp_path, reduced, rate)
        return temp_path
    except Exception as e:
        print("Noise reduction error:", e)
        return input_path

def transcribe_audio(file_path, chunk_length_ms=60000, overlap_ms=1500):
    """Chunk-based transcription using old working logic"""
    audio = AudioSegment.from_file(file_path)
    recognizer = sr.Recognizer()
    full_text = []

    total_chunks = math.ceil(len(audio) / chunk_length_ms)
    for i in range(total_chunks):
        start = max(0, i * chunk_length_ms - overlap_ms)
        end = min(len(audio), (i + 1) * chunk_length_ms)
        chunk = audio[start:end]
        chunk_path = os.path.join(TEMP_FOLDER, f"chunk_{i}.wav")
        chunk.export(chunk_path, format="wav")

        with sr.AudioFile(chunk_path) as source:
            audio_data = recognizer.record(source)
            try:
                text = recognizer.recognize_google(audio_data, language="ta-IN")
                full_text.append(text)
            except sr.UnknownValueError:
                full_text.append("")
            except sr.RequestError as e:
                print("Google API error:", e)
                full_text.append("")

    return " ".join(full_text)


@upload_bp.route("/convert", methods=["POST"])
def convert_text():
    try:
        if "user_email" not in session:
            return jsonify({"error": "Login required"}), 403

        from models.user_model import get_user_by_email
        from models.history_model import add_history

        user = get_user_by_email(session["user_email"])
        if not user:
            return jsonify({"error": "User not found"}), 403

        user_id = user[0]

        text = request.form.get("text", "").strip()
        fmt = request.form.get("format", "docx").lower()
        if not text:
            return jsonify({"error": "No text to convert"}), 400
        if fmt not in ("docx", "pdf"):
            fmt = "docx"

        timestamp = int(time.time())
        output_filename = f"transcript_{timestamp}.{fmt}"
        output_path = os.path.join(UPLOAD_FOLDER, output_filename)

        if fmt == "docx":
            from docx import Document
            doc = Document()
            doc.add_paragraph(text)
            doc.save(output_path)
        else:
            save_as_pdf(text, output_path)

        # save in history
        add_history(output_filename, fmt, user_id)

        return send_file(output_path, as_attachment=True, download_name=output_filename)

    except Exception as e:
        print("CONVERT ERROR:", e)
        traceback.print_exc()
        return jsonify({"error": f"Conversion failed: {str(e)}"}), 500


def save_as_pdf(text, output_path):
    # 1. Sanitize & convert plain text to HTML
    html_content = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            @page {{
                size: A4;
                margin: 2cm;
            }}
            body {{
                font-family: '{TAMIL_FONT_NAME}', sans-serif;
                font-size: 16px;
                line-height: 1.6;
                white-space: pre-wrap;
            }}
        </style>
    </head>
    <body>
        {text}
    </body>
    </html>
    """

    # 2. Generate PDF
    HTML(string=html_content).write_pdf(output_path)

@upload_bp.route("/upload", methods=["POST"])
def upload():
    """Handle audio upload, transcribe Tamil, and return text (no file save)."""
    try:
        if "user_email" not in session:
            return jsonify({"error": "Login required"}), 403

        from models.user_model import get_user_by_email
        from models.history_model import add_history

        user = get_user_by_email(session["user_email"])
        if not user:
            return jsonify({"error": "User not found"}), 403

        user_id = user[0]

        if "audio" not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files["audio"]
        orig_filename = secure_filename(file.filename or f"record_{int(time.time())}.wav")
        filepath = os.path.join(UPLOAD_FOLDER, orig_filename)
        file.save(filepath)

        # Store uploaded file in history
        add_history(orig_filename, "audio", user_id)

        # ---------------- Process audio ----------------
        try:
            vocals_path = separate_vocals(filepath)
            clean_path = denoise_audio(vocals_path)
        except Exception as e:
            print("Warning: Spleeter/Noise reduction failed:", e)
            clean_path = filepath  # fallback

        # ---------------- Transcription ----------------
        raw_text = transcribe_audio(clean_path)
        clean_text = clean_tamil_text(raw_text)

        # ---------------- Return result ----------------
        if not clean_text.strip():
            # still empty after fallback
            return jsonify({"text": "", "warning": "No speech detected"}), 200

        return jsonify({"text": clean_text})

    except Exception as e:
        print("TRANSCRIBE ERROR:", e)
        traceback.print_exc()
        return jsonify({"error": f"Transcription failed: {str(e)}"}), 500

@upload_bp.route("/history")
def history():
    """Render history page with only DOCX/PDF converted files grouped by date"""
    try:
        if "user_email" not in session:
            return redirect(url_for("auth.login"))
        
        user = get_user_by_email(session["user_email"])
        if not user:
            return redirect(url_for("auth.login"))

        user_id = user[0]
        print("Logged-in user ID:", user_id)  # ✅ Print user ID to console

        all_records = get_all_history(user_id=user_id)
        records = [r for r in all_records if r[2] in ("docx", "pdf")]

        records_by_date = defaultdict(list)
        for r in records:
            id, filename, filetype, converted_at = r
            date_only = converted_at.split(" ")[0]
            records_by_date[date_only].append([id, filename, filetype, converted_at])

        sorted_records = dict(sorted(records_by_date.items(), reverse=True))

        # Get translations
        translations = {
            "english": {
                "back":"back",
                # "menu": "Menu",
                "dashboard": "Dashboard",
                "history": "History",
                "home": "Home",
                "files": "Files",
                "settings": "Settings",
                "help": "Help",
                "logout": "Logout",
                # "back": "Back",
                "account": "Account",
                "language": "Language",
                "version": "Version",
                "privacy": "Privacy",
                "history": "Converted Files History",
                "converted": "Converted",
                "download": "Download",
                "no_history": "No history found.",
                "select_format": "Select Download Format"
            },
            "tamil": {
                # "menu": "மெனு",
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
                "history": " வரலாறு",
                "converted": "மாற்றிய தேதி",
                "download": "பதிவிறக்கு",
                "no_history": "வரலாறு இல்லை.",
                "select_format": "பதிவிறக்க வடிவத்தைத் தேர்ந்தெடுக்கவும்"
            }
        }


        lang = session.get("lang", "english")
        t = translations.get(lang, translations["english"])

        return render_template("history.html", records_by_date=sorted_records, t=t)

    except Exception as e:
        print("History page error:", e)
        lang = session.get("lang", "english")
        t = translations.get(lang, translations["english"])
        return render_template("history.html", records_by_date={}, t=t)

@upload_bp.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@upload_bp.route("/dashboard")
def dashboard():
    """Render dashboard with counts (cards)"""
    try:
        if "user_email" not in session:
            return redirect(url_for("auth.login"))
        
        user = get_user_by_email(session["user_email"])
        print(user)
        if not user:
            return redirect(url_for("auth.login"))

        user_id = user[0]
        print("Logged-in user ID:", user_id)  # ✅ Print user ID to console

        counts = get_counts(user_id)
        recent = get_all_history(user_id, limit=10)

        # Translations
        translations = {
            "english": {
                "back":"back",
                # "menu": "Menu",
                "dashboard": "Dashboard",
                "history": "History",
                "home": "Home",
                "files": "Files",
                "settings": "Settings",
                "help": "Help",
                "logout": "Logout",
                # "back": "Back",
                "account": "Account",
                "language": "Language",
                "version": "Version",
                "privacy": "Privacy",
                # "history": "History",
                "converted": "Converted",
                "download": "Download",
                "no_history": "No history found.",
                "select_format": "Select Download Format",

                "dashboard_title": "Dashboard",
                "Total Files (all types)":"Total Files (all types)",
                "Audio files uploaded":"Audio files uploaded",
                "Converted (docx/pdf)":"Converted (docx/pdf)",
                "Word (.docx)":"Word (.docx)",
                "PDF (.pdf)":"PDF (.pdf)",                      
                "Recent uploads / conversions":"Recent uploads / conversions",
                "Filename":"Filename",
                "Type":"Type",             
                "Date":"Date",                   
                "Download":"Download",  
                "No history yet":"No history yet"
            

            },
            "tamil": {
                # "menu": "மெனு",
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
                "history": " வரலாறு",
                "converted": "மாற்றிய தேதி",
                "Download": "பதிவிறக்கு",
                "no_history": "வரலாறு இல்லை.",
                "select_format": "பதிவிறக்க வடிவத்தைத் தேர்ந்தெடுக்கவும்",

                "dashboard_title": "கண்காணிப்பு பலகை",
                "Total Files (all types)": "மொத்த கோப்புகள் (எல்லா வகைகள்)",
                "Audio files uploaded":"பதிவேற்றப்பட்ட ஒலி கோப்புகள்",
                "Converted (docx/pdf)":"மாற்றப்பட்டவை (docx/pdf)",
                "Word (.docx)":"Word (.docx)",                
                "PDF (.pdf)":"PDF (.pdf)",              
                "Recent uploads / conversions":"சமீபத்திய பதிவுகள் / மாற்றங்கள் ",
                "Filename":"கோப்பு பெயர்",                    
                "Type":"வகை",                         
                "Date":"தேதி",
                "Download":"பதிவிறக்கு",
                "No history yet":"வரலாறு இல்லை"                  

            }
        }

        lang = session.get("lang", "english")
        t = translations.get(lang, translations["english"])

        return render_template("dashboard.html", counts=counts, recent=recent, t=t)

    except Exception as e:
        print("Dashboard error:", e)
        lang = session.get("lang", "english")
        t = translations.get(lang, translations["english"])
        return render_template("dashboard.html", counts={}, recent=[], t=t)
