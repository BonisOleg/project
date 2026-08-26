# Generated manually for legal address

from django.db import migrations, models

DEFAULT_LEGAL_ADDRESS = 'Львів, вул. Генерала Юнаківа, 9'


def seed_legal_address(apps, schema_editor):
    SiteSettings = apps.get_model('core', 'SiteSettings')
    obj, _created = SiteSettings.objects.get_or_create(pk=1)
    if not (obj.legal_address or '').strip():
        obj.legal_address = DEFAULT_LEGAL_ADDRESS
        obj.save(update_fields=['legal_address'])


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_sitephone'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesettings',
            name='legal_address',
            field=models.CharField(
                blank=True,
                default=DEFAULT_LEGAL_ADDRESS,
                max_length=255,
                verbose_name='Юридична адреса',
            ),
        ),
        migrations.RunPython(seed_legal_address, migrations.RunPython.noop),
    ]
