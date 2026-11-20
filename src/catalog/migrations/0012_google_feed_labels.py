from django.db import migrations, models


WINTER_NAMES = ('Генератори', 'Печі і каміни')
SPRING_NAMES = (
    'Теплиці',
    'Садові гойдалки',
    'Шезлонги',
    'Садові та пляжні парасольки',
    'Садові павільйони, альтанки',
    'Підвісні крісла та гамаки',
    'Електронасос для SUP-дошки',
    'Аксесуари для батутів',
    'Батути',
    'Самокати',
)


def seed_feed_seasons(apps, schema_editor):
    Category = apps.get_model('catalog', 'Category')
    Category.objects.filter(name__in=WINTER_NAMES).update(feed_season='winter')
    Category.objects.filter(name__in=SPRING_NAMES).update(feed_season='spring_summer')


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0011_supplier_and_stock'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='feed_season',
            field=models.CharField(
                blank=True,
                choices=[
                    ('', 'Як у батьківської'),
                    ('winter', 'Зима'),
                    ('spring_summer', 'Весна-літо'),
                    ('all_season', 'Всесезон'),
                ],
                default='',
                help_text=(
                    'Порожнє значення бере сезон батьківської категорії. '
                    '«Всесезон» зупиняє спадковість.'
                ),
                max_length=20,
                verbose_name='Сезонність (custom_label_2)',
            ),
        ),
        migrations.AddField(
            model_name='product',
            name='feed_priority',
            field=models.CharField(
                blank=True,
                choices=[
                    ('', 'Авто'),
                    ('generators', 'Генератори'),
                    ('hit', 'Хіт'),
                    ('standard', 'Стандарт'),
                ],
                default='',
                help_text=(
                    'Порожнє: категорія «Генератори» → Генератори, '
                    'інакше галочка «Хіт продажу» → Хіт, інакше Стандарт.'
                ),
                max_length=20,
                verbose_name='Пріоритет (custom_label_3)',
            ),
        ),
        migrations.RunPython(seed_feed_seasons, migrations.RunPython.noop),
    ]
