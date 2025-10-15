from flask import Flask
from config import SECRET_KEY
from models.user_model import init_db
from models.history_model import init_history_table   # ✅ import


def create_app():
    app = Flask(__name__)
    app.secret_key = SECRET_KEY


    # ✅ Initialize both tables
    init_db()              # users table
    init_history_table()   # history table

    from routes.auth_routes import auth_bp
    from routes.main_routes import main_bp
    from routes.upload import upload_bp  
    from routes.settings import settings_bp  # import your blueprint


    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(upload_bp)
    app.register_blueprint(settings_bp)

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
