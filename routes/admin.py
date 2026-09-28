import json
from functools import wraps
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import User, Movie, Theatre, Screen, Show, Booking, SeatCategory, SeatLock, FoodItem, Review, PageVisit, BookingFood, Seat, TriviaQuestion

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Admin privilege required.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

# NEW FEATURE 4: "Cinema Intelligence" Business Analytics Dashboard
@admin_bp.route('/')
@admin_bp.route('/intelligence')
@login_required
@admin_required
def dashboard():
    now = datetime.utcnow()
    today_start = datetime.combine(now.date(), datetime.min.time())

    # Live computed statistics
    total_revenue = db.session.query(db.func.sum(Booking.total_amount)).filter(Booking.status == 'confirmed').scalar() or 0.0
    today_revenue = db.session.query(db.func.sum(Booking.total_amount)).filter(Booking.status == 'confirmed', Booking.created_at >= today_start).scalar() or 0.0
    
    total_bookings = Booking.query.filter_by(status='confirmed').count()
    today_bookings = Booking.query.filter(Booking.created_at >= today_start, Booking.status == 'confirmed').count()
    
    total_users = User.query.count()
    active_holds = SeatLock.query.filter_by(status='held').count()

    total_shows = Show.query.count()
    total_confirmed_seats = db.session.query(SeatLock).filter_by(status='converted').count()
    occupancy_rate = round((total_confirmed_seats / (total_shows * 100)) * 100, 1) if total_shows > 0 else 0.0

    # Most booked movie
    most_booked_query = db.session.query(
        Movie.title,
        db.func.count(Booking.id).label('bcount')
    ).join(Show, Show.movie_id == Movie.id)\
     .join(Booking, Booking.show_id == Show.id)\
     .filter(Booking.status == 'confirmed')\
     .group_by(Movie.id)\
     .order_by(db.desc('bcount')).first()

    most_booked_movie = most_booked_query[0] if most_booked_query else "N/A"

    # Most ordered food item
    most_ordered_food_query = db.session.query(
        FoodItem.name,
        db.func.sum(BookingFood.quantity).label('qsum')
    ).join(BookingFood, BookingFood.food_item_id == FoodItem.id)\
     .group_by(FoodItem.id)\
     .order_by(db.desc('qsum')).first()

    most_ordered_food = most_ordered_food_query[0] if most_ordered_food_query else "Salted Popcorn"

    # Peak showtime calculation
    shows = Show.query.all()
    slot_counts = {"Morning": 0, "Afternoon": 0, "Evening": 0, "Night": 0}
    for s in shows:
        hour = s.show_datetime.hour
        b_cnt = Booking.query.filter_by(show_id=s.id, status='confirmed').count()
        if hour < 12:
            slot_counts["Morning"] += b_cnt
        elif hour < 16:
            slot_counts["Afternoon"] += b_cnt
        elif hour < 20:
            slot_counts["Evening"] += b_cnt
        else:
            slot_counts["Night"] += b_cnt

    peak_slot = max(slot_counts, key=slot_counts.get) if any(slot_counts.values()) else "Evening (07:10 PM)"

    # 14-Day Revenue & Bookings Line Charts Data
    dates = []
    revenue_data = []
    bookings_data = []
    for i in range(13, -1, -1):
        day = now.date() - timedelta(days=i)
        dates.append(day.strftime('%b %d'))
        day_start = datetime.combine(day, datetime.min.time())
        day_end = datetime.combine(day, datetime.max.time())
        
        rev = db.session.query(db.func.sum(Booking.total_amount)).filter(
            Booking.status == 'confirmed',
            Booking.created_at >= day_start,
            Booking.created_at <= day_end
        ).scalar() or 0.0
        revenue_data.append(round(rev, 2))

        cnt = Booking.query.filter(
            Booking.status == 'confirmed',
            Booking.created_at >= day_start,
            Booking.created_at <= day_end
        ).count()
        bookings_data.append(cnt)

    # Top Performing Movies Table
    top_movies = db.session.query(
        Movie.title,
        Movie.rating,
        db.func.count(Booking.id).label('b_count'),
        db.func.sum(Booking.total_amount).label('rev')
    ).join(Show, Show.movie_id == Movie.id)\
     .join(Booking, Booking.show_id == Show.id)\
     .filter(Booking.status == 'confirmed')\
     .group_by(Movie.id)\
     .order_by(db.desc('rev')).limit(5).all()

    top_movie_labels = [m[0] for m in top_movies]
    top_movie_values = [round(m[3], 2) for m in top_movies]

    recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(8).all()

    return render_template(
        'admin/dashboard.html',
        total_revenue=round(total_revenue, 2),
        today_revenue=round(today_revenue, 2),
        total_bookings=total_bookings,
        today_bookings=today_bookings,
        total_users=total_users,
        occupancy_rate=occupancy_rate,
        active_holds=active_holds,
        most_booked_movie=most_booked_movie,
        most_ordered_food=most_ordered_food,
        peak_slot=peak_slot,
        slot_counts=slot_counts,
        recent_bookings=recent_bookings,
        top_movies=top_movies,
        chart_dates=json.dumps(dates),
        chart_revenue=json.dumps(revenue_data),
        chart_bookings=json.dumps(bookings_data),
        top_movie_labels=json.dumps(top_movie_labels),
        top_movie_values=json.dumps(top_movie_values)
    )

# FIX 4: "Site Activity" Traffic Analytics Admin Panel
@admin_bp.route('/site-activity')
@login_required
@admin_required
def site_activity():
    now = datetime.utcnow()
    today_start = datetime.combine(now.date(), datetime.min.time())
    week_start = now - timedelta(days=7)

    total_visits_all_time = PageVisit.query.count()
    visits_today = PageVisit.query.filter(PageVisit.visited_at >= today_start).count()
    visits_this_week = PageVisit.query.filter(PageVisit.visited_at >= week_start).count()

    unique_sessions = db.session.query(db.func.count(db.func.distinct(PageVisit.session_id))).scalar() or 0

    # 14-Day Traffic Visits Line Chart Data
    dates = []
    visit_counts = []
    for i in range(13, -1, -1):
        day = now.date() - timedelta(days=i)
        dates.append(day.strftime('%b %d'))
        day_start = datetime.combine(day, datetime.min.time())
        day_end = datetime.combine(day, datetime.max.time())
        
        cnt = PageVisit.query.filter(
            PageVisit.visited_at >= day_start,
            PageVisit.visited_at <= day_end
        ).count()
        visit_counts.append(cnt)

    # Top Visited Pages Table
    top_pages = db.session.query(
        PageVisit.path,
        db.func.count(PageVisit.id).label('visit_cnt')
    ).group_by(PageVisit.path).order_by(db.desc('visit_cnt')).limit(8).all()

    # Recent 30 Visits Activity Feed
    recent_visits = PageVisit.query.order_by(PageVisit.visited_at.desc()).limit(30).all()

    # Parse simple device type from User-Agent
    for v in recent_visits:
        ua = (v.user_agent or '').lower()
        if 'mobile' in ua or 'android' in ua or 'iphone' in ua:
            v.device_type = '📱 Mobile'
        elif 'tablet' in ua or 'ipad' in ua:
            v.device_type = '💻 Tablet'
        else:
            v.device_type = '🖥️ Desktop'

    return render_template(
        'admin/site_activity.html',
        total_visits_all_time=total_visits_all_time,
        visits_today=visits_today,
        visits_this_week=visits_this_week,
        unique_sessions=unique_sessions,
        chart_dates=json.dumps(dates),
        chart_visits=json.dumps(visit_counts),
        top_pages=top_pages,
        recent_visits=recent_visits
    )

@admin_bp.route('/movies', methods=['GET', 'POST'])
@login_required
@admin_required
def movies():
    if request.method == 'POST':
        action = request.form.get('action', 'add')
        if action == 'add':
            title = request.form.get('title')
            title_hi = request.form.get('title_hi')
            slug = request.form.get('slug') or title.lower().replace(' ', '-').replace(':', '')
            description = request.form.get('description')
            description_hi = request.form.get('description_hi')
            trivia = request.form.get('trivia')
            duration_minutes = int(request.form.get('duration_minutes', 120))
            genres = request.form.get('genres', 'Action, Drama')
            languages = request.form.get('languages', 'Hindi, English')
            formats = request.form.get('formats', '2D, 3D')
            certificate = request.form.get('certificate', 'UA')
            release_date = datetime.strptime(request.form.get('release_date'), '%Y-%m-%d').date()
            poster_url = request.form.get('poster_url')
            banner_url = request.form.get('banner_url')
            trailer_youtube_id = request.form.get('trailer_youtube_id', 'dQw4w9WgXcQ')
            status = request.form.get('status', 'now_showing')
            is_classic = True if request.form.get('is_classic') else False

            movie = Movie(
                title=title,
                title_hi=title_hi,
                slug=slug,
                description=description,
                description_hi=description_hi,
                trivia=trivia,
                duration_minutes=duration_minutes,
                genres=genres,
                languages=languages,
                formats=formats,
                certificate=certificate,
                release_date=release_date,
                poster_url=poster_url,
                banner_url=banner_url,
                trailer_youtube_id=trailer_youtube_id,
                status=status,
                is_classic=is_classic
            )
            db.session.add(movie)
            db.session.commit()
            flash('Movie saved successfully!', 'success')

        elif action == 'delete':
            movie_id = request.form.get('movie_id', type=int)
            movie = Movie.query.get_or_404(movie_id)
            db.session.delete(movie)
            db.session.commit()
            flash('Movie deleted successfully.', 'info')

        return redirect(url_for('admin.movies'))

    all_movies = Movie.query.order_by(Movie.id.desc()).all()
    return render_template('admin/movies.html', movies=all_movies)

@admin_bp.route('/theatres', methods=['GET', 'POST'])
@login_required
@admin_required
def theatres():
    if request.method == 'POST':
        action = request.form.get('action', 'add')
        if action == 'add':
            name = request.form.get('name')
            city_id = request.form.get('city_id', type=int)
            address = request.form.get('address')
            amenities = request.form.get('amenities', 'Parking,F&B,Wheelchair,M-Ticket')

            t = Theatre(name=name, city_id=city_id, address=address, amenities=amenities)
            db.session.add(t)
            db.session.commit()

            screen = Screen(theatre_id=t.id, name="Audi 1", total_rows=10, seats_per_row=12)
            db.session.add(screen)
            db.session.commit()

            flash('Theatre and screen created successfully!', 'success')

        elif action == 'delete':
            theatre_id = request.form.get('theatre_id', type=int)
            t = Theatre.query.get_or_404(theatre_id)
            db.session.delete(t)
            db.session.commit()
            flash('Theatre deleted.', 'info')

        return redirect(url_for('admin.theatres'))

    all_theatres = Theatre.query.all()
    from models import City
    cities = City.query.all()
    return render_template('admin/theatres.html', theatres=all_theatres, cities=cities)

@admin_bp.route('/shows', methods=['GET', 'POST'])
@login_required
@admin_required
def shows():
    if request.method == 'POST':
        action = request.form.get('action', 'add')
        if action == 'add':
            movie_id = request.form.get('movie_id', type=int)
            screen_id = request.form.get('screen_id', type=int)
            show_dt = datetime.strptime(request.form.get('show_datetime'), '%Y-%m-%dT%H:%M')
            language = request.form.get('language', 'Hindi')
            format_type = request.form.get('format', '2D')
            base_price = float(request.form.get('base_price', 200.0))

            show = Show(
                movie_id=movie_id,
                screen_id=screen_id,
                show_datetime=show_dt,
                language=language,
                format=format_type,
                base_price=base_price,
                status='open'
            )
            db.session.add(show)
            db.session.commit()

            sc1 = SeatCategory(show_id=show.id, name="Recliner", row_start="A", row_end="B", price=base_price * 2.2)
            sc2 = SeatCategory(show_id=show.id, name="Gold", row_start="C", row_end="H", price=base_price * 1.25)
            sc3 = SeatCategory(show_id=show.id, name="Silver", row_start="I", row_end="N", price=base_price)
            db.session.add_all([sc1, sc2, sc3])
            db.session.commit()

            flash('Show scheduled successfully!', 'success')

        elif action == 'delete':
            show_id = request.form.get('show_id', type=int)
            s = Show.query.get_or_404(show_id)
            db.session.delete(s)
            db.session.commit()
            flash('Show cancelled/deleted.', 'info')

        return redirect(url_for('admin.shows'))

    all_shows = Show.query.order_by(Show.show_datetime.desc()).all()
    all_movies = Movie.query.all()
    all_screens = Screen.query.all()
    return render_template('admin/shows.html', shows=all_shows, movies=all_movies, screens=all_screens)

@admin_bp.route('/bookings')
@login_required
@admin_required
def bookings():
    q = request.args.get('q', '')
    query = Booking.query
    if q:
        query = query.filter(
            (Booking.booking_code.ilike(f'%{q}%')) |
            (Booking.seats_label.ilike(f'%{q}%'))
        )
    all_bookings = query.order_by(Booking.created_at.desc()).all()
    return render_template('admin/bookings.html', bookings=all_bookings, q=q)

@admin_bp.route('/users', methods=['GET', 'POST'])
@login_required
@admin_required
def users():
    if request.method == 'POST':
        user_id = request.form.get('user_id', type=int)
        u = User.query.get_or_404(user_id)
        if u.id != current_user.id:
            u.is_admin = not u.is_admin
            db.session.commit()
            flash(f'Admin status updated for {u.name}.', 'success')

    all_users = User.query.all()
    return render_template('admin/users.html', users=all_users)


@admin_bp.route('/trivia', methods=['GET', 'POST'])
@login_required
@admin_required
def trivia():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            movie_id = request.form.get('movie_id', type=int)
            q_text = request.form.get('question_text', '').strip()
            opt_a = request.form.get('option_a', '').strip()
            opt_b = request.form.get('option_b', '').strip()
            opt_c = request.form.get('option_c', '').strip()
            correct = request.form.get('correct_option', 'a').strip().lower()
            pts = request.form.get('points_reward', type=int, default=5)

            if movie_id and q_text and opt_a and opt_b and opt_c:
                tq = TriviaQuestion(
                    movie_id=movie_id,
                    question_text=q_text,
                    option_a=opt_a,
                    option_b=opt_b,
                    option_c=opt_c,
                    correct_option=correct,
                    points_reward=pts
                )
                db.session.add(tq)
                db.session.commit()
                flash('Trivia question added successfully!', 'success')
            else:
                flash('All fields are required.', 'error')

        elif action == 'delete':
            tq_id = request.form.get('trivia_id', type=int)
            tq = TriviaQuestion.query.get_or_404(tq_id)
            db.session.delete(tq)
            db.session.commit()
            flash('Trivia question deleted.', 'info')

        return redirect(url_for('admin.trivia'))

    all_trivia = TriviaQuestion.query.order_by(TriviaQuestion.id.desc()).all()
    all_movies = Movie.query.order_by(Movie.title.asc()).all()
    return render_template('admin/trivia.html', trivia_questions=all_trivia, movies=all_movies)

