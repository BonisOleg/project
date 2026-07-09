from django.db import migrations, models


def seed_site_blocks(apps, schema_editor):
    SiteBlock = apps.get_model('core', 'SiteBlock')

    from src.core.block_defaults import BLOCK_CONTENT_TYPES, BLOCK_DEFAULTS
    from src.core.site_content_registry import all_registry_block_keys, get_block_field_label

    for page, key in all_registry_block_keys():
        content_type = BLOCK_CONTENT_TYPES.get((page, key), 'text')
        text_default = BLOCK_DEFAULTS.get((page, key), '1' if key.endswith('_section_visible') else '')

        SiteBlock.objects.get_or_create(
            page=page,
            key=key,
            defaults={
                'label': get_block_field_label(page, key),
                'content_type': content_type,
                'text_html': text_default,
                'sort_order': 0,
                'is_active': True,
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SiteBlock',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('page', models.CharField(choices=[('home', 'Головна'), ('site', 'Сайт')], max_length=32, verbose_name='Сторінка')),
                ('key', models.CharField(max_length=64, verbose_name='Ключ блоку')),
                ('label', models.CharField(max_length=128, verbose_name='Назва в адмінці')),
                ('content_type', models.CharField(choices=[('text', 'Текст'), ('image', 'Фото')], default='text', max_length=16, verbose_name='Тип контенту')),
                ('text_html', models.TextField(blank=True, verbose_name='Текст')),
                ('image', models.ImageField(blank=True, upload_to='blocks/', verbose_name='Зображення')),
                ('sort_order', models.PositiveSmallIntegerField(default=0, verbose_name='Порядок')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активний')),
            ],
            options={
                'verbose_name': 'Блок контенту',
                'verbose_name_plural': 'Блоки контенту',
                'ordering': ['page', 'sort_order', 'key'],
                'constraints': [models.UniqueConstraint(fields=('page', 'key'), name='unique_site_block_page_key')],
            },
        ),
        migrations.RunPython(seed_site_blocks, migrations.RunPython.noop),
        migrations.CreateModel(
            name='HomeAboutSettings',
            fields=[],
            options={
                'verbose_name': 'Головна — Про нас',
                'verbose_name_plural': 'Головна — Про нас',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('core.sitesettings',),
        ),
        migrations.CreateModel(
            name='HomeBenefitsSettings',
            fields=[],
            options={
                'verbose_name': 'Головна — Переваги',
                'verbose_name_plural': 'Головна — Переваги',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('core.sitesettings',),
        ),
        migrations.CreateModel(
            name='HomeBlogSettings',
            fields=[],
            options={
                'verbose_name': 'Головна — Блог',
                'verbose_name_plural': 'Головна — Блог',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('core.sitesettings',),
        ),
        migrations.CreateModel(
            name='HomeCategoriesSettings',
            fields=[],
            options={
                'verbose_name': 'Головна — Категорії',
                'verbose_name_plural': 'Головна — Категорії',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('core.sitesettings',),
        ),
        migrations.CreateModel(
            name='HomeHeroSettings',
            fields=[],
            options={
                'verbose_name': 'Головна — Hero',
                'verbose_name_plural': 'Головна — Hero',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('core.sitesettings',),
        ),
        migrations.CreateModel(
            name='HomeProductsSettings',
            fields=[],
            options={
                'verbose_name': 'Головна — Товари',
                'verbose_name_plural': 'Головна — Товари',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('core.sitesettings',),
        ),
    ]
