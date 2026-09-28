import time
import math
import datetime
from flask import Blueprint, request, jsonify, session
from flask_login import current_user
from extensions import db
from models import City, SeatLock, ChatLog, Movie, Theatre, Show, Seat, WatchParty, WatchPartyVote, Booking, LoyaltyPoint, TriviaQuestion, LoyaltyTransaction

api_bp = Blueprint('api', __name__)

def haversine(lat1, lon1, lat2, lon2):
    """Calculate the great circle distance in kilometers between two points on the earth."""
    R = 6371.0 # Earth radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

@api_bp.route('/detect-city', methods=['POST'])
def detect_city():
    data = request.get_json(silent=True) or request.form
    lat = float(data.get('latitude', 19.0760))
    lng = float(data.get('longitude', 72.8777))

    cities = City.query.all()
    if not cities:
        return jsonify({'success': False, 'message': 'No cities in database.'})

    nearest_city = None
    min_dist = float('inf')

    for c in cities:
        dist = haversine(lat, lng, c.latitude, c.longitude)
        if dist < min_dist:
            min_dist = dist
            nearest_city = c

    if nearest_city:
        session['city_id'] = nearest_city.id
        session['city_name'] = nearest_city.name
        return jsonify({'success': True, 'city': nearest_city.name, 'distance_km': round(min_dist, 1)})

    return jsonify({'success': False, 'message': 'City detection failed.'})

@api_bp.route('/set-city', methods=['POST'])
def set_city():
    data = request.get_json(silent=True) or request.form
    city_name = data.get('city_name', 'Mumbai')
    city = City.query.filter_by(name=city_name).first()
    if city:
        session['city_id'] = city.id
        session['city_name'] = city.name
        return jsonify({'success': True, 'city': city.name})
    return jsonify({'success': False, 'message': 'Invalid city name.'})

@api_bp.route('/show/<int:show_id>/seat-status')
def seat_status(show_id):
    now = datetime.datetime.utcnow()
    locks = SeatLock.query.filter(
        SeatLock.show_id == show_id,
        SeatLock.status.in_(['held', 'converted']),
        SeatLock.expires_at > now
    ).all()

    held_seat_ids = [l.seat_id for l in locks if l.status == 'held']
    sold_seat_ids = [l.seat_id for l in locks if l.status == 'converted']

    return jsonify({
        'success': True,
        'show_id': show_id,
        'held_seats': held_seat_ids,
        'sold_seats': sold_seat_ids
    })

@api_bp.route('/set-lang', methods=['POST'])
def set_lang():
    data = request.get_json(silent=True) or request.form
    lang = data.get('lang', 'en')
    if lang in ['en', 'hi']:
        session['lang'] = lang
        return jsonify({'success': True, 'lang': lang})
    return jsonify({'success': False, 'message': 'Invalid language code.'})

# FIX 2: Enhanced Bingyy Chatbot Intent Engine
@api_bp.route('/chat', methods=['POST'])
def chat():
    data = request.get_json(silent=True) or request.form
    msg = data.get('message', '').strip().lower()

    if not msg:
        return jsonify({'reply': 'Please type a message.', 'response': 'Please type a message.'})

    lang = session.get('lang', 'en')
    reply = ""

    # Keyword Intent Matching
    if any(k in msg for k in ['hi', 'hello', 'hey', 'namaste', 'नमस्ते', 'नमस्कार', 'शुरू', 'greetings']):
        if lang == 'hi':
            reply = "नमस्ते! मैं बिंजी हूँ — BingeBooth सहायक। मैं आपकी क्या मदद कर सकता हूँ?"
        else:
            reply = "Hello! I am Bingyy — your BingeBooth assistant. How can I help you today?"

    elif any(k in msg for k in ['how to book', 'book ticket', 'booking steps', 'बुक', 'टिकट', 'तरीका', 'कैसे']):
        if lang == 'hi':
            reply = "टिकट बुक करने के लिए: 1. होम पेज पर फिल्म चुनें, 2. शो का समय चुनें, 3. अपनी पसंदीदा सीट चुनें, 4. स्नैक्स जोड़ें और भुगतान पूरा करें!"
        else:
            reply = "To book tickets: 1. Pick a movie on the home page, 2. Select showtime, 3. Choose your preferred seats, 4. Add snacks and complete payment!"

    elif any(k in msg for k in ['cancel', 'refund', 'रद्द', 'रिफंड', 'वापसी', 'रद्दीकरण']):
        if lang == 'hi':
            reply = "रद्दीकरण नीति: शो के समय से कम से कम 2 घंटे पहले 'माई प्रोफ़ाइल' सेक्शन से टिकट रद्द की जा सकती हैं। रिफंड 24 घंटे में क्रेडिट कर दिया जाता है।"
        else:
            reply = "Cancellation Policy: You can cancel your tickets from 'My Profile' at least 2 hours before showtime. Refunds are processed within 24 hours."

    elif any(k in msg for k in ['hold', 'time', 'timing', 'lock', '4 min', '4 मिनट', 'मिनट', 'होल्ड', 'समय']):
        if lang == 'hi':
            reply = "आपकी सीटें भुगतान पूरा करने के लिए 4 मिनट तक सुरक्षित (होल्ड) रखी जाती हैं। यदि समय समाप्त हो जाता है, तो सीटें स्वचालित रूप से रिलीज़ हो जाती हैं।"
        else:
            reply = "Selected seats are held for exactly 4 minutes to complete your payment. If the timer expires, seats are automatically released."

    elif any(k in msg for k in ['payment', 'upi', 'card', 'net banking', 'wallet', 'पेमेंट', 'भुगतान', 'कार्ड']):
        if lang == 'hi':
            reply = "हम UPI (GPay, PhonePe, Paytm), क्रेडिट/डेबिट कार्ड, नेट बैंकिंग और ई-वॉलेट स्वीकार करते हैं।"
        else:
            reply = "We accept UPI (GPay, PhonePe, Paytm), Credit/Debit Cards, Net Banking, and Mobile Wallets."

    elif any(k in msg for k in ['food', 'popcorn', 'snacks', 'drink', 'खाना', 'पॉपकॉर्न', 'स्नैक्स', 'समोसा']):
        if lang == 'hi':
            reply = "हमारे पास बटर पॉपकॉर्न, कैरेमल पॉपकॉर्न, पेप्सी, नाचोस, समोसा और कॉम्बो उपलब्ध हैं! आप सीट चयन के बाद इन्हें ऑर्डर कर सकते हैं।"
        else:
            reply = "We offer Cheese & Caramel Popcorn, Pepsi, Nachos, Samosas, and discount Combos! You can add them after picking your seats."

    elif any(k in msg for k in ['human', 'agent', 'support', 'call', 'contact', '7888081697', 'बात', 'कॉल', 'प्रतिनिधि', 'सहायक', 'हेल्पलाइन']):
        if lang == 'hi':
            reply = "हमारे 24/7 ग्राहक सेवा प्रतिनिधि से बात करने के लिए कॉल करें: 7888081697।"
        else:
            reply = "Call our 24/7 customer care: 7888081697."

    elif any(k in msg for k in ['theatre', 'theater', 'cinema', 'सिनेमाघर', 'टॉकीज']):
        city_name = session.get('city_name', 'Mumbai')
        theatres = Theatre.query.join(City).filter(City.name == city_name).all()
        t_names = ", ".join([t.name for t in theatres]) if theatres else "INOX, PVR, Cinepolis"
        if lang == 'hi':
            reply = f"{city_name} में हमारे प्रमुख सिनेमाघर हैं: {t_names}।"
        else:
            reply = f"Featured theatres in {city_name}: {t_names}."

    elif any(k in msg for k in ['upcoming', 'next', 'release', 'आने वाली']):
        upcoming_movies = Movie.query.filter_by(status='upcoming').limit(3).all()
        titles = ", ".join([m.title for m in upcoming_movies])
        if lang == 'hi':
            reply = f"जल्द रिलीज़ होने वाली फिल्में: {titles}।"
        else:
            reply = f"Exciting upcoming releases: {titles}."

    else:
        if lang == 'hi':
            reply = "मुझे आपकी बात समझ नहीं आई। आप टिकट बुकिंग, रिफंड नीति या स्नैक्स के बारे में पूछ सकते हैं, या 7888081697 पर कॉल कर सकते हैं।"
        else:
            reply = "I'm sorry, I didn't quite get that. You can ask about ticket booking, refund policy, snacks, or call customer care at 7888081697."

    # Log interaction
    try:
        log = ChatLog(
            user_id=current_user.id if current_user.is_authenticated else None,
            session_id=session.get('_id'),
            message=msg,
            response=reply
        )
        db.session.add(log)
        db.session.commit()
    except Exception:
        pass

    return jsonify({'reply': reply, 'response': reply})


# NEW FEATURE 1: Smart Movie Recommendation Endpoint
@api_bp.route('/recommendations', methods=['POST'])
def recommend_movies():
    data = request.get_json(silent=True) or request.form
    genre = data.get('genre', '').strip()
    lang = data.get('language', '').strip()
    mood = data.get('mood', '').strip()
    movie_type = data.get('movie_type', '').strip() # now_showing, upcoming, classic
    min_rating = float(data.get('min_rating', 0.0))

    query = Movie.query

    if movie_type == 'classic':
        query = query.filter_by(is_classic=True)
    elif movie_type == 'now_showing':
        query = query.filter_by(status='now_showing')
    elif movie_type == 'upcoming':
        query = query.filter_by(status='upcoming')

    if min_rating > 0:
        query = query.filter(Movie.rating >= min_rating)

    movies = query.all()
    scored_movies = []

    for m in movies:
        score = 0
        if genre and genre.lower() in m.genres.lower():
            score += 5
        if lang and lang.lower() in m.languages.lower():
            score += 4

        # Mood rule mapping
        if mood == 'Feel-good' and ('Comedy' in m.genres or 'Drama' in m.genres):
            score += 3
        elif mood == 'Intense' and ('Action' in m.genres or 'Crime' in m.genres):
            score += 3
        elif mood == 'Romantic' and ('Romance' in m.genres or 'Drama' in m.genres):
            score += 3
        elif mood == 'Thrilling' and ('Thriller' in m.genres or 'Sci-Fi' in m.genres):
            score += 3
        elif mood == 'Funny' and 'Comedy' in m.genres:
            score += 3

        score += (m.rating / 2.0)
        scored_movies.append((m, score))

    scored_movies.sort(key=lambda x: x[1], reverse=True)

    # Pick top match or randomized top selection
    results = []
    reason_prefix = f"Because you liked {genre or mood or 'top rated movies'}" if (genre or mood or lang) else "Because it's trending right now"

    for m, score in scored_movies[:4]:
        # Pull live next showtime if available
        next_show = Show.query.filter_by(movie_id=m.id, status='open').filter(Show.show_datetime >= datetime.datetime.utcnow()).order_by(Show.show_datetime.asc()).first()
        showtime_str = next_show.show_datetime.strftime('%b %d, %I:%M %p') if next_show else "Check Showtimes"

        results.append({
            'id': m.id,
            'title': m.title,
            'title_hi': m.title_hi,
            'slug': m.slug,
            'poster_url': m.poster_url,
            'rating': m.rating,
            'genres': m.genres,
            'languages': m.languages,
            'description': m.description[:120] + '...',
            'showtime': showtime_str,
            'reason': reason_prefix,
            'is_classic': m.is_classic
        })

    return jsonify({'success': True, 'recommendations': results})


# NEW FEATURE 2: Group Seat Booking Finder Algorithm
@api_bp.route('/find-best-seats', methods=['POST'])
def find_best_seats():
    data = request.get_json(silent=True) or request.form
    show_id = int(data.get('show_id', 0))
    group_size = int(data.get('group_size', 2))

    if not show_id or group_size < 1:
        return jsonify({'success': False, 'message': 'Invalid parameters.'})

    show = Show.query.get_or_404(show_id)
    now = datetime.datetime.utcnow()

    # Query active held/converted seat locks
    locks = SeatLock.query.filter(
        SeatLock.show_id == show_id,
        SeatLock.status.in_(['held', 'converted']),
        SeatLock.expires_at > now
    ).all()
    unavailable_seat_ids = set(l.seat_id for l in locks)

    # Query all normal seats for screen
    seats = Seat.query.filter_by(screen_id=show.screen_id).order_by(Seat.row_label.asc(), Seat.seat_number.asc()).all()

    # Group seats by row
    rows_dict = {}
    for s in seats:
        if s.row_label not in rows_dict:
            rows_dict[s.row_label] = []
        rows_dict[s.row_label].append(s)

    best_run = []
    best_row = ""
    best_score = -999

    # Score rows (prefer middle rows E, F, G, H)
    row_weights = {'E': 10, 'F': 10, 'G': 9, 'H': 9, 'D': 8, 'C': 7, 'I': 6, 'J': 5, 'B': 4, 'A': 3}

    for row_label, seat_list in rows_dict.items():
        weight = row_weights.get(row_label, 2)
        available_run = []

        for s in seat_list:
            if s.seat_type == 'aisle_gap':
                available_run = [] # Reset on aisle gap
                continue

            if s.id not in unavailable_seat_ids and s.seat_type == 'normal':
                available_run.append(s)
                if len(available_run) >= group_size:
                    # Score this contiguous run based on row weight & center seat alignment
                    run_seats = available_run[-group_size:]
                    avg_seat_num = sum(st.seat_number for st in run_seats) / float(group_size)
                    center_penalty = abs(6.5 - avg_seat_num) # 12 seats total, center is ~6.5
                    score = (weight * 10) - center_penalty

                    if score > best_score:
                        best_score = score
                        best_run = run_seats
                        best_row = row_label
            else:
                available_run = []

    if best_run:
        seat_ids = [s.id for s in best_run]
        labels = ", ".join([f"{s.row_label}{s.seat_number}" for s in best_run])
        return jsonify({
            'success': True,
            'row': best_row,
            'seat_ids': seat_ids,
            'labels': labels,
            'message': f"We found {group_size} seats together in Row {best_row} ({labels})!"
        })

    return jsonify({
        'success': False,
        'message': f"Couldn't find {group_size} seats together in one row — please select seats manually or choose another showtime."
    })


# NEW FEATURE 3: Redeem BingePoints Reward Endpoint
@api_bp.route('/redeem-reward', methods=['POST'])
def redeem_reward():
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'message': 'Please log in to redeem points.'})

    data = request.get_json(silent=True) or request.form
    reward_id = data.get('reward_id', '')

    rewards_map = {
        'discount_50': {'cost': 100, 'desc': '₹50 Off Ticket Discount', 'code': 'POINTS50'},
        'discount_100': {'cost': 200, 'desc': '₹100 Off Ticket Discount', 'code': 'POINTS100'},
        'free_popcorn': {'cost': 150, 'desc': 'Free Medium Popcorn Voucher', 'code': 'FREEPOPCORN'},
        'free_drink': {'cost': 100, 'desc': 'Free Large Pepsi Voucher', 'code': 'FREEDRINK'}
    }

    reward = rewards_map.get(reward_id)
    if not reward:
        return jsonify({'success': False, 'message': 'Invalid reward selection.'})

    lp = LoyaltyPoint.query.filter_by(user_id=current_user.id).first()
    if not lp or lp.points_balance < reward['cost']:
        return jsonify({'success': False, 'message': f"Insufficient points. You need {reward['cost']} points."})

    # Deduct points
    lp.points_balance -= reward['cost']

    # Record transaction
    from models import LoyaltyTransaction
    tx = LoyaltyTransaction(
        user_id=current_user.id,
        activity_type='redemption',
        points_earned=-reward['cost'],
        description=f"Redeemed reward: {reward['desc']} (Code: {reward['code']})"
    )
    db.session.add(tx)
    db.session.commit()

    return jsonify({
        'success': True,
        'new_balance': lp.points_balance,
        'code': reward['code'],
        'message': f"Successfully redeemed {reward['desc']}! Promo Code: {reward['code']}"
    })


# FEATURE A: Watch Party API Endpoints
@api_bp.route('/party/create', methods=['POST'])
def party_create():
    import string
    import random
    data = request.get_json(silent=True) or request.form
    show_id = data.get('show_id')
    if not show_id:
        return jsonify({'success': False, 'message': 'show_id is required'}), 400

    show = Show.query.get(show_id)
    if not show:
        return jsonify({'success': False, 'message': 'Showtime not found'}), 404

    # Generate 6-char random alphanumeric code
    code_chars = string.ascii_uppercase + string.digits
    party_code = 'WP-' + ''.join(random.choices(code_chars, k=6))

    # 10 minutes expiry for watch party session
    expires_at = datetime.datetime.utcnow() + datetime.timedelta(minutes=10)
    host_id = current_user.id if current_user.is_authenticated else None

    party = WatchParty(
        party_code=party_code,
        show_id=show.id,
        host_user_id=host_id,
        expires_at=expires_at,
        status='active'
    )
    db.session.add(party)
    db.session.commit()

    return jsonify({
        'success': True,
        'party_code': party_code,
        'share_url': f'/party/{party_code}',
        'expires_at': expires_at.isoformat()
    })

@api_bp.route('/party/<party_code>/votes', methods=['GET'])
def party_votes_summary(party_code):
    party = WatchParty.query.filter_by(party_code=party_code).first()
    if not party:
        return jsonify({'success': False, 'message': 'Watch party not found'}), 404

    is_expired = (datetime.datetime.utcnow() > party.expires_at) or (party.status == 'closed')

    # Calculate votes count per seat
    votes = party.votes
    votes_by_seat = {}
    voters_set = set()
    for v in votes:
        votes_by_seat[v.seat_id] = votes_by_seat.get(v.seat_id, 0) + 1
        voters_set.add(v.voter_name)

    # Get top voted seats with seat labels
    top_seat_ids = sorted(votes_by_seat.keys(), key=lambda k: votes_by_seat[k], reverse=True)[:5]
    top_seats = []
    for sid in top_seat_ids:
        seat = Seat.query.get(sid)
        if seat:
            label = f"{seat.row_label}{seat.seat_number}"
            top_seats.append({
                'seat_id': sid,
                'label': label,
                'votes': votes_by_seat[sid]
            })

    top_labels_str = ", ".join([f"{s['label']} ({s['votes']} votes)" for s in top_seats[:3]])

    return jsonify({
        'success': True,
        'party_code': party_code,
        'is_expired': is_expired,
        'total_voters': len(voters_set),
        'top_seats': top_seats,
        'top_labels_summary': top_labels_str,
        'votes_by_seat': votes_by_seat
    })

@api_bp.route('/party/<party_code>/vote', methods=['POST'])
def party_vote_submit(party_code):
    data = request.get_json(silent=True) or request.form
    voter_name = (data.get('voter_name') or 'Guest').strip()
    seat_ids = data.get('seat_ids', [])

    party = WatchParty.query.filter_by(party_code=party_code).first()
    if not party:
        return jsonify({'success': False, 'message': 'Watch party not found'}), 404

    if datetime.datetime.utcnow() > party.expires_at or party.status == 'closed':
        return jsonify({'success': False, 'message': 'This watch party has expired or ended'}), 400

    if not seat_ids:
        return jsonify({'success': False, 'message': 'Please select at least one seat to vote for.'}), 400

    # Record votes
    for sid in seat_ids:
        v = WatchPartyVote(
            party_id=party.id,
            seat_id=int(sid),
            voter_name=voter_name
        )
        db.session.add(v)

    db.session.commit()
    return jsonify({
        'success': True,
        'message': f"Thanks {voter_name}! Your votes for {len(seat_ids)} seats have been submitted to the host."
    })


# FEATURE B: Crowd Meter Live Occupancy Endpoint
@api_bp.route('/showtimes/occupancy', methods=['GET'])
def showtimes_occupancy():
    show_ids_raw = request.args.get('show_ids', '')
    if show_ids_raw:
        try:
            s_ids = [int(x.strip()) for x in show_ids_raw.split(',') if x.strip()]
            shows = Show.query.filter(Show.id.in_(s_ids)).all()
        except Exception:
            shows = Show.query.all()
    else:
        shows = Show.query.all()

    now = datetime.datetime.utcnow()
    occupancy_data = {}

    for s in shows:
        screen = s.screen
        total_seats = Seat.query.filter_by(screen_id=screen.id).count() or (screen.total_rows * screen.seats_per_row)

        # Count confirmed bookings + active locks/holds
        held_and_sold_count = SeatLock.query.filter(
            SeatLock.show_id == s.id,
            SeatLock.status.in_(['held', 'converted']),
            SeatLock.expires_at > now
        ).count()

        percent = int(round((held_and_sold_count / total_seats) * 100)) if total_seats > 0 else 0
        percent = min(100, max(0, percent))

        if percent == 0 or percent <= 25:
            label = "Just opened"
            color_class = "emerald"
        elif percent <= 60:
            label = "Filling up"
            color_class = "amber"
        elif percent <= 85:
            label = "Filling fast"
            color_class = "orange"
        elif percent < 100:
            label = "Almost full"
            color_class = "red"
        else:
            label = "Housefull"
            color_class = "purple"

        occupancy_data[str(s.id)] = {
            'percent': percent,
            'label': f"{percent}% filled • {label}" if percent > 0 else label,
            'status_label': label,
            'color': color_class
        }

    return jsonify({
        'success': True,
        'occupancy': occupancy_data
    })


# NEW FEATURE: Pre-show Trivia Mini-Quiz API Endpoints
@api_bp.route('/movie/<int:movie_id>/trivia', methods=['GET'])
def get_movie_trivia(movie_id):
    questions = TriviaQuestion.query.filter_by(movie_id=movie_id).all()
    if not questions:
        return jsonify({'success': True, 'questions': [], 'message': 'No trivia questions found.'})

    import random
    sample_q = random.sample(questions, min(len(questions), 3))
    out = []
    for q in sample_q:
        out.append({
            'id': q.id,
            'question_text': q.question_text,
            'option_a': q.option_a,
            'option_b': q.option_b,
            'option_c': q.option_c,
            'points_reward': q.points_reward
        })

    return jsonify({
        'success': True,
        'questions': out
    })

@api_bp.route('/trivia/award', methods=['POST'])
def award_trivia_points():
    data = request.get_json(silent=True) or request.form
    q_id = data.get('question_id')
    selected = (data.get('selected_option') or '').strip().lower()

    if not q_id or not selected:
        return jsonify({'success': False, 'message': 'Invalid parameters.'}), 400

    q = TriviaQuestion.query.get(q_id)
    if not q:
        return jsonify({'success': False, 'message': 'Question not found.'}), 404

    is_correct = (selected == q.correct_option.lower())
    points_earned = q.points_reward if is_correct else 0

    if is_correct and current_user.is_authenticated:
        lp = LoyaltyPoint.query.filter_by(user_id=current_user.id).first()
        if not lp:
            lp = LoyaltyPoint(user_id=current_user.id, points_balance=0, lifetime_points_earned=0)
            db.session.add(lp)
        lp.points_balance += points_earned
        lp.lifetime_points_earned += points_earned

        tx = LoyaltyTransaction(
            user_id=current_user.id,
            activity_type='bonus',
            points_earned=points_earned,
            description=f"Trivia: correct answer for '{q.movie.title}'"
        )
        db.session.add(tx)
        db.session.commit()

    option_labels = {'a': f"A: {q.option_a}", 'b': f"B: {q.option_b}", 'c': f"C: {q.option_c}"}
    correct_text = option_labels.get(q.correct_option.lower(), q.correct_option.upper())

    return jsonify({
        'success': True,
        'is_correct': is_correct,
        'correct_option': q.correct_option.lower(),
        'correct_text': correct_text,
        'points_earned': points_earned,
        'message': f"Correct! +{points_earned} BingePoints awarded!" if is_correct else f"Incorrect! The correct answer was {correct_text}."
    })


