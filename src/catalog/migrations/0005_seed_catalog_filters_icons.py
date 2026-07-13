# Generated manually after 0004 schema migration

from django.db import migrations


def seed_filters_and_icons(apps, schema_editor):
    CatalogFilter = apps.get_model('catalog', 'CatalogFilter')
    Category = apps.get_model('catalog', 'Category')

    slug_icons = {
        'dim-i-sad': ('home', '#2BBD7E'),
        'valizy': ('suitcase', '#2453E0'),
        'krisla': ('chair', '#FF6A3D'),
        'budivnytstvo': ('tools', '#2453E0'),
        'dytiachi': ('kids', '#FFC93C'),
        'sport': ('sport', '#FF6A3D'),
        'traktory': ('tractor', '#2BBD7E'),
        'zootovary': ('pet', '#C99200'),
        'utsineni': ('sale', '#FF3B5C'),
        'sto': ('garage', '#2453E0'),
    }
    for slug, (icon_key, color) in slug_icons.items():
        Category.objects.filter(slug=slug).update(icon_key=icon_key, color=color)

    if CatalogFilter.objects.exists():
        return

    defaults = [
        ('Бренд', 'brand', '', '', 10, False),
        ('Ціна, грн', 'price', '', '', 20, True),
        ('Вид', 'category', '', '', 30, False),
        ('Форма', 'attribute', 'Форма', 'Кругла\nКвадратна\nОвальна\nКласична\nПрямокутна', 40, False),
        ('Максимальне навантаження', 'attribute', 'Максимальне навантаження', '100 кг\n120 кг\n150 кг\n200 кг', 50, False),
        ('Діаметр, см', 'attribute', 'Діаметр, см', '244\n252\n312\n374\n404', 60, False),
        ('Колір', 'attribute', 'Колір', 'Білий\nЧорний\nСірий\nБежевий\nРожевий', 70, False),
        ('Країна-виробник товару', 'attribute', 'Країна-виробник товару', 'Україна\nКитай\nПольща', 80, False),
        ('Країна реєстрації бренду', 'attribute', 'Країна реєстрації бренду', 'Україна\nКитай', 90, False),
        ('Наявність', 'in_stock', '', '', 200, False),
    ]
    for name, ftype, attr, fallback, order, opened in defaults:
        CatalogFilter.objects.create(
            name=name,
            filter_type=ftype,
            attribute_name=attr,
            fallback_values=fallback,
            sort_order=order,
            is_active=True,
            open_by_default=opened,
        )


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0004_category_icon_color_catalogfilter'),
    ]

    operations = [
        migrations.RunPython(seed_filters_and_icons, noop),
    ]
