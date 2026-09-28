# PROJECT REPORT: BINGEBOOTH
## Full-Stack Movie Ticket Booking Web Application
**Submitted for College Project Examination**

---

## 1. ABSTRACT

BingeBooth is an end-to-end, production-quality movie ticket booking web application designed and developed to provide a seamless cinema ticketing experience without reliance on third-party cloud services or paid APIs. Built using Python Flask, SQLite/SQLAlchemy ORM, Jinja2, Tailwind CSS, Alpine.js, and Vanilla JavaScript, BingeBooth introduces an original dark-first cinematic visual identity, real-time seat availability polling, atomic 4-minute temporary seat locks, background hold expiration via APScheduler, bilingual English/Hindi internationalization (i18n), automated geolocation city detection, an interactive rule-based chatbot ("Bingyy"), and a full-featured admin management portal with Chart.js analytics.

---

## 2. SYSTEM ARCHITECTURAL DESIGN

### 2.1 Technology Stack Selection
- **Backend Framework**: Python 3.10 + Flask 3.0 (Lightweight WSGI framework facilitating modular blueprint architecture).
- **Database Layer**: SQLite 3 with SQLAlchemy ORM (Relational persistence with transaction management, cascade rules, and partial indexes).
- **Authentication**: Flask-Login session management paired with Werkzeug `scrypt` key derivation function for password hashing.
- **Background Task Scheduling**: APScheduler (BackgroundScheduler) running asynchronous 30-second interval routines for releasing expired seat holds.
- **Templating Engine**: Jinja2 with custom context processors for dynamic language translation injection (`t()` global function).
- **Frontend Stack**: Single-page responsive interfaces constructed with HTML5, Tailwind CSS via CDN, Alpine.js for lightweight state management, Lucide Icons, Chart.js for data visualization, and html2canvas with QRCode.js for client-side digital ticket generation.

---

## 3. DATABASE SCHEMA & RELATIONAL MODEL

The database schema comprises 15 relational tables designed with strict foreign key constraints, cascade rules, and index optimization.

```
       +------------------+
       |      User        |
       +------------------+
       | id (PK)          |
       | email (UQ, IDX)  |
       | password_hash    |
       | is_admin         |
       +--------+---------+
                |
                | 1:N
                v
       +------------------+             +------------------+
       |     Booking      |------------>|     Show         |
       +------------------+ N:1         +------------------+
       | id (PK)          |             | id (PK)          |
       | booking_code(UQ) |             | movie_id (FK)    |
       | show_id (FK)     |             | screen_id (FK)   |
       | user_id (FK)     |             | show_datetime    |
       | ticket_amount    |             | base_price       |
       | total_amount     |             +--------+---------+
       | status           |                      |
       +--------+---------+                      | 1:N
                |                                v
                | 1:N                   +------------------+
                v                       |   SeatLock       |
       +------------------+             +------------------+
       |  BookingFood     |             | id (PK)          |
       +------------------+             | show_id (FK)     |
       | booking_id (FK)  |             | seat_id (FK)     |
       | food_item_id(FK) |             | expires_at (IDX) |
       | quantity         |             | status           |
       +------------------+             +------------------+
```

### Table-by-Table Overview

1. **`users`**: Stores user authentication credentials, contact phone, and administrative privilege flags (`is_admin`).
2. **`cities`**: Stores geographic coordinates (latitude, longitude) for Haversine distance calculations and metro/district classifications.
3. **`theatres`**: Cinema halls associated with a city, storing street addresses, screen counts, and comma-separated amenity tags.
4. **`screens`**: Individual auditoriums within a theatre, storing total rows, seats per row, and JSON structural layouts.
5. **`movies`**: Comprehensive movie records containing dual-language titles (`title`, `title_hi`), descriptions, duration, genres, certificate ratings, YouTube trailer IDs, rating scores, vote counts, JSON cast/crew arrays, and status flags (`now_showing`, `upcoming`, `archived`, `is_classic`).
6. **`movie_images`**: High-resolution gallery photos associated with a movie.
7. **`reviews`**: User ratings (1-10) and written reviews linked to specific movies.
8. **`shows`**: Scheduled movie screenings linking a movie to a screen at a specific date and time, with language/format specifications and base price settings.
9. **`seat_categories`**: Pricing tiers assigned to row ranges within a show (e.g., Recliner: Rows A-B, Gold: Rows C-H, Silver: Rows I-N).
10. **`seats`**: Individual physical seats within a screen defined by row labels (A-N), seat numbers, and seat types (`normal`, `aisle_gap`, `blocked`, `couple`).
11. **`seat_locks`**: Temporary or permanent seat reservations for a show. Contains a composite partial index `idx_show_seat_held` on `(show_id, seat_id)` where `status='held'` to enforce atomic seat holding.
12. **`bookings`**: Ticket reservation orders tracking unique booking codes (e.g., `BB7K2M4X`), ticket amounts, food amounts, convenience fees, GST, total paid, and booking status (`pending`, `confirmed`, `cancelled`, `expired`).
13. **`food_items`**: Concession menu items categorized into Popcorn, Beverages, Combos, and Snacks, storing veg/non-veg flags and prices.
14. **`booking_food`**: Junction table mapping food items and quantities to specific bookings.
15. **`chat_logs`**: Logs user interactions and AI rule-based assistant responses for auditing and persistent memory.

---

## 4. MODULE DETAILS & ALGORITHMS

### 4.1 Geolocation Distance Algorithm (Haversine Formula)
When a user clicks "Detect My Location", client-side JS captures latitude and longitude via `navigator.geolocation` and posts to `/api/detect-city`. The server computes the great-circle distance to all database cities using the Haversine formula:

$$d = 2r \arcsin \left( \sqrt{ \sin^2 \left( \frac{\Delta \phi}{2} \right) + \cos(\phi_1) \cos(\phi_2) \sin^2 \left( \frac{\Delta \lambda}{2} \right) } \right)$$

The city with the minimum distance $d$ is set as the active session city.

### 4.2 Concurrency-Safe Seat Lock & Release Algorithm
1. **Hold Request**: When a user selects seats and clicks "Proceed to Pay", an explicit database transaction is opened.
2. **Conflict Check**: A query checks for any active `SeatLock` records where `show_id` and `seat_id` match and `status IN ('held', 'converted')` with `expires_at > datetime.utcnow()`.
3. **Atomic Commit**: If no conflict exists, new `SeatLock` records are inserted with `status='held'` and `expires_at = datetime.utcnow() + timedelta(minutes=4)`. A `Booking` record with `status='pending'` is created.
4. **Background Cleanup Routine**: An APScheduler thread executes every 30 seconds to clean up orphaned locks:
   - Sets `SeatLock.status = 'expired'` for all held locks where `expires_at <= now`.
   - Sets `Booking.status = 'expired'` for pending bookings created more than 4 minutes ago.

### 4.3 Rule-Based Chatbot Engine ("Bingyy")
The chatbot operates on keyword pattern matching supporting both English and Hindi. Intents handled include:
- Greetings (`hi`, `hello`, `namaste`, `नमस्ते`)
- Booking Steps (`how to book`, `ticket`, `बुक`)
- Cancellation Policy (`cancel`, `refund`, `रद्द`)
- Hold Timer Explanation (`hold`, `timing`, `4 min`, `4 मिनट`)
- Payment Options (`payment`, `upi`, `card`, `पेमेंट`)
- Food & Snacks (`food`, `popcorn`, `खाना`, `पॉपकॉर्न`)
- Human Agent Escalation (`human`, `agent`, `7888081697`, `कॉल`) -> Returns `"Call our 24/7 customer care: 7888081697"`.

---

## 5. FLOW OF A BOOKING

```
[1. Home Page] ---> [2. Location Detection] ---> [3. Movie Details]
                                                         |
                                                         v
[6. Digital Ticket] <-- [5. Mock Payment] <-- [4. Food & Snacks] <-- [3b. Seat Map Selection]
   (QR Code + PNG)       (UPI / Card)            (Popcorn/Pepsi)       (4-Min Hold Timer)
```

1. **Movie Selection**: User navigates home page or filters by city, selecting a movie (e.g. *Kalki 2898 AD*).
2. **Showtime Selection**: User chooses a date from the 7-day date strip, picks a theatre (e.g. *PVR Kirti Mall, Jalgaon*), and selects a showtime (e.g. *04:05 PM*).
3. **Seat Selection**: User selects seat count (e.g. 2 seats) and picks seats on the interactive auditorium map (e.g. *C5, C6* in Gold Category). Clicking Pay creates a 4-minute hold.
4. **Food Addons**: User optionally adds Salted Popcorn and Pepsi to the order. Timer updates grand total in real-time.
5. **Checkout**: User enters mock UPI or Card credentials and clicks "Pay Now". A 2-second spinner simulates gateway processing.
6. **Ticket Generation**: Booking turns `confirmed`, seat locks convert, and a digital ticket card is displayed complete with a scannable QR code and downloadable PNG export button.

---

## 6. VERIFICATION & TEST RESULTS

1. **Database Seeding**: Verified `seed.py` successfully populates 26 cities (including Jalgaon), 10+ theatres, 20 movies, 7-day shows, 14 food items, admin/demo users, and presold seats without relational integrity errors.
2. **Multi-Tab Concurrency**: Verified that holding a seat in Browser Tab 1 immediately displays that seat as held/hatched in Browser Tab 2 upon 5-second polling.
3. **Timer Expiration**: Verified that waiting 4 minutes without completing payment releases held seats automatically and updates booking status to `expired`.
4. **Admin Dashboard**: Verified chart rendering for 7-day revenue lines and top movie bars via Chart.js.

---

## 7. FUTURE SCOPE

1. Integration of WebSockets (Flask-SocketIO) for real-time instant seat updates without HTTP polling overhead.
2. Addition of dynamic pricing algorithms based on demand curves and showtime proximity.
3. Implementation of progressive web app (PWA) offline wallet storage for saved digital tickets.
