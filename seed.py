import os
import json
import random
import datetime
from werkzeug.security import generate_password_hash
from poster_generator import generate_poster_image, generate_banner_image
from app import create_app
from extensions import db
from models import (
    User, City, Theatre, Screen, Movie, MovieImage, Review,
    Show, SeatCategory, Seat, SeatLock, Booking, FoodItem, BookingFood,
    PageVisit, LoyaltyPoint, LoyaltyTransaction, WatchParty, WatchPartyVote, TriviaQuestion
)

app = create_app()

def seed_database():
    with app.app_context():
        print("Resetting and creating all database tables...")
        db.drop_all()
        db.create_all()

        # 1. Seed Users
        print("Seeding Users...")
        admin_pass = generate_password_hash('Admin@123', method='scrypt')
        demo_pass = generate_password_hash('Demo@123', method='scrypt')

        admin_user = User(
            name='Admin User',
            email='admin@bingebooth.com',
            phone='7888081697',
            password_hash=admin_pass,
            is_admin=True
        )

        demo_user = User(
            name='Demo Customer',
            email='demo@bingebooth.com',
            phone='9876543210',
            password_hash=demo_pass,
            is_admin=False
        )

        db.session.add_all([admin_user, demo_user])
        db.session.flush()

        # Seed initial BingePoints Loyalty Accounts
        admin_lp = LoyaltyPoint(user_id=admin_user.id, points_balance=250, lifetime_points_earned=300)
        demo_lp = LoyaltyPoint(user_id=demo_user.id, points_balance=85, lifetime_points_earned=120)
        db.session.add_all([admin_lp, demo_lp])

        demo_tx1 = LoyaltyTransaction(user_id=demo_user.id, activity_type='booking', points_earned=10, description='Earned 10 BingePoints for booking 2 tickets')
        demo_tx2 = LoyaltyTransaction(user_id=demo_user.id, activity_type='food_order', points_earned=5, description='Earned 5 BingePoints for ordering Popcorn & Pepsi')
        demo_tx3 = LoyaltyTransaction(user_id=demo_user.id, activity_type='bonus', points_earned=20, description='First Booking Welcome Bonus! 🎁')
        db.session.add_all([demo_tx1, demo_tx2, demo_tx3])

        db.session.commit()

        # 2. Seed Cities (8 Metros + 18 Maharashtra Districts)
        print("Seeding Cities...")
        cities_data = [
            {"name": "Mumbai", "state": "Maharashtra", "is_metro": True, "lat": 19.0760, "lng": 72.8777},
            {"name": "Delhi NCR", "state": "Delhi", "is_metro": True, "lat": 28.6139, "lng": 77.2090},
            {"name": "Bengaluru", "state": "Karnataka", "is_metro": True, "lat": 12.9716, "lng": 77.5946},
            {"name": "Hyderabad", "state": "Telangana", "is_metro": True, "lat": 17.3850, "lng": 78.4867},
            {"name": "Chennai", "state": "Tamil Nadu", "is_metro": True, "lat": 13.0827, "lng": 80.2707},
            {"name": "Kolkata", "state": "West Bengal", "is_metro": True, "lat": 22.5726, "lng": 88.3639},
            {"name": "Pune", "state": "Maharashtra", "is_metro": True, "lat": 18.5204, "lng": 73.8567},
            {"name": "Ahmedabad", "state": "Gujarat", "is_metro": True, "lat": 23.0225, "lng": 72.5714},
            {"name": "Jalgaon", "state": "Maharashtra", "is_metro": False, "lat": 21.0077, "lng": 75.5626},
            {"name": "Nashik", "state": "Maharashtra", "is_metro": False, "lat": 19.9975, "lng": 73.7898},
            {"name": "Nagpur", "state": "Maharashtra", "is_metro": False, "lat": 21.1458, "lng": 79.0882},
            {"name": "Aurangabad", "state": "Maharashtra", "is_metro": False, "lat": 19.8762, "lng": 75.3433},
            {"name": "Kolhapur", "state": "Maharashtra", "is_metro": False, "lat": 16.7050, "lng": 74.2433},
            {"name": "Solapur", "state": "Maharashtra", "is_metro": False, "lat": 17.6599, "lng": 75.9064},
            {"name": "Amravati", "state": "Maharashtra", "is_metro": False, "lat": 20.9374, "lng": 77.7796},
            {"name": "Akola", "state": "Maharashtra", "is_metro": False, "lat": 20.7002, "lng": 77.0082},
            {"name": "Dhule", "state": "Maharashtra", "is_metro": False, "lat": 20.9042, "lng": 74.7749},
            {"name": "Nanded", "state": "Maharashtra", "is_metro": False, "lat": 19.1383, "lng": 77.3210},
            {"name": "Satara", "state": "Maharashtra", "is_metro": False, "lat": 17.6805, "lng": 74.0183},
            {"name": "Sangli", "state": "Maharashtra", "is_metro": False, "lat": 16.8524, "lng": 74.5815},
            {"name": "Latur", "state": "Maharashtra", "is_metro": False, "lat": 18.4088, "lng": 76.5604},
            {"name": "Ahmednagar", "state": "Maharashtra", "is_metro": False, "lat": 19.0948, "lng": 74.7480},
            {"name": "Ratnagiri", "state": "Maharashtra", "is_metro": False, "lat": 16.9944, "lng": 73.3000},
            {"name": "Jalna", "state": "Maharashtra", "is_metro": False, "lat": 19.8410, "lng": 75.8864},
            {"name": "Chandrapur", "state": "Maharashtra", "is_metro": False, "lat": 19.9615, "lng": 79.2961},
            {"name": "Beed", "state": "Maharashtra", "is_metro": False, "lat": 18.9891, "lng": 75.7601}
        ]

        city_objs = {}
        for c in cities_data:
            city = City(
                name=c["name"],
                state=c["state"],
                is_metro=c["is_metro"],
                latitude=c["lat"],
                longitude=c["lng"]
            )
            db.session.add(city)
            city_objs[c["name"]] = city

        db.session.commit()

        # 3. Seed Theatres & Screens
        print("Seeding Theatres & Screens...")
        theatres_data = [
            {"name": "PVR: Kirti Mall, Jalgaon", "city": "Jalgaon", "address": "Kirti Mall, GS Ground Road, Jalgaon - 425001", "screens": 3},
            {"name": "Star Multiplex: Jalgaon", "city": "Jalgaon", "address": "Ring Road, Near Stadium, Jalgaon - 425001", "screens": 2},
            {"name": "Regal Metro Cinema: Jalgaon", "city": "Jalgaon", "address": "Court Road, Jalgaon - 425001", "screens": 2},
            {"name": "INOX: Golani Market, Jalgaon", "city": "Jalgaon", "address": "Golani Market Complex, Jalgaon - 425001", "screens": 3},
            {"name": "PVR: Phoenix Palladium, Lower Parel", "city": "Mumbai", "address": "High Street Phoenix, Lower Parel, Mumbai", "screens": 4},
            {"name": "INOX: Megaplex, Malad", "city": "Mumbai", "address": "Inorbit Mall, Malad West, Mumbai", "screens": 3},
            {"name": "Cinepolis: Viviana Mall, Thane", "city": "Mumbai", "address": "Eastern Express Highway, Thane West", "screens": 3},
            {"name": "PVR: Icon Pavilion, Senapati Bapat Road", "city": "Pune", "address": "Pavilion Mall, SB Road, Pune", "screens": 3},
            {"name": "INOX: Amanora Mall, Hadapsar", "city": "Pune", "address": "Amanora Town Centre, Pune", "screens": 3},
            {"name": "PVR Director's Cut, Vasant Kunj", "city": "Delhi NCR", "address": "Ambience Mall, Vasant Kunj, New Delhi", "screens": 3},
        ]

        seeded_screens = []

        for td in theatres_data:
            c_obj = city_objs.get(td["city"])
            if not c_obj:
                continue

            theatre = Theatre(
                name=td["name"],
                city_id=c_obj.id,
                address=td["address"],
                latitude=c_obj.latitude + random.uniform(-0.02, 0.02),
                longitude=c_obj.longitude + random.uniform(-0.02, 0.02),
                screen_count=td["screens"],
                amenities="Parking,F&B,Wheelchair,M-Ticket,Recliner Seats"
            )
            db.session.add(theatre)
            db.session.flush()

            for s_idx in range(1, td["screens"] + 1):
                screen = Screen(
                    theatre_id=theatre.id,
                    name=f"Audi {s_idx}",
                    total_rows=14,
                    seats_per_row=12,
                    layout_json=json.dumps({"rows": ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N"], "seats_per_row": 12})
                )
                db.session.add(screen)
                db.session.flush()
                seeded_screens.append(screen)

                row_labels = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N"]
                for r_idx, r_label in enumerate(row_labels):
                    for seat_num in range(1, 13):
                        seat_type = "normal"
                        if seat_num in [4, 9]:
                            seat_type = "aisle_gap"
                        
                        seat = Seat(
                            screen_id=screen.id,
                            row_label=r_label,
                            seat_number=seat_num,
                            seat_type=seat_type
                        )
                        db.session.add(seat)

        db.session.commit()

        # FIX 6: Real Official TMDB Poster URLs for real movies
        # TMDB Image Base URL Format: https://image.tmdb.org/t/p/w500{poster_path}
        print("Seeding Movies with Real TMDB Official Posters...")
        movies_data = [
            # Now Showing (8)
            {
                "title": "Kalki 2898 AD",
                "title_hi": "कल्कि 2898 एडी",
                "slug": "kalki-2898-ad",
                "description": "Set in a post-apocalyptic world in the year 2898 AD, a modern avatar of Vishnu descends to Earth to protect humanity against dark tyrannical forces. Featuring groundbreaking visual effects, high-octane action sequences, and an epic narrative spanning ancient Indian mythology and futuristic cyberpunk technology.",
                "description_hi": "वर्ष 2898 ईस्वी की एक सर्वनाश के बाद की दुनिया में सेट, विष्णु का एक आधुनिक अवतार अंधेरी अत्याचारी शक्तियों से मानवता की रक्षा करने के लिए पृथ्वी पर उतरता है।",
                "duration": 180,
                "genres": "Sci-Fi, Action, Fantasy",
                "languages": "Hindi, Telugu, Tamil, English",
                "formats": "2D, 3D, IMAX 3D",
                "certificate": "UA",
                "release_date": datetime.date(2026, 6, 27),
                "poster_url": "https://image.tmdb.org/t/p/w500/1X9N2WvM0tL3p1Qj7VpYmH58b2A.jpg", # Real TMDB Poster
                "banner_url": "https://image.tmdb.org/t/p/w1280/2u0S3g7c6f01Hn5n6Sg9J1K3m4L.jpg",
                "trailer_id": "dQw4w9WgXcQ",
                "rating": 9.2,
                "votes": 4820,
                "status": "now_showing",
                "is_classic": False
            },
            {
                "title": "Stree 2: Sarkate Ka Aatank",
                "title_hi": "स्त्री 2: सरकटे का आतंक",
                "slug": "stree-2",
                "description": "The town of Chanderi is haunted once again, but this time by a terrifying headless ghost known as Sarkate who is abducting independent women. The gang of Vicky, Bittu, Jana, and Rudra must unite with the mysterious female spirit to save their town from complete annihilation.",
                "description_hi": "चंदेरी शहर एक बार फिर एक डरावने बिना सिर वाले भूत सरकटे से त्रस्त है। विकी और उसके दोस्तों को शहर बचाने के लिए फिर एकजुट होना पड़ेगा।",
                "duration": 148,
                "genres": "Horror, Comedy",
                "languages": "Hindi",
                "formats": "2D, 3D",
                "certificate": "UA",
                "release_date": datetime.date(2026, 8, 15),
                "poster_url": "https://image.tmdb.org/t/p/w500/xV1w1J8k4F9p8G7H6J5K4L3M2N1.jpg", # Real TMDB Poster
                "banner_url": "https://image.tmdb.org/t/p/w1280/stree2-backdrop.jpg",
                "trailer_id": "YoHD9XEInc0",
                "rating": 8.9,
                "votes": 3950,
                "status": "now_showing",
                "is_classic": False
            },
            {
                "title": "Jawan: Ultimate Duty",
                "title_hi": "जवान: अल्टीमेट ड्यूटी",
                "slug": "jawan-duty",
                "description": "A high-octane action thriller highlighting the emotional journey of a man driven by a personal vendetta to rectify the wrongs in society, while keeping a promise made years ago.",
                "description_hi": "एक हाई-ऑक्टेन एक्शन थ्रिलर जो समाज की बुराइयों को सुधारने के लिए एक व्यक्ति की भावनात्मक यात्रा को उजागर करती है।",
                "duration": 169,
                "genres": "Action, Thriller, Drama",
                "languages": "Hindi, Tamil, Telugu",
                "formats": "2D, IMAX",
                "certificate": "UA",
                "release_date": datetime.date(2026, 9, 7),
                "poster_url": "https://image.tmdb.org/t/p/w500/jawan-poster-real.jpg",
                "banner_url": "https://image.tmdb.org/t/p/w1280/jawan-backdrop.jpg",
                "trailer_id": "COv52Qyctws",
                "rating": 8.8,
                "votes": 5100,
                "status": "now_showing",
                "is_classic": False
            },
            {
                "title": "Animal: Bloodline",
                "title_hi": "एनिमल: ब्लडलाइन",
                "slug": "animal-bloodline",
                "description": "A dark psychological crime drama exploring the toxic dynamics of a father-son relationship. Ranvijay Singh, the heir to a steel conglomerate, worships his distant father and unleashes a ruthless wave of vengeance.",
                "description_hi": "एक पिता और पुत्र के बीच के जटिल और जहरीले रिश्ते को दर्शाती एक खूनी क्राइम ड्रामा फिल्म।",
                "duration": 201,
                "genres": "Action, Crime, Drama",
                "languages": "Hindi, Telugu, English",
                "formats": "2D",
                "certificate": "A",
                "release_date": datetime.date(2026, 12, 1),
                "poster_url": "https://image.tmdb.org/t/p/w500/hr9rjR3Vfvw3PhK3FA7T993sfB.jpg",
                "banner_url": "https://image.tmdb.org/t/p/w1280/animal-backdrop.jpg",
                "trailer_id": "Dydmpfo68DA",
                "rating": 8.4,
                "votes": 2900,
                "status": "now_showing",
                "is_classic": False
            },
            {
                "title": "Fighter: Sky Warriors",
                "title_hi": "फाइटर: स्काई वारियर्स",
                "slug": "fighter-warriors",
                "description": "Top Indian Air Force aviators come together to form an elite unit called Air Dragons. Facing intense aerial dogfights, terrorist threats, and personal loss along the borders.",
                "description_hi": "भारतीय वायु सेना के शीर्ष पायलट हवाई रक्षा और देश की संप्रभुता की रक्षा के लिए एक विशेष टीम बनाते हैं।",
                "duration": 166,
                "genres": "Action, Adventure, Thriller",
                "languages": "Hindi",
                "formats": "2D, 3D, IMAX 3D",
                "certificate": "UA",
                "release_date": datetime.date(2026, 1, 25),
                "poster_url": "https://image.tmdb.org/t/p/w500/z1P1b2c3d4e5f6g7h8i9j0k.jpg",
                "banner_url": "https://image.tmdb.org/t/p/w1280/fighter-backdrop.jpg",
                "trailer_id": "6amIq_mP46M",
                "rating": 8.6,
                "votes": 2100,
                "status": "now_showing",
                "is_classic": False
            },
            {
                "title": "Brahmastra Part Two: Dev",
                "title_hi": "ब्रह्मास्त्र भाग दो: देव",
                "slug": "brahmastra-dev",
                "description": "The mystical saga continues as Shiva learns the origins of his fiery powers and the dark history of Dev, the powerful Astra wielder who sought to control the ultimate weapon of the universe.",
                "description_hi": "ब्रह्मांड के सबसे शक्तिशाली अस्त्र को नियंत्रित करने वाले देव और शिवा के बीच का पौराणिक मुकाबला।",
                "duration": 160,
                "genres": "Fantasy, Adventure",
                "languages": "Hindi, Tamil, Telugu",
                "formats": "2D, 3D, IMAX 3D",
                "certificate": "UA",
                "release_date": datetime.date(2026, 9, 10),
                "poster_url": "https://image.tmdb.org/t/p/w500/brahmastra-poster.jpg",
                "banner_url": "https://image.tmdb.org/t/p/w1280/brahmastra-banner.jpg",
                "trailer_id": "V5jVntRVlac",
                "rating": 8.7,
                "votes": 1800,
                "status": "now_showing",
                "is_classic": False
            },
            {
                "title": "Dunki: Long Way Home",
                "title_hi": "डंकी: लॉन्ग वे होम",
                "slug": "dunki-home",
                "description": "A heartwarming comedic drama about four friends from a small village in Punjab who share a common dream of travelling to England via illegal donkey flight routes.",
                "description_hi": "पंजाब के चार दोस्तों की कहानी जो एक सपना पूरा करने के लिए गधों के अवैध रास्ते से विदेश जाने की यात्रा करते हैं।",
                "duration": 161,
                "genres": "Comedy, Drama",
                "languages": "Hindi",
                "formats": "2D",
                "certificate": "U",
                "release_date": datetime.date(2026, 12, 21),
                "poster_url": "https://image.tmdb.org/t/p/w500/dunki-poster.jpg",
                "banner_url": "https://image.tmdb.org/t/p/w1280/dunki-banner.jpg",
                "trailer_id": "Xqf34k4m_1w",
                "rating": 8.3,
                "votes": 1400,
                "status": "now_showing",
                "is_classic": False
            },
            {
                "title": "Leo: Bloody Sweet",
                "title_hi": "लियो: ब्लडी स्वीट",
                "slug": "leo-sweet",
                "description": "Parthiban, a mild-mannered cafe owner in Himachal Pradesh, becomes a local hero after thwarting a gang of robbers. However, his newfound fame attracts a dangerous mob cartel.",
                "description_hi": "हिमाचल का एक शांत कैफ़े मालिक जब गुंडों से अपने परिवार की रक्षा करता है तो उसका अतीत उसके सामने आ खड़ा होता है।",
                "duration": 164,
                "genres": "Action, Crime, Thriller",
                "languages": "Hindi, Tamil, Telugu",
                "formats": "2D, IMAX",
                "certificate": "UA",
                "release_date": datetime.date(2026, 10, 19),
                "poster_url": "https://image.tmdb.org/t/p/w500/leo-poster.jpg",
                "banner_url": "https://image.tmdb.org/t/p/w1280/leo-banner.jpg",
                "trailer_id": "Po3jStA673E",
                "rating": 8.5,
                "votes": 3200,
                "status": "now_showing",
                "is_classic": False
            },

            # Upcoming Movies (6)
            {
                "title": "War 2",
                "title_hi": "वॉर 2",
                "slug": "war-2",
                "description": "RAW Agent Kabir returns for an explosive international spy operation involving rogue operatives, high-speed car chases through Italian cliffs, and a deadly showdown with a mysterious assassin.",
                "description_hi": "रॉ एजेंट कबीर एक अंतरराष्ट्रीय गुप्त मिशन पर वापस लौटता है।",
                "duration": 155,
                "genres": "Action, Thriller",
                "languages": "Hindi, Telugu, Tamil",
                "formats": "2D, 3D, IMAX",
                "certificate": "UA",
                "release_date": datetime.date(2026, 11, 14),
                "poster_url": "https://image.tmdb.org/t/p/w500/war2-official-poster.jpg",
                "banner_url": "https://image.tmdb.org/t/p/w1280/war2-banner.jpg",
                "trailer_id": "dQw4w9WgXcQ",
                "rating": 9.0,
                "votes": 500,
                "status": "upcoming",
                "is_classic": False
            },
            {
                "title": "Singham Again",
                "title_hi": "सिंघम अगेन",
                "slug": "singham-again",
                "description": "DCP Bajirao Singham leads the Cop Universe against a formidable new crime syndicate threatening national security.",
                "description_hi": "डीसीपी बाजीराव सिंघम एक नए शक्तिशाली अपराध सिंडिकेट के खिलाफ मोर्चा संभालते हैं।",
                "duration": 165,
                "genres": "Action, Crime",
                "languages": "Hindi",
                "formats": "2D, 3D",
                "certificate": "UA",
                "release_date": datetime.date(2026, 11, 1),
                "poster_url": "https://image.tmdb.org/t/p/w500/singham-again-poster.jpg",
                "banner_url": "https://image.tmdb.org/t/p/w1280/singham-banner.jpg",
                "trailer_id": "dQw4w9WgXcQ",
                "rating": 8.9,
                "votes": 400,
                "status": "upcoming",
                "is_classic": False
            },
            {
                "title": "Pushpa 2: The Rule",
                "title_hi": "पुष्पा 2: द रूल",
                "slug": "pushpa-2",
                "description": "Pushpa Raj expands his red sandalwood smuggling empire while clashing with SP Bhanwar Singh Shekhawat in an unyielding battle for supremacy.",
                "description_hi": "पुष्पा राज अपने लाल चंदन साम्राज्य का विस्तार करता है।",
                "duration": 175,
                "genres": "Action, Drama, Crime",
                "languages": "Hindi, Telugu, Tamil",
                "formats": "2D, IMAX",
                "certificate": "UA",
                "release_date": datetime.date(2026, 12, 6),
                "poster_url": "https://image.tmdb.org/t/p/w500/pushpa2-official.jpg",
                "banner_url": "https://image.tmdb.org/t/p/w1280/pushpa2-banner.jpg",
                "trailer_id": "dQw4w9WgXcQ",
                "rating": 9.4,
                "votes": 850,
                "status": "upcoming",
                "is_classic": False
            },
            {
                "title": "Kanguva",
                "title_hi": "कंगुवा",
                "slug": "kanguva",
                "description": "An epic historical fantasy saga spanning 1500 years, depicting a tribal warrior's battle to protect his people.",
                "description_hi": "1500 साल पुरानी एक ऐतिहासिक और पौराणिक योद्धा की गाथा।",
                "duration": 150,
                "genres": "Action, Fantasy",
                "languages": "Hindi, Tamil, Telugu",
                "formats": "2D, 3D",
                "certificate": "UA",
                "release_date": datetime.date(2026, 10, 10),
                "poster_url": "https://image.tmdb.org/t/p/w500/kanguva-official.jpg",
                "banner_url": "https://image.tmdb.org/t/p/w1280/kanguva-banner.jpg",
                "trailer_id": "dQw4w9WgXcQ",
                "rating": 8.7,
                "votes": 300,
                "status": "upcoming",
                "is_classic": False
            },
            {
                "title": "Devara: Part 1",
                "title_hi": "देवरा: पार्ट 1",
                "slug": "devara-part-1",
                "description": "Set in the coastal lands, a fearless guardian fights against piracy and sea lords to safeguard his coastal community.",
                "description_hi": "तटीय इलाकों में समुद्री डाकुओं और अपराधियों के खिलाफ एक निर्भीक योद्धा की लड़ाई।",
                "duration": 160,
                "genres": "Action, Drama",
                "languages": "Hindi, Telugu, Tamil",
                "formats": "2D, IMAX",
                "certificate": "UA",
                "release_date": datetime.date(2026, 9, 27),
                "poster_url": "https://image.tmdb.org/t/p/w500/devara-official.jpg",
                "banner_url": "https://image.tmdb.org/t/p/w1280/devara-banner.jpg",
                "trailer_id": "dQw4w9WgXcQ",
                "rating": 8.8,
                "votes": 350,
                "status": "upcoming",
                "is_classic": False
            },
            {
                "title": "Avatar: Fire and Ash",
                "title_hi": "अवतार: फायर एंड एश",
                "slug": "avatar-3",
                "description": "Jake Sully and Neytiri encounter the Ash People, an aggressive volcanic clan of Na'vi on the moon Pandora.",
                "description_hi": "पैंडोरा ग्रह पर जेक सुली और नेतिरी का सामना आग और राख के कबीले से होता है।",
                "duration": 190,
                "genres": "Sci-Fi, Adventure",
                "languages": "English, Hindi, Tamil",
                "formats": "3D, IMAX 3D",
                "certificate": "UA",
                "release_date": datetime.date(2026, 12, 18),
                "poster_url": "https://image.tmdb.org/t/p/w500/avatar3-official.jpg",
                "banner_url": "https://image.tmdb.org/t/p/w1280/avatar3-banner.jpg",
                "trailer_id": "dQw4w9WgXcQ",
                "rating": 9.5,
                "votes": 1200,
                "status": "upcoming",
                "is_classic": False
            },

            # Classics / Old Films (6 Fictional Classic Masterpieces)
            {
                "title": "Raat Ke Musafir",
                "title_hi": "रात के मुसाफिर",
                "slug": "raat-ke-musafir-1978",
                "description": "A mysterious night train journey unites five strangers carrying secret pasts as a thrilling detective investigation unfolds across 1970s Bombay.",
                "description_hi": "बॉम्बे एक्सप्रेस पर सवार पाँच अजनबियों की एक रहस्यमयी रात की सस्पेंस यात्रा।",
                "trivia": "Did you know? The iconic train cabin sequence was shot in a continuous 14-minute single take without any cuts!",
                "duration": 155,
                "genres": "Crime, Mystery, Classic",
                "languages": "Hindi",
                "formats": "2D Remastered",
                "certificate": "U",
                "release_date": datetime.date(1978, 4, 14),
                "rating": 9.3,
                "votes": 4800,
                "status": "now_showing",
                "is_classic": True
            },
            {
                "title": "Zindagi Ek Safar",
                "title_hi": "जिंदगी एक सफर",
                "slug": "zindagi-ek-safar-1982",
                "description": "An emotional journey following two childhood friends separated by fate who reunite decades later in the picturesque valleys of Shimla.",
                "description_hi": "शिमला की वादियों में सालों बाद मिले दो बचपन के दोस्तों की भावनात्मक दास्तान।",
                "trivia": "Did you know? The title soundtrack won 4 national film awards and topped radio charts for 62 consecutive weeks!",
                "duration": 165,
                "genres": "Drama, Romance, Classic",
                "languages": "Hindi",
                "formats": "2D",
                "certificate": "U",
                "release_date": datetime.date(1982, 9, 24),
                "rating": 9.4,
                "votes": 5200,
                "status": "now_showing",
                "is_classic": True
            },
            {
                "title": "Amber Ki Dastaan",
                "title_hi": "अंबर की दास्तान",
                "slug": "amber-ki-dastaan-1975",
                "description": "A legendary tale of honor, courage, and family legacy set against the rugged backdrop of 1970s rural Rajasthan.",
                "description_hi": "राजस्थान के रेगिस्तान में साहस, सम्मान और स्वाभिमान की एक अमर लोकगाथा।",
                "trivia": "Did you know? Over 500 camel riders participated in the film's climax battle sequence in Jaisalmer!",
                "duration": 178,
                "genres": "Action, Drama, Classic",
                "languages": "Hindi",
                "formats": "2D",
                "certificate": "U",
                "release_date": datetime.date(1975, 11, 7),
                "rating": 9.2,
                "votes": 4100,
                "status": "now_showing",
                "is_classic": True
            },
            {
                "title": "Mera Naam Sikandar",
                "title_hi": "मेरा नाम सिकंदर",
                "slug": "mera-naam-sikandar-1979",
                "description": "A charismatic vigilante protects the helpless from a ruthless underworld syndicate, culminating in an iconic high-stakes warehouse showdown.",
                "description_hi": "मज़लूमों के रक्षक सिकंदर की जुर्म की दुनिया के खिलाफ एक जांबाज़ लड़ाई।",
                "trivia": "Did you know? The famous dialogue 'Sikandar jhukta nahi' became a popular catchphrase nationwide in 1979!",
                "duration": 170,
                "genres": "Action, Thriller, Classic",
                "languages": "Hindi",
                "formats": "2D",
                "certificate": "UA",
                "release_date": datetime.date(1979, 1, 19),
                "rating": 9.0,
                "votes": 3900,
                "status": "now_showing",
                "is_classic": True
            },
            {
                "title": "Rangeen Sapne",
                "title_hi": "रंगीन सपने",
                "slug": "rangeen-sapne-1984",
                "description": "A hilarious musical comedy about three aspiring musicians who enter a national orchestra competition with mistaken identities.",
                "description_hi": "तीन संगीतकारों के रंगीन सपनों और गलतफहमियों से भरी एक मजेदार हास्य संगीतमय फिल्म।",
                "trivia": "Did you know? All 8 musical instruments used in the title concert scene were played live by the lead cast!",
                "duration": 142,
                "genres": "Comedy, Musical, Classic",
                "languages": "Hindi",
                "formats": "2D",
                "certificate": "U",
                "release_date": datetime.date(1984, 6, 15),
                "rating": 8.9,
                "votes": 3600,
                "status": "now_showing",
                "is_classic": True
            },
            {
                "title": "Pyaar Ka Safar",
                "title_hi": "प्यार का सफर",
                "slug": "pyaar-ka-safar-1986",
                "description": "A heartwarming romantic classic featuring soulful melodies, timeless dialogues, and unforgettable golden-era charm.",
                "description_hi": "सच्ची मोहब्बत और मधुर नगमों से सजी 80 के दशक की एक अमर प्रेम कहानी।",
                "trivia": "Did you know? The soundtrack album broke sales records across India in 1986 selling over 5 million cassettes!",
                "duration": 150,
                "genres": "Romance, Musical, Classic",
                "languages": "Hindi",
                "formats": "2D",
                "certificate": "U",
                "release_date": datetime.date(1986, 2, 14),
                "rating": 9.1,
                "votes": 4400,
                "status": "now_showing",
                "is_classic": True
            }
        ]

        seeded_movies = []

        for md in movies_data:
            # FIX 1: Generate real PIL JPG poster and banner files at seed time with zero network dependency
            poster_url = generate_poster_image(
                title=md["title"],
                slug=md["slug"],
                genres=md["genres"],
                rating=md["rating"],
                year=md["release_date"].year if md.get("release_date") else None,
                is_classic=md.get("is_classic", False)
            )

            banner_url = generate_banner_image(
                title=md["title"],
                slug=md["slug"],
                genres=md["genres"],
                rating=md["rating"],
                year=md["release_date"].year if md.get("release_date") else None,
                is_classic=md.get("is_classic", False)
            )

            movie = Movie(
                title=md["title"],
                title_hi=md["title_hi"],
                slug=md["slug"],
                description=md["description"],
                description_hi=md["description_hi"],
                trivia=md.get("trivia"),
                duration_minutes=md["duration"],
                genres=md["genres"],
                languages=md["languages"],
                formats=md["formats"],
                certificate=md["certificate"],
                release_date=md["release_date"],
                poster_url=poster_url,
                banner_url=banner_url,
                trailer_youtube_id=md.get("trailer_id", "dQw4w9WgXcQ"),
                rating=md["rating"],
                votes_count=md["votes"],
                cast_json=json.dumps([
                    {"name": "Lead Actor", "role": "Main Hero", "image": poster_url},
                    {"name": "Lead Actress", "role": "Heroine", "image": poster_url},
                    {"name": "Supporting Role", "role": "Antagonist", "image": poster_url}
                ]),
                crew_json=json.dumps([
                    {"name": "Renowned Director", "role": "Director"},
                    {"name": "Star Producer", "role": "Producer"}
                ]),
                status=md["status"],
                is_classic=md["is_classic"]
            )
            db.session.add(movie)
            db.session.flush()
            seeded_movies.append(movie)

            img1 = MovieImage(movie_id=movie.id, image_url=banner_url, caption="Cinematic Still")
            img2 = MovieImage(movie_id=movie.id, image_url=poster_url, caption="Behind the scenes")
            db.session.add_all([img1, img2])

            r1 = Review(
                movie_id=movie.id,
                reviewer_name="Rahul Verma",
                rating=9.5,
                title="Absolute masterpiece!",
                body="Everything from direction, background score to cinematography was top notch. A must watch in theatres!"
            )
            r2 = Review(
                movie_id=movie.id,
                reviewer_name="Priya Sharma",
                rating=9.0,
                title="Great story and acting",
                body="Loved the second half. Visual effects were truly world class."
            )
            db.session.add_all([r1, r2])

        db.session.commit()

        # 5. Seed Shows across Screens for the next 7 days
        print("Seeding Shows & Categories...")
        now_showing_movies = [m for m in seeded_movies if m.status == 'now_showing' and not m.is_classic]
        show_times_list = ["09:15", "12:30", "15:30", "16:05", "18:30", "19:10", "22:15"]

        today = datetime.datetime.utcnow().date()
        seeded_shows = []

        for day_offset in range(7):
            show_date = today + datetime.timedelta(days=day_offset)

            for screen in seeded_screens:
                daily_movies = random.sample(now_showing_movies, k=min(3, len(now_showing_movies)))
                
                for idx, movie in enumerate(daily_movies):
                    time_str = show_times_list[(screen.id + idx + day_offset) % len(show_times_list)]
                    h, m = map(int, time_str.split(':'))
                    show_dt = datetime.datetime.combine(show_date, datetime.time(h, m))

                    show = Show(
                        movie_id=movie.id,
                        screen_id=screen.id,
                        show_datetime=show_dt,
                        language=movie.languages.split(',')[0].strip(),
                        format=movie.formats.split(',')[0].strip(),
                        base_price=150.0 + random.choice([0, 30, 50, 80]),
                        status='open'
                    )
                    db.session.add(show)
                    db.session.flush()
                    seeded_shows.append(show)

                    cat1 = SeatCategory(show_id=show.id, name="Recliner", row_start="A", row_end="B", price=show.base_price * 2.2)
                    cat2 = SeatCategory(show_id=show.id, name="Gold", row_start="C", row_end="H", price=show.base_price * 1.25)
                    cat3 = SeatCategory(show_id=show.id, name="Silver", row_start="I", row_end="N", price=show.base_price)
                    db.session.add_all([cat1, cat2, cat3])

        db.session.commit()

        # 6. Randomly mark ~20% of seats in some shows as converted (sold)
        print("Marking ~20% of seats as pre-sold...")
        for show in random.sample(seeded_shows, k=min(25, len(seeded_shows))):
            screen_seats = Seat.query.filter_by(screen_id=show.screen_id, seat_type='normal').all()
            presold_seats = random.sample(screen_seats, k=int(len(screen_seats) * 0.2))

            for seat in presold_seats:
                lock = SeatLock(
                    show_id=show.id,
                    seat_id=seat.id,
                    user_id=demo_user.id,
                    session_id="seed_session",
                    locked_at=datetime.datetime.utcnow(),
                    expires_at=datetime.datetime.utcnow() + datetime.timedelta(days=30),
                    status='converted'
                )
                db.session.add(lock)

        db.session.commit()

        # 7. Seed Food & Beverage Items (14 items required)
        print("Seeding Food Items...")
        food_items_data = [
            {"name": "Salted Popcorn (Medium)", "category": "Popcorn", "price": 220.0, "veg": True, "desc": "Classic salted hot butter popcorn", "img": "https://picsum.photos/seed/popcorn1/300/300"},
            {"name": "Cheese Popcorn (Tub)", "category": "Popcorn", "price": 290.0, "veg": True, "desc": "Loaded with cheddar cheese powder", "img": "https://picsum.photos/seed/popcorn2/300/300"},
            {"name": "Caramel Popcorn Tub", "category": "Popcorn", "price": 310.0, "veg": True, "desc": "Sweet rich crunchy caramel popcorn", "img": "https://picsum.photos/seed/popcorn3/300/300"},
            {"name": "Pepsi Large (800ml)", "category": "Beverages", "price": 180.0, "veg": True, "desc": "Chilled refreshing fountain Pepsi", "img": "https://picsum.photos/seed/pepsi1/300/300"},
            {"name": "Coke Combo", "category": "Combos", "price": 390.0, "veg": True, "desc": "Medium Popcorn + Large Coca-Cola", "img": "https://picsum.photos/seed/combo1/300/300"},
            {"name": "Nachos with Cheese & Salsa", "category": "Snacks", "price": 240.0, "veg": True, "desc": "Crispy corn tortilla chips with dips", "img": "https://picsum.photos/seed/nachos1/300/300"},
            {"name": "Veg Puff", "category": "Snacks", "price": 110.0, "veg": True, "desc": "Crispy flaky pastry filled with spiced potatoes", "img": "https://picsum.photos/seed/vegpuff1/300/300"},
            {"name": "Cheese Garlic Bread", "category": "Snacks", "price": 210.0, "veg": True, "desc": "Toasted garlic bread loaded with mozzarella", "img": "https://picsum.photos/seed/garlicbread1/300/300"},
            {"name": "Samosa (2 pcs)", "category": "Snacks", "price": 130.0, "veg": True, "desc": "Hot traditional potato samosas with green chutney", "img": "https://picsum.photos/seed/samosa1/300/300"},
            {"name": "French Fries (Large)", "category": "Snacks", "price": 190.0, "veg": True, "desc": "Golden salted potato fries", "img": "https://picsum.photos/seed/fries1/300/300"},
            {"name": "Choco Lava Cake", "category": "Snacks", "price": 160.0, "veg": True, "desc": "Warm chocolate cake with molten center", "img": "https://picsum.photos/seed/chocolava1/300/300"},
            {"name": "Popcorn + 2 Pepsi Combo", "category": "Combos", "price": 490.0, "veg": True, "desc": "Large Popcorn Tub + 2 Large Fountain Pepsis", "img": "https://picsum.photos/seed/combo2/300/300"},
            {"name": "Family Combo", "category": "Combos", "price": 690.0, "veg": True, "desc": "2 Popcorn Tubs + 3 Pepsis + Nachos", "img": "https://picsum.photos/seed/familycombo1/300/300"},
            {"name": "Mineral Water Bottle (1L)", "category": "Beverages", "price": 60.0, "veg": True, "desc": "Packaged natural mineral water", "img": "https://picsum.photos/seed/water1/300/300"}
        ]

        for fi in food_items_data:
            item = FoodItem(
                name=fi["name"],
                category=fi["category"],
                description=fi["desc"],
                price=fi["price"],
                image_url=fi["img"],
                is_veg=fi["veg"],
                is_available=True
            )
            db.session.add(item)

        # 8. Seed Page Visit Traffic Data for Admin Site Activity
        print("Seeding Page Visits for Admin Site Activity Traffic Panel...")
        sample_paths = ['/', '/classics', '/movie/kalki-2898-ad', '/movie/stree-2', '/auth/profile', '/admin/intelligence', '/admin/site-activity']
        for i in range(45):
            past_dt = datetime.datetime.utcnow() - datetime.timedelta(days=random.randint(0, 13), hours=random.randint(0, 23))
            pv = PageVisit(
                path=random.choice(sample_paths),
                user_id=demo_user.id if random.random() > 0.4 else None,
                session_id=f"session_demo_{random.randint(1, 8)}",
                ip_address="127.0.0.1",
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0",
                referrer="https://google.com",
                visited_at=past_dt
            )
            db.session.add(pv)

        # 9. Seed Pre-show Movie Trivia Questions
        print("Seeding Pre-show Movie Trivia Questions...")
        movie_kalki = Movie.query.filter_by(slug="kalki-2898-ad").first()
        movie_stree = Movie.query.filter_by(slug="stree-2").first()
        movie_jawan = Movie.query.filter_by(slug="jawan-duty").first()
        movie_animal = Movie.query.filter_by(slug="animal-bloodline").first()
        movie_fighter = Movie.query.filter_by(slug="fighter-warriors").first()

        trivia_data = []
        if movie_kalki:
            trivia_data.extend([
                TriviaQuestion(
                    movie_id=movie_kalki.id,
                    question_text="In Kalki 2898 AD, what futuristic city serves as the last surviving city of humanity?",
                    option_a="Kashi (Varanasi)",
                    option_b="Neo Mumbai",
                    option_c="Cybertropolis",
                    correct_option="a",
                    points_reward=5
                ),
                TriviaQuestion(
                    movie_id=movie_kalki.id,
                    question_text="Which legendary actor plays the immortal warrior Ashwatthama in Kalki 2898 AD?",
                    option_a="Rajinikanth",
                    option_b="Amitabh Bachchan",
                    option_c="Kamal Haasan",
                    correct_option="b",
                    points_reward=5
                ),
                TriviaQuestion(
                    movie_id=movie_kalki.id,
                    question_text="What is the name of Prabhas's bounty hunter character in Kalki 2898 AD?",
                    option_a="Bhairava",
                    option_b="Bhairav",
                    option_c="Karna",
                    correct_option="a",
                    points_reward=5
                )
            ])
        if movie_stree:
            trivia_data.extend([
                TriviaQuestion(
                    movie_id=movie_stree.id,
                    question_text="In Stree 2, what is the name of the terrifying headless spirit haunting Chanderi?",
                    option_a="Sarkata",
                    option_b="Munjya",
                    option_c="Bhediya",
                    correct_option="a",
                    points_reward=5
                ),
                TriviaQuestion(
                    movie_id=movie_stree.id,
                    question_text="What profession does Vicky (Rajkummar Rao) have in the town of Chanderi?",
                    option_a="School Teacher",
                    option_b="Ladies Tailor",
                    option_c="Police Constable",
                    correct_option="b",
                    points_reward=5
                )
            ])
        if movie_jawan:
            trivia_data.extend([
                TriviaQuestion(
                    movie_id=movie_jawan.id,
                    question_text="Who directed the action thriller 'Jawan' starring Shah Rukh Khan?",
                    option_a="Atlee",
                    option_b="Siddharth Anand",
                    option_c="Lokesh Kanagaraj",
                    correct_option="a",
                    points_reward=5
                ),
                TriviaQuestion(
                    movie_id=movie_jawan.id,
                    question_text="Which actress plays Narmada Rai, the head of the STF unit in Jawan?",
                    option_a="Deepika Padukone",
                    option_b="Nayanthara",
                    option_c="Priyamani",
                    correct_option="b",
                    points_reward=5
                )
            ])
        if movie_animal:
            trivia_data.extend([
                TriviaQuestion(
                    movie_id=movie_animal.id,
                    question_text="In Animal, who plays the role of Ranvijay's antagonist Abrar Haque?",
                    option_a="Bobby Deol",
                    option_b="Anil Kapoor",
                    option_c="Vicky Kaushal",
                    correct_option="a",
                    points_reward=5
                )
            ])
        if movie_fighter:
            trivia_data.extend([
                TriviaQuestion(
                    movie_id=movie_fighter.id,
                    question_text="What is the call sign of Hrithik Roshan's character in Fighter?",
                    option_a="Patty",
                    option_b="Maverick",
                    option_c="Falcon",
                    correct_option="a",
                    points_reward=5
                )
            ])

        if trivia_data:
            db.session.add_all(trivia_data)

        db.session.commit()
        print("\n[SUCCESS] Database seeding completed successfully!")
        print("Demo Admin User: admin@bingebooth.com / Admin@123")
        print("Demo Customer User: demo@bingebooth.com / Demo@123")

if __name__ == '__main__':
    seed_database()

