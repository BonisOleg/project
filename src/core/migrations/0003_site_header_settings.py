from django.db import migrations


def seed_header_blocks(apps, schema_editor):
    SiteBlock = apps.get_model('core', 'SiteBlock')

    from src.core.block_defaults import BLOCK_CONTENT_TYPES, BLOCK_DEFAULTS
    from src.core.site_content_registry import get_section, iter_section_blocks, get_block_field_label

    section = get_section('site', 'header')
    for page, key in iter_section_blocks(section):
        content_type = BLOCK_CONTENT_TYPES.get((page, key), 'text')
        default = BLOCK_DEFAULTS.get((page, key), '1' if key.endswith('_visible') else '')

        SiteBlock.objects.get_or_create(
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


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_siteblock_cms'),
    ]

    operations = [
        migrations.RunPython(seed_header_blocks, migrations.RunPython.noop),
        migrations.CreateModel(
            name='SiteHeaderSettings',
            fields=[],
            options={
                'verbose_name': 'Шапка — Меню',
                'verbose_name_plural': 'Шапка — Меню',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('core.sitesettings',),
        ),
    ]
