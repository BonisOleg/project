from django.db import migrations, models


def forwards_migrate_hero_image(apps, schema_editor):
    SiteBlock = apps.get_model('core', 'SiteBlock')
    HeroSlide = apps.get_model('core', 'HeroSlide')

    if HeroSlide.objects.exists():
        SiteBlock.objects.filter(page='home', key__in=('hero_image', 'hero_image_alt')).delete()
        return

    image_block = SiteBlock.objects.filter(page='home', key='hero_image').first()
    alt_block = SiteBlock.objects.filter(page='home', key='hero_image_alt').first()
    alt_text = (alt_block.text_html or '').strip() if alt_block else ''

    if image_block and image_block.image:
        HeroSlide.objects.create(
            image=image_block.image,
            alt_text=alt_text,
            sort_order=0,
            is_active=True,
        )

    SiteBlock.objects.filter(page='home', key__in=('hero_image', 'hero_image_alt')).delete()


def backwards_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_sitefootersettings'),
    ]

    operations = [
        migrations.CreateModel(
            name='HeroSlide',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='hero/', verbose_name='Фото')),
                ('alt_text', models.CharField(blank=True, max_length=200, verbose_name='Alt-текст')),
                ('sort_order', models.PositiveIntegerField(default=0, verbose_name='Порядок')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активний')),
            ],
            options={
                'verbose_name': 'Слайд hero',
                'verbose_name_plural': 'Слайди hero',
                'ordering': ['sort_order', 'id'],
            },
        ),
        migrations.RunPython(forwards_migrate_hero_image, backwards_noop),
    ]
