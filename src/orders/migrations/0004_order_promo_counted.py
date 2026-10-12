from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0003_checkout_courier_and_account_label'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='promo_counted',
            field=models.BooleanField(
                default=False,
                verbose_name='Промокод зараховано в used_count',
            ),
        ),
    ]
