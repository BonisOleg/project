from django.db import migrations, models

DEFAULT_GTM_ID = 'GTM-ML3T82P6'
DEFAULT_VERIFICATION = 'PwqksGkk03OfHYb8_lnn2SKIGcS6boJgRCNgA2DRz0A'


def seed_gtm_defaults(apps, schema_editor):
    SiteSettings = apps.get_model('core', 'SiteSettings')
    obj, _created = SiteSettings.objects.get_or_create(pk=1)
    update_fields = []
    if not (obj.gtm_container_id or '').strip():
        obj.gtm_container_id = DEFAULT_GTM_ID
        update_fields.append('gtm_container_id')
    if not (obj.google_site_verification or '').strip():
        obj.google_site_verification = DEFAULT_VERIFICATION
        update_fields.append('google_site_verification')
    if not obj.gtm_enabled:
        obj.gtm_enabled = True
        update_fields.append('gtm_enabled')
    if update_fields:
        obj.save(update_fields=update_fields)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_sitesettings_legal_address'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesettings',
            name='gtm_enabled',
            field=models.BooleanField(default=True, verbose_name='GTM увімкнено'),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='gtm_container_id',
            field=models.CharField(
                blank=True,
                default=DEFAULT_GTM_ID,
                help_text='Формат: GTM-XXXXXXX',
                max_length=32,
                verbose_name='GTM Container ID',
            ),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='google_site_verification',
            field=models.CharField(
                blank=True,
                default=DEFAULT_VERIFICATION,
                help_text='Значення content з meta google-site-verification',
                max_length=128,
                verbose_name='Google site verification',
            ),
        ),
        migrations.CreateModel(
            name='GoogleTagManagerSettings',
            fields=[],
            options={
                'verbose_name': 'Google Tag Manager',
                'verbose_name_plural': 'Google Tag Manager',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('core.sitesettings',),
        ),
        migrations.RunPython(seed_gtm_defaults, migrations.RunPython.noop),
    ]
