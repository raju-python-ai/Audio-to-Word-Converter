import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(BASE_DIR, "app.db")
SECRET_KEY = os.urandom(24)
