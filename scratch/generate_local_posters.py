import os
import zlib
import struct

def make_png_poster(width=400, height=600, bg_rgb=(124, 58, 237)):
    """Generate a minimal valid PNG poster with background color"""
    def chunk(tag, data):
        return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)
    
    ihdr = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    raw = b''
    r, g, b = bg_rgb
    for _ in range(height):
        raw += b'\x00' + bytes([r, g, b]) * width
    compressed = zlib.compress(raw)
    
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', ihdr) + chunk(b'IDAT', compressed) + chunk(b'IEND', b'')

def generate_svg_poster(title, subtitle, tag, color1, color2):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 600" width="100%" height="100%">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{color1}"/>
      <stop offset="100%" stop-color="{color2}"/>
    </linearGradient>
    <linearGradient id="accent" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#7C3AED"/>
      <stop offset="100%" stop-color="#EC4899"/>
    </linearGradient>
  </defs>
  <rect width="400" height="600" fill="url(#bg)"/>
  
  <!-- Film Reel Header Icon -->
  <g transform="translate(160, 80) scale(1.6)" fill="none" stroke="#FFFFFF" stroke-width="2" opacity="0.9">
    <rect x="2" y="2" width="44" height="44" rx="8" fill="#18181B" opacity="0.4"/>
    <circle cx="24" cy="24" r="14" stroke="url(#accent)" stroke-width="3"/>
    <circle cx="24" cy="24" r="4" fill="#EC4899"/>
  </g>

  <!-- Cinema Badge -->
  <rect x="130" y="200" width="140" height="26" rx="13" fill="url(#accent)"/>
  <text x="200" y="217" font-family="system-ui, sans-serif" font-weight="800" font-size="11" fill="#FFFFFF" text-anchor="middle" letter-spacing="1.5">{tag.upper()}</text>

  <!-- Movie Title -->
  <text x="200" y="320" font-family="system-ui, sans-serif" font-weight="900" font-size="26" fill="#FFFFFF" text-anchor="middle">{title}</text>
  
  <rect x="150" y="345" width="100" height="3" fill="url(#accent)" rx="1.5"/>

  <!-- Subtitle / Genre -->
  <text x="200" y="380" font-family="system-ui, sans-serif" font-weight="600" font-size="14" fill="#E9D5FF" text-anchor="middle">{subtitle}</text>
  
  <!-- Footer Branding -->
  <text x="200" y="540" font-family="system-ui, sans-serif" font-weight="800" font-size="14" fill="#FFFFFF" text-anchor="middle" letter-spacing="2">BINGEBOOTH CINEMA</text>
  <text x="200" y="560" font-family="system-ui, sans-serif" font-weight="500" font-size="11" fill="#9CA3AF" text-anchor="middle">Official Release</text>
</svg>'''

movies_meta = [
    ("kalki-2898-ad", "Kalki 2898 AD", "Sci-Fi • Action • Fantasy", "NOW SHOWING", "#1e1b4b", "#4c1d95"),
    ("stree-2", "Stree 2", "Horror • Comedy", "NOW SHOWING", "#311042", "#701a75"),
    ("jawan-duty", "Jawan: Ultimate Duty", "Action • Thriller", "NOW SHOWING", "#450a0a", "#991b1b"),
    ("animal-bloodline", "Animal: Bloodline", "Action • Crime • Drama", "NOW SHOWING", "#171717", "#44403c"),
    ("fighter-warriors", "Fighter", "Action • Air Force", "NOW SHOWING", "#0c4a6e", "#0369a1"),
    ("brahmastra-dev", "Brahmastra: Dev", "Fantasy • Adventure", "NOW SHOWING", "#1e1b4b", "#6b21a8"),
    ("dunki-home", "Dunki: Long Way Home", "Comedy • Drama", "NOW SHOWING", "#064e3b", "#047857"),
    ("leo-sweet", "Leo: Bloody Sweet", "Action • Crime", "NOW SHOWING", "#450a0a", "#7f1d1d"),
    ("war-2", "War 2", "Action • Spy Thriller", "UPCOMING", "#1e293b", "#334155"),
    ("singham-again", "Singham Again", "Action • Cop Universe", "UPCOMING", "#7c2d12", "#9a3412"),
    ("pushpa-2", "Pushpa 2: The Rule", "Action • Smuggling Empire", "UPCOMING", "#451a03", "#78350f"),
    ("kanguva", "Kanguva", "Historical • Fantasy", "UPCOMING", "#3b0764", "#581c87"),
    ("devara-part-1", "Devara: Part 1", "Action • Coastal Drama", "UPCOMING", "#0f172a", "#1e293b"),
    ("avatar-3", "Avatar: Fire and Ash", "Sci-Fi • Pandora Saga", "UPCOMING", "#064e3b", "#0f766e"),
    ("sholay", "Sholay (1975)", "Action • Classic Masterpiece", "CLASSIC ARCHIVE", "#78350f", "#b45309"),
    ("mughal-e-azam", "Mughal-e-Azam", "Epic Romance • Classic", "CLASSIC ARCHIVE", "#581c87", "#7e22ce"),
    ("mother-india", "Mother India", "Drama • Classic Masterpiece", "CLASSIC ARCHIVE", "#831843", "#be185d"),
    ("anand", "Anand (1971)", "Drama • Heartwarming Classic", "CLASSIC ARCHIVE", "#14532d", "#15803d"),
    ("deewaar", "Deewaar (1975)", "Crime Drama • Cult Classic", "CLASSIC ARCHIVE", "#1e293b", "#475569"),
    ("chupke-chupke", "Chupke Chupke", "Comedy • Classic Masterpiece", "CLASSIC ARCHIVE", "#701a75", "#a21caf"),
    ("placeholder", "BingeBooth Cinema", "Poster Coming Soon", "OFFICIAL CINEMA", "#1e1b4b", "#4c1d95")
]

os.makedirs('static/img/posters', exist_ok=True)

for slug, title, sub, tag, c1, c2 in movies_meta:
    # Write SVG file
    svg_data = generate_svg_poster(title, sub, tag, c1, c2)
    with open(f'static/img/posters/{slug}.svg', 'w', encoding='utf-8') as f:
        f.write(svg_data)
    
    # Write PNG/JPG binary file so both .jpg and .png paths serve valid image bytes
    png_bytes = make_png_poster(400, 600, (124, 58, 237))
    with open(f'static/img/posters/{slug}.jpg', 'wb') as f:
        f.write(png_bytes)
    with open(f'static/img/posters/{slug}.png', 'wb') as f:
        f.write(png_bytes)

print(f"Generated local posters for {len(movies_meta)} movies successfully!")
