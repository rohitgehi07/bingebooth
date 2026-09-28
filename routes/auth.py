from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db
from models import User, Booking, SeatLock, LoyaltyPoint, LoyaltyTransaction

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not name or not email or not password:
            flash('Please fill in all required fields.', 'error')
            return render_template('auth/register.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('auth/register.html')

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email address is already registered. Please sign in.', 'warning')
            return redirect(url_for('auth.login'))

        hashed = generate_password_hash(password, method='scrypt')
        new_user = User(
            name=name,
            email=email,
            phone=phone,
            password_hash=hashed,
            is_admin=False
        )
        db.session.add(new_user)
        db.session.flush()

        # Initialize Loyalty Points Account
        lp = LoyaltyPoint(user_id=new_user.id, points_balance=0, lifetime_points_earned=0)
        db.session.add(lp)
        db.session.commit()

        login_user(new_user)
        flash(f'Welcome to BingeBooth, {name}!', 'success')
        return redirect(url_for('main.index'))

    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = True if request.form.get('remember') else False

        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password_hash, password):
            flash('Invalid email or password. Please try again.', 'error')
            return render_template('auth/login.html')

        login_user(user, remember=remember)
        flash(f'Welcome back, {user.name}!', 'success')
        next_page = request.args.get('next')
        return redirect(next_page or url_for('main.index'))

    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))

@auth_bp.route('/profile')
@login_required
def profile():
    now = datetime.utcnow()
    user_bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.created_at.desc()).all()

    upcoming_bookings = []
    past_bookings = []

    for b in user_bookings:
        can_cancel = False
        if b.show and b.status == 'confirmed':
            time_diff = b.show.show_datetime - now
            if time_diff > timedelta(hours=2):
                can_cancel = True

        b.can_cancel = can_cancel
        if b.show and b.show.show_datetime >= now and b.status == 'confirmed':
            upcoming_bookings.append(b)
        else:
            past_bookings.append(b)

    # NEW FEATURE 3: Loyalty Account Data
    lp = LoyaltyPoint.query.filter_by(user_id=current_user.id).first()
    if not lp:
        lp = LoyaltyPoint(user_id=current_user.id, points_balance=0, lifetime_points_earned=0)
        db.session.add(lp)
        db.session.commit()

    loyalty_txs = LoyaltyTransaction.query.filter_by(user_id=current_user.id).order_by(LoyaltyTransaction.created_at.desc()).limit(10).all()

    # Calculate progress toward next tier (100 pts)
    next_reward_target = 100
    progress_percentage = min(100, int((lp.points_balance % next_reward_target) / float(next_reward_target) * 100))

    return render_template(
        'auth/profile.html',
        upcoming_bookings=upcoming_bookings,
        past_bookings=past_bookings,
        loyalty_point=lp,
        loyalty_transactions=loyalty_txs,
        progress_percentage=progress_percentage
    )

@auth_bp.route('/booking/cancel/<int:booking_id>', methods=['POST'])
@login_required
def cancel_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.user_id != current_user.id and not current_user.is_admin:
        flash('Unauthorized action.', 'error')
        return redirect(url_for('auth.profile'))

    now = datetime.utcnow()
    if booking.show and (booking.show.show_datetime - now) < timedelta(hours=2):
        flash('Bookings can only be cancelled at least 2 hours before showtime.', 'error')
        return redirect(url_for('auth.profile'))

    booking.status = 'cancelled'

    # Release held or converted seat locks for this booking
    locks = SeatLock.query.filter_by(show_id=booking.show_id, user_id=booking.user_id).all()
    for l in locks:
        l.status = 'expired'

    # Deduct loyalty points if confirmed booking was cancelled
    lp = LoyaltyPoint.query.filter_by(user_id=booking.user_id).first()
    if lp and lp.points_balance >= 10:
        lp.points_balance -= 10
        tx = LoyaltyTransaction(
            user_id=booking.user_id,
            activity_type='cancellation',
            points_earned=-10,
            description=f"Deducted 10 BingePoints for booking cancellation ({booking.booking_code})"
        )
        db.session.add(tx)

    db.session.commit()
    flash(f'Booking {booking.booking_code} cancelled successfully. Refund initiated.', 'success')
    return redirect(url_for('auth.profile'))
