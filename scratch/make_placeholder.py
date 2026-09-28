import zlib, struct, os

def make_png(width, height, color_rgb):
    def chunk(tag, data):
        return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)
    
    ihdr = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    raw = b''
    r, g, b = color_rgb
    for _ in range(height):
        raw += b'\x00' + bytes([r, g, b]) * width
    compressed = zlib.compress(raw)
    
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', ihdr) + chunk(b'IDAT', compressed) + chunk(b'IEND', b'')

os.makedirs('static/img/posters', exist_ok=True)
png_data = make_png(400, 600, (76, 29, 149)) # Purple color
with open('static/img/posters/placeholder.png', 'wb') as f:
    f.write(png_data)
with open('static/img/posters/placeholder.jpg', 'wb') as f:
    f.write(png_data)

svg_content = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 600" width="100%" height="100%">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#1e1b4b"/>
      <stop offset="50%" stop-color="#4c1d95"/>
      <stop offset="100%" stop-color="#831843"/>
    </linearGradient>
    <linearGradient id="accent" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#7C3AED"/>
      <stop offset="100%" stop-color="#EC4899"/>
    </linearGradient>
  </defs>
  <rect width="400" height="600" fill="url(#bg)"/>
  <circle cx="200" cy="220" r="70" fill="url(#accent)" opacity="0.2"/>
  <g transform="translate(165, 185) scale(1.5)" fill="none" stroke="#A855F7" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <rect x="2" y="2" width="44" height="44" rx="6" fill="#2e1065"/>
    <path d="M16 2v44M32 2v44M2 16h44M2 32h44"/>
  </g>
  <text x="200" y="340" font-family="system-ui, sans-serif" font-weight="800" font-size="28" fill="#FFFFFF" text-anchor="middle" letter-spacing="1">BingeBooth</text>
  <rect x="120" y="360" width="160" height="3" fill="url(#accent)" rx="1.5"/>
  <text x="200" y="400" font-family="system-ui, sans-serif" font-weight="600" font-size="16" fill="#C084FC" text-anchor="middle">POSTER COMING SOON</text>
  <text x="200" y="430" font-family="system-ui, sans-serif" font-weight="400" font-size="13" fill="#9CA3AF" text-anchor="middle">Official Cinema Release</text>
</svg>"""

with open('static/img/posters/placeholder.svg', 'w', encoding='utf-8') as f:
    f.write(svg_content)

print("Placeholder files created successfully!")
