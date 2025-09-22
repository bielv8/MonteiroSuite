import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    # Database configuration
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        app.config["SQLALCHEMY_DATABASE_URI"] = database_url
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
            "pool_recycle": 300,
            "pool_pre_ping": True,
        }
    else:
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///instance/monteiro_lite.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'login'  # type: ignore
    login_manager.login_message = 'Por favor, faça login para acessar esta página.'
    login_manager.login_message_category = 'info'
    
    with app.app_context():
        # Import models to ensure tables are created
        import models
        db.create_all()
        
        # Create default admin user if it doesn't exist
        from models import User
        from werkzeug.security import generate_password_hash
        
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User()
            admin.username = 'admin'
            admin.email = 'admin@monteirocorretora.com'
            admin.name = 'Administrador'
            admin.role = 'admin'
            admin.password_hash = generate_password_hash('admin123')
            
            db.session.add(admin)
            db.session.commit()
            logging.info("Default admin user created: admin/admin123")
    
    return app

app = create_app()

# Import routes after app is created to avoid circular import
import routes

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))
