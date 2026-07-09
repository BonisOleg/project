from PIL import Image, ImageDraw, ImageFilter, ImageFont

SIZE = (1920, 1080)

SLIDE_THEMES = {
    'BAT374': {
        'gradient': ((34, 120, 78), (74, 168, 214), (255, 214, 120)),
        'orbs': ((255, 255, 255, 70), (255, 180, 90, 90), (40, 90, 60, 110)),
        'label': 'Спорт і відпочинок',
    },
    'B173': {
        'gradient': ((245, 236, 220), (214, 186, 150), (168, 132, 98)),
        'orbs': ((255, 255, 255, 85), (255, 230, 200, 70), (120, 90, 70, 60)),
        'label': 'Кухонні крісла',
    },
    'B619': {
        'gradient': ((24, 44, 92), (52, 88, 168), (120, 156, 220)),
        'orbs': ((255, 255, 255, 55), (80, 120, 220, 90), (20, 30, 70, 100)),
        'label': 'Офісні крісла',
    },
    'P9040': {
        'gradient': ((58, 62, 70), (110, 116, 126), (180, 186, 196)),
        'orbs': ((255, 255, 255, 45), (90, 96, 108, 100), (40, 44, 52, 120)),
        'label': 'Металеві стелажі',
    },
    'VAL28': {
        'gradient': ((255, 106, 61), (255, 160, 90), (36, 83, 224)),
        'orbs': ((255, 255, 255, 75), (255, 220, 180, 80), (30, 60, 180, 90)),
        'label': 'Дорожні валізи',
    },
}


def _linear_gradient(size, top_color, bottom_color):
    width, height = size
    base = Image.new('RGB', size, top_color)
    draw = ImageDraw.Draw(base)
    for y in range(height):
        ratio = y / max(height - 1, 1)
        color = tuple(
            int(top_color[channel] + (bottom_color[channel] - top_color[channel]) * ratio)
            for channel in range(3)
        )
        draw.line([(0, y), (width, y)], fill=color)
    return base


def _draw_orb(canvas, center, radius, color):
    overlay = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.ellipse(
        (center[0] - radius, center[1] - radius, center[0] + radius, center[1] + radius),
        fill=color,
    )
    blurred = overlay.filter(ImageFilter.GaussianBlur(radius=radius * 0.22))
    return Image.alpha_composite(canvas.convert('RGBA'), blurred)


def _load_font(size: int):
    try:
        return ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', size)
    except OSError:
        try:
            return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', size)
        except OSError:
            return ImageFont.load_default()


def generate_product_slide(sku: str, product_name: str) -> Image.Image:
    theme = SLIDE_THEMES.get(sku, SLIDE_THEMES['BAT374'])
    colors = theme['gradient']
    canvas = _linear_gradient(SIZE, colors[0], colors[2])
    canvas = canvas.convert('RGBA')

    orb_specs = (
        (0.78, 0.28, 360),
        (0.62, 0.72, 280),
        (0.22, 0.42, 220),
    )
    for orb_color, (x_ratio, y_ratio, radius) in zip(theme['orbs'], orb_specs, strict=True):
        center = (int(SIZE[0] * x_ratio), int(SIZE[1] * y_ratio))
        canvas = _draw_orb(canvas, center, radius, orb_color)

    draw = ImageDraw.Draw(canvas)
    title_font = _load_font(78)
    subtitle_font = _load_font(42)
    badge_font = _load_font(34)

    draw.rounded_rectangle((96, 96, 430, 168), radius=36, fill=(255, 255, 255, 210))
    draw.text((128, 118), 'OYRA', fill=(36, 83, 224, 255), font=badge_font)
    draw.text((96, 260), theme['label'], fill=(255, 255, 255, 235), font=subtitle_font)

    wrapped_name = product_name if len(product_name) <= 34 else f'{product_name[:31]}...'
    draw.text((96, 340), wrapped_name, fill=(255, 255, 255, 255), font=title_font)

    accent = Image.new('RGBA', SIZE, (0, 0, 0, 0))
    accent_draw = ImageDraw.Draw(accent)
    accent_draw.polygon(
        [(0, SIZE[1]), (0, int(SIZE[1] * 0.55)), (int(SIZE[0] * 0.42), SIZE[1])],
        fill=(20, 24, 43, 55),
    )
    canvas = Image.alpha_composite(canvas, accent)

    return canvas.convert('RGB')
