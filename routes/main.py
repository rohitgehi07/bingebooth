import json
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from flask_login import current_user
from extensions import db
from models import Movie, City, Theatre, Screen, Show, Review, LoyaltyPoint, LoyaltyTransaction

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    active_city_name = session.get('city_name', 'Mumbai')
    active_city = City.query.filter_by(name=active_city_name).first()
    if not active_city:
        active_city = City.query.filter_by(name='Mumbai').first()
        session['city_id'] = active_city.id if active_city else 1
        session['city_name'] = active_city.name if active_city else 'Mumbai'

    # Filter movies showing in current city
    if active_city:
        theatre_ids = [t.id for t in Theatre.query.filter_by(city_id=active_city.id).all()]
        screen_ids = [s.id for s in Screen.query.filter(Screen.theatre_id.in_(theatre_ids)).all()] if theatre_ids else []
        showing_movie_ids = db.session.query(Show.movie_id).filter(Show.screen_id.in_(screen_ids)).distinct().all() if screen_ids else []
        showing_movie_ids = [m[0] for m in showing_movie_ids]
    else:
        showing_movie_ids = []

    # Movies queries
    if showing_movie_ids:
        now_showing = Movie.query.filter(Movie.id.in_(showing_movie_ids), Movie.status == 'now_showing', Movie.is_classic == False).all()
    else:
        now_showing = Movie.query.filter_by(status='now_showing', is_classic=False).all()

    upcoming = Movie.query.filter_by(status='upcoming').order_by(Movie.release_date.asc()).all()
    classics = Movie.query.filter_by(is_classic=True).all()
    hero_featured = Movie.query.filter_by(status='now_showing', is_classic=False).order_by(Movie.rating.desc()).limit(5).all()

    all_genres = set()
    all_languages = set()
    for m in Movie.query.all():
        for g in m.genres.split(','):
            all_genres.add(g.strip())
        for l in m.languages.split(','):
            all_languages.add(l.strip())

    return render_template(
        'index.html',
        now_showing=now_showing,
        upcoming=upcoming,
        classics=classics,
        hero_featured=hero_featured,
        genres=sorted(list(all_genres)),
        languages=sorted(list(all_languages)),
        active_city=active_city_name
    )

# FIX 5: Classics Archive Top-Level Page
@main_bp.route('/classics')
def classics():
    classics_list = Movie.query.filter_by(is_classic=True).order_by(Movie.release_date.asc()).all()
    return render_template('classics.html', classics=classics_list)

# FIX 5: Read-Only Classic Movie Detail View
@main_bp.route('/movie/classic/<slug>')
def classic_detail(slug):
    movie = Movie.query.filter_by(slug=slug, is_classic=True).first_or_404()
    
    cast = json.loads(movie.cast_json) if movie.cast_json else []
    crew = json.loads(movie.crew_json) if movie.crew_json else []
    reviews = Review.query.filter_by(movie_id=movie.id).order_by(Review.created_at.desc()).all()
    images = movie.images

    return render_template(
        'classic_detail.html',
        movie=movie,
        cast=cast,
        crew=crew,
        reviews=reviews,
        images=images
    )

@main_bp.route('/movie/<slug>')
def movie_detail(slug):
    movie = Movie.query.filter_by(slug=slug).first_or_404()
    if movie.is_classic:
        return redirect(url_for('main.classic_detail', slug=movie.slug))

    cast = json.loads(movie.cast_json) if movie.cast_json else []
    crew = json.loads(movie.crew_json) if movie.crew_json else []
    reviews = Review.query.filter_by(movie_id=movie.id).order_by(Review.created_at.desc()).all()
    images = movie.images
    similar_movies = Movie.query.filter(Movie.id != movie.id, Movie.status == 'now_showing', Movie.is_classic == False).limit(4).all()

    return render_template(
        'movie_detail.html',
        movie=movie,
        cast=cast,
        crew=crew,
        reviews=reviews,
        images=images,
        similar_movies=similar_movies
    )

@main_bp.route('/movie/<slug>/shows')
def showtimes(slug):
    movie = Movie.query.filter_by(slug=slug).first_or_404()
    if movie.is_classic:
        flash('Classic archive movies are not currently screening in theatres.', 'info')
        return redirect(url_for('main.classic_detail', slug=movie.slug))

    active_city_name = session.get('city_name', 'Mumbai')
    active_city = City.query.filter_by(name=active_city_name).first()
    
    selected_date_str = request.args.get('date', datetime.utcnow().strftime('%Y-%m-%d'))
    try:
        selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
    except ValueError:
        selected_date = datetime.utcnow().date()
        selected_date_str = selected_date.strftime('%Y-%m-%d')

    today = datetime.utcnow().date()
    date_strip = []
    for i in range(7):
        d = today + timedelta(days=i)
        date_strip.append({
            'date_str': d.strftime('%Y-%m-%d'),
            'day': d.strftime('%a'),
            'date_num': d.strftime('%d'),
            'month': d.strftime('%b'),
            'is_selected': d == selected_date
        })

    if active_city:
        theatres = Theatre.query.filter_by(city_id=active_city.id).all()
    else:
        theatres = Theatre.query.all()

    start_dt = datetime.combine(selected_date, datetime.min.time())
    end_dt = datetime.combine(selected_date, datetime.max.time())

    theatre_shows = []
    for t in theatres:
        screens = Screen.query.filter_by(theatre_id=t.id).all()
        screen_ids = [s.id for s in screens]
        if not screen_ids:
            continue

        shows = Show.query.filter(
            Show.movie_id == movie.id,
            Show.screen_id.in_(screen_ids),
            Show.show_datetime >= start_dt,
            Show.show_datetime <= end_dt
        ).order_by(Show.show_datetime.asc()).all()

        if shows:
            theatre_shows.append({
                'theatre': t,
                'shows': shows
            })

    return render_template(
        'showtimes.html',
        movie=movie,
        date_strip=date_strip,
        selected_date_str=selected_date_str,
        theatre_shows=theatre_shows,
        active_city=active_city_name
    )

@main_bp.route('/movie/<int:movie_id>/review', methods=['POST'])
def add_review(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    rating = float(request.form.get('rating', 8.0))
    title = request.form.get('title', 'Great movie!')
    body = request.form.get('body', '')
    reviewer_name = current_user.name if current_user.is_authenticated else request.form.get('reviewer_name', 'Anonymous')
    
    review = Review(
        movie_id=movie.id,
        user_id=current_user.id if current_user.is_authenticated else None,
        reviewer_name=reviewer_name,
        rating=rating,
        title=title,
        body=body
    )
    db.session.add(review)
    
    # Recalculate movie average rating
    all_reviews = Review.query.filter_by(movie_id=movie.id).all()
    total_rating = sum(r.rating for r in all_reviews) + rating
    movie.votes_count += 1
    movie.rating = round(total_rating / movie.votes_count, 1)

    # NEW FEATURE 3: Award +15 BingePoints for writing a review
    if current_user.is_authenticated:
        lp = LoyaltyPoint.query.filter_by(user_id=current_user.id).first()
        if not lp:
            lp = LoyaltyPoint(user_id=current_user.id, points_balance=0, lifetime_points_earned=0)
            db.session.add(lp)
        lp.points_balance += 15
        lp.lifetime_points_earned += 15

        tx = LoyaltyTransaction(
            user_id=current_user.id,
            activity_type='review',
            points_earned=15,
            description=f"Earned 15 BingePoints for reviewing '{movie.title}'"
        )
        db.session.add(tx)
        flash('Thank you for your review! +15 BingePoints added to your account! 🌟', 'success')
    else:
        flash('Thank you for submitting your review!', 'success')
    
    db.session.commit()

    if movie.is_classic:
        return redirect(url_for('main.classic_detail', slug=movie.slug))
    return redirect(url_for('main.movie_detail', slug=movie.slug))


# FEATURE A: Watch Party Guest Voting Page Route
@main_bp.route('/party/<party_code>')
def party_vote_page(party_code):
    from models import WatchParty, Seat
    party = WatchParty.query.filter_by(party_code=party_code).first_or_404()

    is_expired = (datetime.utcnow() > party.expires_at) or (party.status == 'closed')
    show = party.show
    movie = show.movie
    screen = show.screen
    theatre = screen.theatre

    seats = Seat.query.filter_by(screen_id=screen.id).order_by(Seat.row_label.asc(), Seat.seat_number.asc()).all()

    # Group seats by row label
    rows_dict = {}
    for s in seats:
        if s.row_label not in rows_dict:
            rows_dict[s.row_label] = []
        rows_dict[s.row_label].append(s)

    # Vote counts per seat
    votes_by_seat = {}
    for v in party.votes:
        votes_by_seat[v.seat_id] = votes_by_seat.get(v.seat_id, 0) + 1

    return render_template(
        'party_vote.html',
        party=party,
        is_expired=is_expired,
        show=show,
        movie=movie,
        screen=screen,
        theatre=theatre,
        rows_dict=rows_dict,
        votes_by_seat=votes_by_seat
    )

