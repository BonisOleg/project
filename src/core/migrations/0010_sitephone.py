# Generated manually for multi-phone admin

import re

from django.db import migrations, models


def _split_phones(raw: str) -> list[str]:
    parts = re.split(r'[,;\n]+', raw or '')
    return [item.strip() for item in parts if item.strip()]


def migrate_site_phones(apps, schema_editor):
    SiteSettings = apps.get_model('core', 'SiteSettings')
    SitePhone = apps.get_model('core', 'SitePhone')
    for settings in SiteSettings.objects.all():
        numbers = _split_phones(getattr(settings, 'phone', '') or '')
        for index, number in enumerate(numbers):
            SitePhone.objects.create(
                settings=settings,
                phone=number,
                sort_order=index,
                is_active=True,
            )


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_offer_requisites_settings'),
    ]

    operations = [
        migrations.CreateModel(
            name='SitePhone',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phone', models.CharField(max_length=30, verbose_name='Телефон')),
                ('sort_order', models.PositiveSmallIntegerField(default=0, verbose_name='Порядок')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активний')),
                (
                    'settings',
                    models.ForeignKey(
                        on_delete=models.CASCADE,
                        related_name='phones',
                        to='core.sitesettings',
                        verbose_name='Налаштування сайту',
                    ),
                ),
            ],
            options={
                'verbose_name': 'Телефон',
                'verbose_name_plural': 'Телефони',
                'ordering': ['sort_order', 'id'],
            },
        ),
        migrations.RunPython(migrate_site_phones, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='sitesettings',
            name='phone',
        ),
    ]
