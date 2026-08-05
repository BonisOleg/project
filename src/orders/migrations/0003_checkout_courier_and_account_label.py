from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0002_oyra_tz_features'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='create_account',
            field=models.BooleanField(
                default=False,
                verbose_name='Створити акаунт для швидших покупок',
            ),
        ),
        migrations.AlterField(
            model_name='order',
            name='delivery_service',
            field=models.CharField(
                choices=[
                    ('nova_poshta', 'Нова Пошта'),
                    ('courier_delivery', 'Курʼєрська доставка'),
                    ('ukrposhta', 'Укрпошта'),
                ],
                max_length=20,
                verbose_name='Доставка',
            ),
        ),
    ]
