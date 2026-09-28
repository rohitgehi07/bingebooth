from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from apscheduler.schedulers.background import BackgroundScheduler

db = SQLAlchemy()
login_manager = LoginManager()
scheduler = BackgroundScheduler(daemon=True)

login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'
