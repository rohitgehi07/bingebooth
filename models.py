import datetime
import json
from flask_login import UserMixin
from extensions import db

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), nullable=True)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    bookings = db.relationship('Booking', backref='user', lazy=True)
    reviews = db.relationship('Review', backref='user', lazy=True)
    loyalty_points = db.relationship('LoyaltyPoint', backref='user', uselist=False, lazy=True)
    loyalty_transactions = db.relationship('LoyaltyTransaction', backref='user', lazy=True)

class City(db.Model):
    __tablename__ = 'cities'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    state = db.Column(db.String(100), nullable=False)
    is_metro = db.Column(db.Boolean, default=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)

    theatres = db.relationship('Theatre', backref='city', lazy=True, cascade="all, delete-orphan")

class Theatre(db.Model):
    __tablename__ = 'theatres'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    city_id = db.Column(db.Integer, db.ForeignKey('cities.id'), nullable=False)
    address = db.Column(db.Text, nullable=False)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    screen_count = db.Column(db.Integer, default=1)
    amenities = db.Column(db.String(255), default="Parking,F&B,Wheelchair,M-Ticket")

    screens = db.relationship('Screen', backref='theatre', lazy=True, cascade="all, delete-orphan")

class Screen(db.Model):
    __tablename__ = 'screens'
    id = db.Column(db.Integer, primary_key=True)
    theatre_id = db.Column(db.Integer, db.ForeignKey('theatres.id'), nullable=False)
    name = db.Column(db.String(80), nullable=False) # e.g. "Audi 1"
    total_rows = db.Column(db.Integer, default=10)
    seats_per_row = db.Column(db.Integer, default=12)
    layout_json = db.Column(db.Text, nullable=True) # JSON store of layout structure

    seats = db.relationship('Seat', backref='screen', lazy=True, cascade="all, delete-orphan")
    shows = db.relationship('Show', backref='screen', lazy=True, cascade="all, delete-orphan")

class Movie(db.Model):
    __tablename__ = 'movies'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    title_hi = db.Column(db.String(200), nullable=True)
    slug = db.Column(db.String(200), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)
    description_hi = db.Column(db.Text, nullable=True)
    trivia = db.Column(db.Text, nullable=True) # Fun facts for classic/archived movies
    duration_minutes = db.Column(db.Integer, nullable=False)
    genres = db.Column(db.String(200), nullable=False) # Comma-separated: Action, Sci-Fi
    languages = db.Column(db.String(200), nullable=False) # Comma-separated: Hindi, English
    formats = db.Column(db.String(100), default="2D,3D") # 2D, 3D, IMAX
    certificate = db.Column(db.String(20), default="UA") # U, UA, A
    release_date = db.Column(db.Date, nullable=False)
    poster_url = db.Column(db.String(500), nullable=False)
    banner_url = db.Column(db.String(500), nullable=False)
    trailer_youtube_id = db.Column(db.String(100), nullable=False)
    rating = db.Column(db.Float, default=8.5)
    votes_count = db.Column(db.Integer, default=1240)
    cast_json = db.Column(db.Text, nullable=True) # JSON list of {name, role, image}
    crew_json = db.Column(db.Text, nullable=True) # JSON list of {name, role}
    status = db.Column(db.String(30), default='now_showing') # now_showing, upcoming, archived
    is_classic = db.Column(db.Boolean, default=False)

    images = db.relationship('MovieImage', backref='movie', lazy=True, cascade="all, delete-orphan")
    reviews = db.relationship('Review', backref='movie', lazy=True, cascade="all, delete-orphan")
    shows = db.relationship('Show', backref='movie', lazy=True, cascade="all, delete-orphan")

class MovieImage(db.Model):
    __tablename__ = 'movie_images'
    id = db.Column(db.Integer, primary_key=True)
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.id'), nullable=False)
    image_url = db.Column(db.String(500), nullable=False)
    caption = db.Column(db.String(200), nullable=True)

class Review(db.Model):
    __tablename__ = 'reviews'
    id = db.Column(db.Integer, primary_key=True)
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    reviewer_name = db.Column(db.String(120), nullable=False)
    rating = db.Column(db.Float, nullable=False) # 1-10
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class Show(db.Model):
    __tablename__ = 'shows'
    id = db.Column(db.Integer, primary_key=True)
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.id'), nullable=False)
    screen_id = db.Column(db.Integer, db.ForeignKey('screens.id'), nullable=False)
    show_datetime = db.Column(db.DateTime, nullable=False, index=True)
    language = db.Column(db.String(50), default="Hindi")
    format = db.Column(db.String(50), default="2D")
    base_price = db.Column(db.Float, default=200.0)
    status = db.Column(db.String(30), default="open") # open, cancelled, completed

    seat_categories = db.relationship('SeatCategory', backref='show', lazy=True, cascade="all, delete-orphan")
    seat_locks = db.relationship('SeatLock', backref='show', lazy=True, cascade="all, delete-orphan")
    bookings = db.relationship('Booking', backref='show', lazy=True, cascade="all, delete-orphan")

class SeatCategory(db.Model):
    __tablename__ = 'seat_categories'
    id = db.Column(db.Integer, primary_key=True)
    show_id = db.Column(db.Integer, db.ForeignKey('shows.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False) # Recliner, Gold, Silver
    row_start = db.Column(db.String(5), nullable=False) # e.g. "A"
    row_end = db.Column(db.String(5), nullable=False) # e.g. "B"
    price = db.Column(db.Float, nullable=False)

class Seat(db.Model):
    __tablename__ = 'seats'
    id = db.Column(db.Integer, primary_key=True)
    screen_id = db.Column(db.Integer, db.ForeignKey('screens.id'), nullable=False)
    row_label = db.Column(db.String(5), nullable=False) # e.g. "A"
    seat_number = db.Column(db.Integer, nullable=False) # e.g. 5
    seat_type = db.Column(db.String(30), default="normal") # normal, aisle_gap, blocked, couple

    seat_locks = db.relationship('SeatLock', backref='seat', lazy=True, cascade="all, delete-orphan")

class SeatLock(db.Model):
    __tablename__ = 'seat_locks'
    id = db.Column(db.Integer, primary_key=True)
    show_id = db.Column(db.Integer, db.ForeignKey('shows.id'), nullable=False)
    seat_id = db.Column(db.Integer, db.ForeignKey('seats.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    session_id = db.Column(db.String(100), nullable=False)
    locked_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False, index=True)
    status = db.Column(db.String(30), default='held') # held, converted, expired

    __table_args__ = (
        db.Index('idx_show_seat_held', 'show_id', 'seat_id', sqlite_where=(status == 'held')),
    )

class Booking(db.Model):
    __tablename__ = 'bookings'
    id = db.Column(db.Integer, primary_key=True)
    booking_code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    show_id = db.Column(db.Integer, db.ForeignKey('shows.id'), nullable=False)
    seat_ids_json = db.Column(db.Text, nullable=False) # JSON array of seat IDs
    seats_label = db.Column(db.String(200), nullable=False) # e.g. "C5, C6"
    ticket_amount = db.Column(db.Float, nullable=False)
    food_amount = db.Column(db.Float, default=0.0)
    discount_amount = db.Column(db.Float, default=0.0) # BingePoints discount applied
    convenience_fee = db.Column(db.Float, default=30.0)
    gst = db.Column(db.Float, default=18.0)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(30), default='pending') # pending, confirmed, cancelled, expired
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    confirmed_at = db.Column(db.DateTime, nullable=True)

    booking_foods = db.relationship('BookingFood', backref='booking', lazy=True, cascade="all, delete-orphan")

class FoodItem(db.Model):
    __tablename__ = 'food_items'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(50), nullable=False) # Popcorn, Beverages, Combos, Snacks
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(500), nullable=False)
    is_veg = db.Column(db.Boolean, default=True)
    is_available = db.Column(db.Boolean, default=True)

class BookingFood(db.Model):
    __tablename__ = 'booking_food'
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False)
    food_item_id = db.Column(db.Integer, db.ForeignKey('food_items.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Float, nullable=False)

    food_item = db.relationship('FoodItem', lazy='joined')

class ChatLog(db.Model):
    __tablename__ = 'chat_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    session_id = db.Column(db.String(100), nullable=True)
    message = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

# NEW FIX 4: Site Traffic Analytics Table
class PageVisit(db.Model):
    __tablename__ = 'page_visits'
    id = db.Column(db.Integer, primary_key=True)
    path = db.Column(db.String(500), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    session_id = db.Column(db.String(100), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(300), nullable=True)
    referrer = db.Column(db.String(500), nullable=True)
    visited_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, index=True)

# NEW FEATURE 3: Loyalty & Rewards Tables
class LoyaltyPoint(db.Model):
    __tablename__ = 'loyalty_points'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    points_balance = db.Column(db.Integer, default=0)
    lifetime_points_earned = db.Column(db.Integer, default=0)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class LoyaltyTransaction(db.Model):
    __tablename__ = 'loyalty_transactions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    activity_type = db.Column(db.String(40), nullable=False) # booking, food_order, review, bonus, redemption
    points_earned = db.Column(db.Integer, nullable=False) # positive for gain, negative for redemption
    description = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

# FEATURE A: Watch Party Tables
class WatchParty(db.Model):
    __tablename__ = 'watch_parties'
    id = db.Column(db.Integer, primary_key=True)
    party_code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    show_id = db.Column(db.Integer, db.ForeignKey('shows.id'), nullable=False)
    host_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='active') # active, closed

    show = db.relationship('Show', lazy='joined')
    votes = db.relationship('WatchPartyVote', backref='party', lazy=True, cascade="all, delete-orphan")

class WatchPartyVote(db.Model):
    __tablename__ = 'watch_party_votes'
    id = db.Column(db.Integer, primary_key=True)
    party_id = db.Column(db.Integer, db.ForeignKey('watch_parties.id'), nullable=False)
    seat_id = db.Column(db.Integer, db.ForeignKey('seats.id'), nullable=False)
    voter_name = db.Column(db.String(100), nullable=False)
    voted_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    seat = db.relationship('Seat', lazy='joined')

# NEW FEATURE: Pre-show Trivia Mini-Quiz Table
class TriviaQuestion(db.Model):
    __tablename__ = 'trivia_questions'
    id = db.Column(db.Integer, primary_key=True)
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.id'), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.String(255), nullable=False)
    option_b = db.Column(db.String(255), nullable=False)
    option_c = db.Column(db.String(255), nullable=False)
    correct_option = db.Column(db.String(10), nullable=False) # 'a', 'b', 'c'
    points_reward = db.Column(db.Integer, default=5)

    movie = db.relationship('Movie', backref=db.backref('trivia_questions', lazy=True, cascade="all, delete-orphan"))


