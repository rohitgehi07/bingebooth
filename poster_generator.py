import os
import math
from PIL import Image, ImageDraw, ImageFont

# Define color schemes per genre: (top_color, mid_color, bottom_color, accent_color)
GENRE_PALETTES = {
    'action': ((60, 5, 5), (180, 20, 20), (15, 2, 2), (255, 215, 0)),
    'sci-fi': ((8, 12, 40), (80, 20, 180), (0, 210, 255), (0, 255, 255)),
    'romance': ((50, 0, 35), (190, 20, 120), (25, 0, 15), (255, 182, 193)),
    'horror': ((2, 24, 16), (25, 75, 60), (5, 5, 5), (0, 255, 100)),
    'thriller': ((15, 15, 30), (70, 40, 120), (5, 5, 15), (255, 165, 0)),
    'comedy': ((70, 35, 0), (230, 120, 20), (240, 195, 15), (255, 255, 255)),
    'drama': ((40, 10, 50), (120, 40, 140), (15, 5, 20), (230, 200, 255)),
    'classic': ((45, 10, 0), (115, 20, 20), (18, 4, 0), (212, 175, 55)),
    'default': ((40, 10, 80), (124, 58, 237), (236, 72, 153), (244, 114, 182))
}

def get_font(size, bold=True):
    font_names = ['arialbd.ttf', 'segoeuib.ttf', 'impact.ttf', 'georgiab.ttf', 'arial.ttf']
    for name in font_names:
        win_path = os.path.join('C:/Windows/Fonts', name)
        if os.path.exists(win_path):
            try:
                return ImageFont.truetype(win_path, size)
            except Exception:
                pass
    return ImageFont.load_default()

def interpolate_color(c1, c2, factor):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * factor) for i in range(3))

def get_palette_for_movie(slug, genres, is_classic=False):
    if is_classic:
        key = 'classic'
    else:
        genres_lower = genres.lower() if genres else ''
        key = 'default'
        for g in ['action', 'sci-fi', 'romance', 'horror', 'thriller', 'comedy', 'drama']:
            if g in genres_lower:
                key = g
                break

    top_c, mid_c, bot_c, acc_c = GENRE_PALETTES[key]
    
    # Introduce small hash-based variation so no two posters of same genre are identical
    h = sum(ord(ch) for ch in slug) % 25
    top_c = tuple(min(255, max(0, c + (h if i==0 else -h//2))) for i, c in enumerate(top_c))
    mid_c = tuple(min(255, max(0, c + (h if i==1 else h//2))) for i, c in enumerate(mid_c))

    return top_c, mid_c, bot_c, acc_c, key

def generate_poster_image(title, slug, genres, rating, year=None, is_classic=False):
    width, height = 500, 750
    img = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(img)

    top_c, mid_c, bot_c, acc_c, palette_key = get_palette_for_movie(slug, genres, is_classic)

    # 1. Background Gradient
    for y in range(height):
        factor = y / height
        if factor < 0.5:
            color = interpolate_color(top_c, mid_c, factor * 2.0)
        else:
            color = interpolate_color(mid_c, bot_c, (factor - 0.5) * 2.0)
        draw.line([(0, y), (width, y)], fill=color)

    # 2. Draw Decorative Emblem Artwork in Upper 2/3
    center_x, center_y = width // 2, 260

    if palette_key == 'classic':
        # Double gold circle with vintage diamond starburst
        for r in [130, 115, 100, 85]:
            draw.ellipse([center_x - r, center_y - r, center_x + r, center_y + r], outline=acc_c, width=2)
        # Inner starburst rays
        for angle in range(0, 360, 30):
            rad = math.radians(angle)
            x1 = center_x + int(40 * math.cos(rad))
            y1 = center_y + int(40 * math.sin(rad))
            x2 = center_x + int(80 * math.cos(rad))
            y2 = center_y + int(80 * math.sin(rad))
            draw.line([(x1, y1), (x2, y2)], fill=acc_c, width=2)

    elif palette_key in ['action', 'sci-fi']:
        # Sci-Fi / Action aperture glowing geometric shield
        for r in [140, 120, 100, 75]:
            draw.ellipse([center_x - r, center_y - r, center_x + r, center_y + r], outline=acc_c if r % 40 == 0 else mid_c, width=3)
        # Crosshair lines
        draw.line([(center_x - 150, center_y), (center_x + 150, center_y)], fill=acc_c, width=1)
        draw.line([(center_x, center_y - 150), (center_x, center_y + 150)], fill=acc_c, width=1)
        # Polygon diamond crest
        points = [
            (center_x, center_y - 60),
            (center_x + 60, center_y),
            (center_x, center_y + 60),
            (center_x - 60, center_y)
        ]
        draw.polygon(points, outline=acc_c, fill=None)

    elif palette_key == 'romance':
        # Dual glowing overlapping heart-crest rings
        for offset in [-30, 30]:
            draw.ellipse([center_x + offset - 70, center_y - 70, center_x + offset + 70, center_y + 70], outline=acc_c, width=3)
        draw.ellipse([center_x - 100, center_y - 100, center_x + 100, center_y + 100], outline=(255, 255, 255), width=1)

    elif palette_key == 'comedy':
        # Bright sunburst / star emblem
        for r in range(30, 130, 20):
            draw.ellipse([center_x - r, center_y - r, center_x + r, center_y + r], outline=acc_c, width=2)
        for angle in range(0, 360, 45):
            rad = math.radians(angle)
            x2 = center_x + int(110 * math.cos(rad))
            y2 = center_y + int(110 * math.sin(rad))
            draw.line([(center_x, center_y), (x2, y2)], fill=acc_c, width=2)

    else: # horror, thriller, default
        # Modern BingeBooth glowing emblem rings
        for r in range(40, 140, 25):
            draw.ellipse([center_x - r, center_y - r, center_x + r, center_y + r], outline=acc_c, width=2)

    # 3. Top Header Badge
    font_badge = get_font(14, bold=True)
    header_text = "BINGEBOOTH CLASSICS VAULT" if is_classic else "BINGEBOOTH CINEMA PRESENTS"
    draw.text((width // 2, 35), header_text, font=font_badge, fill=acc_c, anchor="mm")

    # Format / Year Badge under emblem
    if year:
        sub_badge = f"{year} • {genres.split(',')[0].upper() if genres else 'CINEMA'}"
    else:
        sub_badge = f"★ {rating} / 10 • {genres.split(',')[0].upper() if genres else 'CINEMA'}"
    draw.text((width // 2, center_y + 130), sub_badge, font=font_badge, fill=(240, 240, 240), anchor="mm")

    # 4. Movie Title in Lower 1/3
    font_title = get_font(32, bold=True)
    words = title.split()
    lines = []
    current_line = []
    for word in words:
        test_line = ' '.join(current_line + [word])
        bbox = font_title.getbbox(test_line) if hasattr(font_title, 'getbbox') else (0, 0, len(test_line)*18, 32)
        line_w = bbox[2] - bbox[0]
        if line_w > 420 and current_line:
            lines.append(' '.join(current_line))
            current_line = [word]
        else:
            current_line.append(word)
    if current_line:
        lines.append(' '.join(current_line))

    # Calculate starting Y position for title block
    line_height = 38
    total_title_h = len(lines) * line_height
    start_y = 570 - (total_title_h // 2)

    for i, line in enumerate(lines):
        y_pos = start_y + (i * line_height)
        # Drop shadow
        draw.text((width // 2 + 2, y_pos + 2), line, font=font_title, fill=(0, 0, 0), anchor="mm")
        draw.text((width // 2, y_pos), line, font=font_title, fill=(255, 255, 255), anchor="mm")

    # Rating / Language Footer Bar
    font_footer = get_font(13, bold=True)
    footer_str = f"RATING: ★ {rating}   •   {genres if genres else 'BLOCKBUSTER'}"
    draw.text((width // 2, 705), footer_str, font=font_footer, fill=acc_c, anchor="mm")

    # 5. Inset Border Frame
    draw.rectangle([12, 12, width - 12, height - 12], outline=acc_c, width=3)

    os.makedirs('static/img/posters', exist_ok=True)
    out_path = f"static/img/posters/{slug}.jpg"
    img.save(out_path, quality=92)
    return f"/{out_path}"

def generate_banner_image(title, slug, genres, rating, year=None, is_classic=False):
    width, height = 1600, 600
    img = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(img)

    top_c, mid_c, bot_c, acc_c, palette_key = get_palette_for_movie(slug, genres, is_classic)

    # 1. Horizontal/Diagonal Gradient
    for x in range(width):
        factor = x / width
        if factor < 0.5:
            color = interpolate_color(top_c, mid_c, factor * 2.0)
        else:
            color = interpolate_color(mid_c, bot_c, (factor - 0.5) * 2.0)
        draw.line([(x, 0), (x, height)], fill=color)

    # 2. Right Side Emblem Artwork
    center_x, center_y = 1200, 300
    for r in [220, 180, 140, 100, 60]:
        draw.ellipse([center_x - r, center_y - r, center_x + r, center_y + r], outline=acc_c if r % 80 == 0 else mid_c, width=3)

    for angle in range(0, 360, 30):
        rad = math.radians(angle)
        x2 = center_x + int(200 * math.cos(rad))
        y2 = center_y + int(200 * math.sin(rad))
        draw.line([(center_x, center_y), (x2, y2)], fill=acc_c, width=1)

    # 3. Left Side Content
    font_badge = get_font(20, bold=True)
    header_text = "BINGEBOOTH CLASSICS VAULT" if is_classic else "NOW SHOWING IN THEATRES"
    draw.text((100, 120), header_text, font=font_badge, fill=acc_c)

    # Title
    font_title = get_font(56, bold=True)
    draw.text((102, 222), title, font=font_title, fill=(0, 0, 0))
    draw.text((100, 220), title, font=font_title, fill=(255, 255, 255))

    # Subtitle / Details
    font_sub = get_font(24, bold=True)
    sub_text = f"★ {rating} / 10 IMDb   |   GENRE: {genres}   |   EXPERIENCE IN 4K DOLBY"
    if year:
        sub_text = f"RELEASED {year}   |   {sub_text}"
    draw.text((100, 320), sub_text, font=font_sub, fill=(230, 230, 230))

    # Tagline button bar
    draw.rectangle([100, 410, 380, 470], fill=acc_c)
    font_btn = get_font(20, bold=True)
    draw.text((240, 440), "EXPLORE NOW", font=font_btn, fill=(0, 0, 0), anchor="mm")

    # Inset Border
    draw.rectangle([20, 20, width - 20, height - 20], outline=acc_c, width=4)

    os.makedirs('static/img/banners', exist_ok=True)
    out_path = f"static/img/banners/{slug}.jpg"
    img.save(out_path, quality=92)
    return f"/{out_path}"
