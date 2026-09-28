# BingeBooth — Production-Quality Movie Ticket Booking Application

BingeBooth is a full-featured, offline-capable, production-grade movie ticket booking web application built from scratch for a college final project submission.

---

## 🌟 Key Features

1. **Original Visual Identity**: Dark-first cinematic aesthetic (`#0B0B12` background, `#15151F` card surface, `#7C3AED` to `#EC4899` violet-magenta primary accent, `#F59E0B` secondary amber rating accent). Zero BookMyShow styling.
2. **Offline Localhost Ready**: Runs 100% offline without external paid APIs (no Stripe, no Firebase, no paid auth). Uses CDN dependencies for Tailwind CSS, Alpine.js, Lucide Icons, Chart.js, QRCode.js, and html2canvas.
3. **Smart Location Detector**: Auto-detects nearest city using browser Geolocation and the Haversine distance formula against 8 Metros & 18 Maharashtra districts (including **Jalgaon** with PVR Kirti Mall, Star Multiplex, Regal Metro, and INOX Golani Market).
4. **Realistic Auditorium Seat Selection**:
   - Curved *SCREEN THIS WAY* neon glow element.
   - Realistic row layout (A-N) with aisle gaps.
   - Price category blocks (Recliner, Gold, Silver).
   - Real-time 5-second polling of seat availability states (Available, Selected, Sold, Held).
5. **Atomic 4-Minute Seat Lock & Auto-Release**:
   - 4-minute timer (MM:SS) during checkout.
   - APScheduler background job running every 30 seconds releases expired seat holds and pending bookings automatically.
   - Database transactions prevent double-booking race conditions.
6. **Food & Beverage Pre-Ordering**: 14 items (Popcorn, Beverages, Combos, Snacks) with quantity steppers and cart calculation.
7. **Digital Ticket with QR Code & Download**: Generates a perforated edge ticket with a QR code and instant PNG download via `html2canvas`.
8. **Bilingual i18n Support**: Full English and Hindi (हिंदी) language toggle persisted in session and `localStorage`. Movie titles and descriptions support Hindi translations.
9. **"Bingyy" Rule-Based Chatbot**: Floating assistant answering booking steps, cancellation policies, seat hold timing, snacks menu, and routing to 24/7 helpline `7888081697`.
10. **Comprehensive Admin Dashboard**: Login-protected control panel with Chart.js revenue line charts, top-performing movie bar charts, and CRUD management for movies, theatres, screens, shows, bookings, users, and food items.

---

## 🛠️ Tech Stack

- **Backend**: Python 3.10+ & Flask 3.0
- **Database**: SQLite with SQLAlchemy ORM
- **Authentication**: Flask-Login + Werkzeug `scrypt` password hashing
- **Background Jobs**: APScheduler
- **Templating**: Jinja2 with server-rendered pages and custom `t()` i18n global helper
- **Frontend**: HTML5, Tailwind CSS (CDN), Alpine.js (CDN), Lucide Icons (CDN), Vanilla JavaScript

---

## 📂 Project Structure

```
bingebooth/
├── app.py                  # App factory + config + i18n + APScheduler
├── run.py                  # Application entry point
├── requirements.txt        # Pinned Python dependencies
├── models.py               # SQLAlchemy ORM database models
├── seed.py                 # Database seeder (movies, theatres, shows, seats, food, users)
├── extensions.py           # SQLAlchemy, LoginManager, and APScheduler instances
├── routes/
│   ├── __init__.py
│   ├── main.py             # Home, movie detail, showtimes, reviews
│   ├── auth.py             # Register, login, logout, profile, cancellation
│   ├── booking.py          # Seat map, hold, food, mock payment, digital ticket
│   ├── admin.py            # Admin dashboard metrics, charts & CRUD
│   └── api.py              # Geolocation distance, seat status polling, chatbot, i18n
├── static/
│   ├── css/custom.css      # Dark cinematic theme, curved screen glow, ticket edges
│   ├── js/seatmap.js       # Seat selection & 5s live polling
│   ├── js/holdtimer.js     # 4-minute countdown timer
│   ├── js/chatbot.js       # Floating Bingyy chatbot assistant
│   ├── js/i18n.js          # Language switcher
│   └── js/location.js      # City modal & Haversine distance detection
├── templates/
│   ├── base.html
│   ├── partials/           # Navbar, footer, chatbot, movie_card, toast
│   ├── index.html
│   ├── movie_detail.html
│   ├── showtimes.html
│   ├── seat_select.html
│   ├── food.html
│   ├── payment.html
│   ├── ticket.html
│   ├── auth/               # login.html, register.html, profile.html
│   └── admin/              # dashboard.html, movies.html, theatres.html, shows.html, bookings.html, users.html
├── translations/
│   ├── en.json
│   └── hi.json
└── instance/bingebooth.db
```

---

## 🚀 How to Run locally

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Seed / Reset Database
```bash
python seed.py
```

### 3. Launch Application
```bash
python run.py
```
Open your browser and navigate to: `http://127.0.0.1:5000`

---

## 🔑 Demo Credentials

| Role | Email | Password |
|---|---|---|
| **Admin User** | `admin@bingebooth.com` | `Admin@123` |
| **Demo Customer** | `demo@bingebooth.com` | `Demo@123` |

---

## 📞 Customer Support
For any booking assistance, call our 24/7 customer care helpline: **7888081697**
