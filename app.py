import os
import json
import datetime
from flask import Flask, session, g, request
from flask_login import current_user
from extensions import db, login_manager, scheduler
from models import User, SeatLock, Booking, PageVisit

def load_translations(lang):
    path = os.path.join(os.path.dirname(__file__), 'translations', f'{lang}.json')
    if not os.path.exists(path):
        path = os.path.join(os.path.dirname(__file__), 'translations', 'en.json')
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

def cleanup_expired_holds(app):
    """Background task to release expired seat locks every 30 seconds."""
    with app.app_context():
        try:
            now = datetime.datetime.utcnow()
            # 1. Expire locks
            expired_locks = SeatLock.query.filter(
                SeatLock.status == 'held',
                SeatLock.expires_at <= now
            ).all()
            for lock in expired_locks:
                lock.status = 'expired'
            
            # 2. Expire pending bookings older than 4 minutes
            cutoff = now - datetime.timedelta(minutes=4)
            expired_bookings = Booking.query.filter(
                Booking.status == 'pending',
                Booking.created_at <= cutoff
            ).all()
            for booking in expired_bookings:
                booking.status = 'expired'
                
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"[Scheduler] Error cleaning up expired holds: {e}")

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    os.makedirs(app.instance_path, exist_ok=True)
    
    app.config['SECRET_KEY'] = 'bingebooth_secret_key_college_project_2026'
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(app.instance_path, 'bingebooth.db')}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize Extensions
    db.init_app(app)
    login_manager.init_app(app)
    
    # Flask-Login User Loader
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # FIX 4: Site Traffic Page View Logging Middleware
    @app.before_request
    def log_page_visit():
        # Exclude static assets and high-frequency background API calls
        p = request.path
        if p.startswith('/static/') or p.startswith('/favicon.ico'):
            return
        if '/seat-status' in p or p == '/api/chat':
            return
            
        try:
            u_id = current_user.id if current_user.is_authenticated else None
            sess_id = session.get('_id') or session.get('session_id') or 'guest'
            ip = request.remote_addr or '127.0.0.1'
            ua = request.headers.get('User-Agent', '')[:300]
            ref = request.referrer[:500] if request.referrer else None

            visit = PageVisit(
                path=p[:500],
                user_id=u_id,
                session_id=sess_id,
                ip_address=ip,
                user_agent=ua,
                referrer=ref,
                visited_at=datetime.datetime.utcnow()
            )
            db.session.add(visit)
            db.session.commit()
        except Exception:
            db.session.rollback()

    # Jinja Translation Helper
    @app.context_processor
    def inject_helpers():
        current_lang = session.get('lang', 'en')
        translations = load_translations(current_lang)
        
        def t(key, default=None):
            return translations.get(key, default or key)
            
        def current_city_name():
            return session.get('city_name', 'Mumbai')
            
        return dict(
            t=t,
            current_lang=current_lang,
            current_city=current_city_name(),
            json_loads=json.loads
        )

    # Register Blueprints
    from routes.main import main_bp
    from routes.auth import auth_bp
    from routes.booking import booking_bp
    from routes.admin import admin_bp
    from routes.api import api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(booking_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(api_bp, url_prefix='/api')

    # Start APScheduler for background seat lock cleanup
    if not scheduler.running:
        scheduler.add_job(
            func=cleanup_expired_holds,
            args=[app],
            trigger="interval",
            seconds=30,
            id="cleanup_expired_holds_job",
            replace_existing=True
        )
        scheduler.start()

    return app
