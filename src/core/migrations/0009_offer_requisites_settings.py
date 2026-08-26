# Generated manually for offer requisites CMS

from django.db import migrations


DEFAULT_RECIPIENT = 'ФОП Яремко Марія Михайлівна'
DEFAULT_IBAN = 'UA82 305299 00000 26002011023486'
DEFAULT_BANK = 'АТ КБ "ПРИВАТБАНК"'


def seed_offer_requisites(apps, schema_editor):
    SiteSettings = apps.get_model('core', 'SiteSettings')
    obj, _created = SiteSettings.objects.get_or_create(pk=1)
    updated = False
    if not (obj.bank_recipient or '').strip():
        obj.bank_recipient = DEFAULT_RECIPIENT
        updated = True
    if not (obj.bank_iban or '').strip():
        obj.bank_iban = DEFAULT_IBAN
        updated = True
    if not (obj.bank_name or '').strip():
        obj.bank_name = DEFAULT_BANK
        updated = True
    if updated:
        obj.save(update_fields=['bank_recipient', 'bank_iban', 'bank_name'])


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_header_home_blog_nav'),
    ]

    operations = [
        migrations.CreateModel(
            name='OfferRequisitesSettings',
            fields=[],
            options={
                'verbose_name': 'Оферта — Реквізити',
                'verbose_name_plural': 'Оферта — Реквізити',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('core.sitesettings',),
        ),
        migrations.RunPython(seed_offer_requisites, migrations.RunPython.noop),
    ]
