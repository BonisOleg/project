from django.db import migrations


HEADER_KEYS = (
    'header_nav_home_label',
    'header_nav_home_visible',
    'header_nav_news_label',
    'header_nav_news_visible',
)


def seed_home_blog_nav(apps, schema_editor):
    SiteBlock = apps.get_model('core', 'SiteBlock')

    from src.core.block_defaults import BLOCK_CONTENT_TYPES, BLOCK_DEFAULTS
    from src.core.site_content_registry import get_block_field_label

    for key in HEADER_KEYS:
        page = 'site'
        default = BLOCK_DEFAULTS.get((page, key), '1' if key.endswith('_visible') else '')
        content_type = BLOCK_CONTENT_TYPES.get((page, key), 'text')
        block, created = SiteBlock.objects.get_or_create(
            page=page,
            key=key,
            defaults={
                'label': get_block_field_label(page, key),
                'content_type': content_type,
                'text_html': default,
                'sort_order': 0,
                'is_active': True,
            },
        )
        if created:
            continue
        # Увімкнути Блог і оновити підписи зі старих «Новини»
        changed_fields: list[str] = []
        new_label = get_block_field_label(page, key)
        if block.label != new_label:
            block.label = new_label
            changed_fields.append('label')
        if key == 'header_nav_news_visible' and block.text_html.strip() in {'0', 'false', 'False', ''}:
            block.text_html = '1'
            changed_fields.append('text_html')
        elif key == 'header_nav_news_label' and block.text_html.strip() in {'Новини', 'новини', ''}:
            block.text_html = 'Блог'
            changed_fields.append('text_html')
        elif key.startswith('header_nav_home_') and not block.text_html.strip():
            block.text_html = default
            changed_fields.append('text_html')
        if changed_fields:
            block.save(update_fields=changed_fields)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_oyra_tz_features'),
    ]

    operations = [
        migrations.RunPython(seed_home_blog_nav, migrations.RunPython.noop),
    ]
