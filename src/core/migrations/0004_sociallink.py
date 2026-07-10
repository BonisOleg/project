from django.db import migrations, models


def seed_social_links(apps, schema_editor):
    SocialLink = apps.get_model('core', 'SocialLink')
    SiteSettings = apps.get_model('core', 'SiteSettings')
    settings = SiteSettings.objects.filter(pk=1).first()

    defaults = [
        ('telegram', '', 10),
        ('facebook', getattr(settings, 'facebook_url', '') if settings else '', 20),
        ('instagram', getattr(settings, 'instagram_url', '') if settings else '', 30),
    ]
    if settings and settings.youtube_url:
        defaults.append(('youtube', settings.youtube_url, 40))

    for network, url, order in defaults:
        SocialLink.objects.get_or_create(
            network=network,
            defaults={
                'url': url or '',
                'sort_order': order,
                'is_active': True,
            },
        )


def unseed_social_links(apps, schema_editor):
    SocialLink = apps.get_model('core', 'SocialLink')
    SocialLink.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_site_header_settings'),
    ]

    operations = [
        migrations.CreateModel(
            name='SocialLink',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('network', models.CharField(
                    choices=[
                        ('telegram', 'Telegram'),
                        ('facebook', 'Facebook'),
                        ('instagram', 'Instagram'),
                        ('tiktok', 'TikTok'),
                        ('viber', 'Viber'),
                        ('whatsapp', 'WhatsApp'),
                        ('youtube', 'YouTube'),
                    ],
                    max_length=20,
                    verbose_name='Мережа',
                )),
                ('url', models.URLField(blank=True, verbose_name='Посилання')),
                ('sort_order', models.PositiveSmallIntegerField(default=0, verbose_name='Порядок')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активне')),
            ],
            options={
                'verbose_name': 'Соцмережа',
                'verbose_name_plural': 'Соцмережі',
                'ordering': ['sort_order', 'id'],
            },
        ),
        migrations.RunPython(seed_social_links, unseed_social_links),
    ]
