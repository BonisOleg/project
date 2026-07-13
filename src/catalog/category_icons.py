"""Готові іконки категорій (ключ → підпис для адмінки)."""

CATEGORY_ICON_CHOICES = (
    ('home', 'Дім'),
    ('suitcase', 'Валіза'),
    ('chair', 'Крісло'),
    ('tools', 'Інструменти'),
    ('kids', 'Дитячі товари'),
    ('sport', 'Спорт'),
    ('tractor', 'Трактор'),
    ('pet', 'Зоотовари'),
    ('sale', 'Уцінка'),
    ('garage', 'СТО / авто'),
    ('grid', 'Загальна (сітка)'),
    ('star', 'Зірка'),
)

# slug → icon_key для міграції існуючих категорій
SLUG_TO_ICON_KEY = {
    'dim-i-sad': 'home',
    'valizy': 'suitcase',
    'krisla': 'chair',
    'budivnytstvo': 'tools',
    'dytiachi': 'kids',
    'sport': 'sport',
    'traktory': 'tractor',
    'zootovary': 'pet',
    'utsineni': 'sale',
    'sto': 'garage',
}

DEFAULT_CATEGORY_COLOR = '#2453E0'
