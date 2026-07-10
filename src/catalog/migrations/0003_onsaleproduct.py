from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0002_proxy_tab_models'),
    ]

    operations = [
        migrations.CreateModel(
            name='OnSaleProduct',
            fields=[
            ],
            options={
                'verbose_name': 'Товар на акції',
                'verbose_name_plural': 'Товари на акції',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('catalog.product',),
        ),
    ]
