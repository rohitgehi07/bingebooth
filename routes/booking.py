import json
import random
import string
import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import current_user, login_required
from extensions import db
from models import Show, Screen, Seat, SeatCategory, SeatLock, Booking, FoodItem, BookingFood, User, LoyaltyPoint, LoyaltyTransaction

booking_bp = Blueprint('booking', __name__)

def generate_booking_code():
    chars = string.ascii_uppercase + string.digits
    code = 'BB' + ''.join(random.choices(chars, k=6))
    while Booking.query.filter_by(booking_code=code).first() is not None:
        code = 'BB' + ''.join(random.choices(chars, k=6))
    return code

@booking_bp.route('/show/<int:show_id>/seats')
def seat_select(show_id):
    show = Show.query.get_or_404(show_id)
    screen = Screen.query.get_or_404(show.screen_id)
    theatre = screen.theatre
    movie = show.movie
    categories = SeatCategory.query.filter_by(show_id=show.id).all()
    
    seats = Seat.query.filter_by(screen_id=screen.id).order_by(Seat.row_label.asc(), Seat.seat_number.asc()).all()
    
    rows_dict = {}
    for s in seats:
        if s.row_label not in rows_dict:
            rows_dict[s.row_label] = []
        rows_dict[s.row_label].append(s)

    now = datetime.datetime.utcnow()
    active_locks = SeatLock.query.filter(
        SeatLock.show_id == show.id,
        SeatLock.status.in_(['held', 'converted']),
        SeatLock.expires_at > now
    ).all()

    held_seat_ids = set()
    sold_seat_ids = set()

    for lock in active_locks:
        if lock.status == 'converted':
            sold_seat_ids.add(lock.seat_id)
        elif lock.status == 'held':
            held_seat_ids.add(lock.seat_id)

    return render_template(
        'seat_select.html',
        show=show,
        screen=screen,
        theatre=theatre,
        movie=movie,
        categories=categories,
        rows_dict=rows_dict,
        held_seat_ids=held_seat_ids,
        sold_seat_ids=sold_seat_ids
    )

@booking_bp.route('/booking/hold', methods=['POST'])
def hold_seats():
    show_id = request.form.get('show_id', type=int)
    seat_ids_str = request.form.get('seat_ids', '')
    seat_labels = request.form.get('seat_labels', '')

    if not show_id or not seat_ids_str:
        flash('Invalid seat selection.', 'error')
        return redirect(url_for('main.index'))

    try:
        seat_ids = [int(s.strip()) for s in seat_ids_str.split(',') if s.strip()]
    except ValueError:
        flash('Invalid seat data received.', 'error')
        return redirect(url_for('main.index'))

    show = Show.query.get_or_404(show_id)
    now = datetime.datetime.utcnow()
    expires_at = now + datetime.timedelta(minutes=4)

    if not current_user.is_authenticated:
        flash('Please log in to continue booking your tickets.', 'info')
        return redirect(url_for('auth.login', next=url_for('booking.seat_select', show_id=show_id)))

    user_id = current_user.id
    session_id = session.get('_id', 'session_guest')

    try:
        conflicting_locks = SeatLock.query.filter(
            SeatLock.show_id == show_id,
            SeatLock.seat_id.in_(seat_ids),
            SeatLock.status.in_(['held', 'converted']),
            SeatLock.expires_at > now
        ).all()

        if conflicting_locks:
            db.session.rollback()
            flash('Sorry! One or more of your selected seats were just taken by another user. Please choose different seats.', 'warning')
            return redirect(url_for('booking.seat_select', show_id=show_id))

        total_ticket_amount = 0.0
        categories = SeatCategory.query.filter_by(show_id=show_id).all()
        selected_seats = Seat.query.filter(Seat.id.in_(seat_ids)).all()

        for s in selected_seats:
            seat_price = show.base_price
            for cat in categories:
                if cat.row_start <= s.row_label <= cat.row_end:
                    seat_price = cat.price
                    break
            total_ticket_amount += seat_price

            lock = SeatLock(
                show_id=show_id,
                seat_id=s.id,
                user_id=user_id,
                session_id=session_id,
                locked_at=now,
                expires_at=expires_at,
                status='held'
            )
            db.session.add(lock)

        convenience_fee = 30.0
        gst = round(0.18 * (total_ticket_amount + convenience_fee), 2)
        grand_total = round(total_ticket_amount + convenience_fee + gst, 2)

        booking = Booking(
            booking_code=generate_booking_code(),
            user_id=user_id,
            show_id=show_id,
            seat_ids_json=json.dumps(seat_ids),
            seats_label=seat_labels,
            ticket_amount=total_ticket_amount,
            food_amount=0.0,
            discount_amount=0.0,
            convenience_fee=convenience_fee,
            gst=gst,
            total_amount=grand_total,
            status='pending',
            created_at=now
        )
        db.session.add(booking)
        db.session.commit()

        session['active_booking_code'] = booking.booking_code
        return redirect(url_for('booking.food_selection', code=booking.booking_code))

    except Exception as e:
        db.session.rollback()
        flash(f'An unexpected error occurred while locking seats: {e}', 'error')
        return redirect(url_for('booking.seat_select', show_id=show_id))

@booking_bp.route('/booking/<code>/food', methods=['GET', 'POST'])
@login_required
def food_selection(code):
    booking = Booking.query.filter_by(booking_code=code, user_id=current_user.id).first_or_404()

    if booking.status in ['expired', 'cancelled']:
        flash('This booking session has expired.', 'warning')
        return redirect(url_for('main.showtimes', slug=booking.show.movie.slug))

    if request.method == 'POST':
        BookingFood.query.filter_by(booking_id=booking.id).delete()
        
        food_items = FoodItem.query.all()
        total_food_amount = 0.0

        for item in food_items:
            qty = request.form.get(f'food_{item.id}', type=int, default=0)
            if qty > 0:
                item_total = qty * item.price
                total_food_amount += item_total
                bf = BookingFood(
                    booking_id=booking.id,
                    food_item_id=item.id,
                    quantity=qty,
                    unit_price=item.price
                )
                db.session.add(bf)

        booking.food_amount = total_food_amount
        subtotal = max(0.0, booking.ticket_amount + booking.food_amount - booking.discount_amount)
        booking.gst = round(0.18 * (subtotal + booking.convenience_fee), 2)
        booking.total_amount = round(subtotal + booking.convenience_fee + booking.gst, 2)

        db.session.commit()
        return redirect(url_for('booking.payment', code=booking.booking_code))

    food_by_category = {
        'Popcorn': FoodItem.query.filter_by(category='Popcorn', is_available=True).all(),
        'Beverages': FoodItem.query.filter_by(category='Beverages', is_available=True).all(),
        'Combos': FoodItem.query.filter_by(category='Combos', is_available=True).all(),
        'Snacks': FoodItem.query.filter_by(category='Snacks', is_available=True).all(),
    }

    elapsed = (datetime.datetime.utcnow() - booking.created_at).total_seconds()
    remaining_seconds = max(0, int(240 - elapsed))

    return render_template(
        'food.html',
        booking=booking,
        food_by_category=food_by_category,
        remaining_seconds=remaining_seconds
    )

@booking_bp.route('/booking/<code>/payment', methods=['GET', 'POST'])
@login_required
def payment(code):
    booking = Booking.query.filter_by(booking_code=code, user_id=current_user.id).first_or_404()

    if booking.status == 'confirmed':
        return redirect(url_for('booking.ticket', code=booking.booking_code))

    if booking.status in ['expired', 'cancelled']:
        flash('Your seat hold timer expired before payment completion.', 'warning')
        return redirect(url_for('main.showtimes', slug=booking.show.movie.slug))

    if request.method == 'POST':
        action = request.form.get('action', 'pay')

        # Handle BingePoints Discount Promo Code Application
        promo_code = request.form.get('promo_code', '').strip().upper()
        if action == 'apply_promo':
            discount = 0.0
            if promo_code == 'POINTS50':
                discount = 50.0
            elif promo_code == 'POINTS100':
                discount = 100.0
            elif promo_code in ['FREEPOPCORN', 'FREEDRINK']:
                discount = 60.0

            if discount > 0:
                booking.discount_amount = discount
                subtotal = max(0.0, booking.ticket_amount + booking.food_amount - discount)
                booking.gst = round(0.18 * (subtotal + booking.convenience_fee), 2)
                booking.total_amount = round(subtotal + booking.convenience_fee + booking.gst, 2)
                db.session.commit()
                flash(f'Promo code {promo_code} applied! ₹{int(discount)} discount added.', 'success')
            else:
                flash('Invalid or expired promo code.', 'error')
            return redirect(url_for('booking.payment', code=booking.booking_code))

        if action == 'simulate_failure':
            seat_ids = json.loads(booking.seat_ids_json)
            SeatLock.query.filter(
                SeatLock.show_id == booking.show_id,
                SeatLock.seat_id.in_(seat_ids),
                SeatLock.user_id == current_user.id
            ).update({'status': 'expired'}, synchronize_session=False)

            booking.status = 'expired'
            db.session.commit()

            flash('Payment simulation failed. Your seats have been released.', 'error')
            return redirect(url_for('main.showtimes', slug=booking.show.movie.slug))

        # Confirm Payment
        now = datetime.datetime.utcnow()
        booking.status = 'confirmed'
        booking.confirmed_at = now

        seat_ids = json.loads(booking.seat_ids_json)
        SeatLock.query.filter(
            SeatLock.show_id == booking.show_id,
            SeatLock.seat_id.in_(seat_ids),
            SeatLock.user_id == current_user.id
        ).update({'status': 'converted'}, synchronize_session=False)

        # NEW FEATURE 3: Award BingePoints (+10 booking, +5 food order, +20 bonus first booking)
        lp = LoyaltyPoint.query.filter_by(user_id=current_user.id).first()
        if not lp:
            lp = LoyaltyPoint(user_id=current_user.id, points_balance=0, lifetime_points_earned=0)
            db.session.add(lp)

        earned_points = 10
        tx_desc = f"Earned 10 BingePoints for booking {len(seat_ids)} ticket(s)"

        if booking.food_amount > 0:
            earned_points += 5
            tx_desc += " + food order"

        # First time booking bonus (+20)
        previous_confirmed = Booking.query.filter_by(user_id=current_user.id, status='confirmed').count()
        if previous_confirmed == 1:
            earned_points += 20
            tx_desc += " (+20 First Booking Bonus! 🎁)"

        lp.points_balance += earned_points
        lp.lifetime_points_earned += earned_points

        tx = LoyaltyTransaction(
            user_id=current_user.id,
            activity_type='booking',
            points_earned=earned_points,
            description=tx_desc
        )
        db.session.add(tx)
        db.session.commit()

        flash(f'Payment successful! Your ticket has been booked (+{earned_points} BingePoints earned! 🎉)', 'success')
        return redirect(url_for('booking.ticket', code=booking.booking_code))

    elapsed = (datetime.datetime.utcnow() - booking.created_at).total_seconds()
    remaining_seconds = max(0, int(240 - elapsed))

    return render_template(
        'payment.html',
        booking=booking,
        remaining_seconds=remaining_seconds
    )

@booking_bp.route('/booking/<code>/ticket')
@login_required
def ticket(code):
    booking = Booking.query.filter_by(booking_code=code).first_or_404()
    if booking.user_id != current_user.id and not current_user.is_admin:
        flash('Unauthorized access to ticket.', 'error')
        return redirect(url_for('main.index'))

    booking_foods = BookingFood.query.filter_by(booking_id=booking.id).all()

    return render_template(
        'ticket.html',
        booking=booking,
        booking_foods=booking_foods
    )
