from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from src.accounts.models import User
from src.blog.models import Post
from src.catalog.models import Brand, Category, Product, ProductAttribute
from src.core.models import SiteSettings
from src.pages.models import FAQItem, StaticPage
from src.promotions.models import PromoCode
from src.reviews.models import Review


CATEGORIES = [
    ('dim-i-sad', 'Дім і сад', [
        ('skladni-mebli', 'Складні меблі'),
        ('sadovi-goydalky', 'Садові гойдалки'),
        ('paviljony', 'Садові павільйони, альтанки'),
        ('vulychni-mebli', 'Вуличні меблі'),
    ]),
    ('valizy', 'Дорожні валізи', [
        ('komplekty', 'Комплекти валіз'),
        ('tkanynni', 'Тканинні валізи'),
        ('plastikovi', 'Пластикові валізи'),
    ]),
    ('krisla', 'Крісла', [
        ('ofisni', 'Офісні крісла'),
        ('barni', 'Барні стільці'),
        ('gejmerski', 'Геймерські крісла'),
        ('kuxonni', 'Стільці для кухні'),
    ]),
    ('budivnytstvo', 'Будівництво і ремонт', [
        ('stellazhi', 'Металеві стелажі'),
        ('vizky', 'Складські візки'),
        ('plitka', 'Плитка керамогранітна'),
        ('vantazhne', 'Вантажне обладнання'),
    ]),
    ('dytiachi', 'Дитячі товари', [
        ('elektromobili', 'Дитячі електромобілі'),
        ('igrovi', 'Ігрові комплекси та гойдалки'),
        ('kvadro', 'Дитячі електроквадроцикли'),
        ('motocikly', 'Дитячі електромотоцикли'),
    ]),
    ('sport', 'Спорт і відпочинок', [
        ('batuty', 'Батути'),
        ('dorizhky', 'Бігові доріжки'),
        ('sup', 'Sup-дошки'),
        ('trenazhery', 'Велотренажери та орбітреки'),
    ]),
    ('traktory', 'Трактори', [('kolisni', 'Трактори колісні')]),
    ('zootovary', 'Зоотовари', [('igrashky', 'Іграшки для тварин')]),
    ('utsineni', 'Уцінений товар', []),
    ('sto', 'Обладнання СТО', [
        ('vantazhopidjomne', 'Вантажопідйомне обладнання'),
        ('presy', 'Преси'),
        ('roztjazhky', 'Розтяжки гідравлічні'),
        ('stendy', 'Стенди для ремонту двигуна'),
    ]),
]

STATIC_PAGES = [
    ('delivery', 'Доставка', 'Доставка Новою Поштою та Укрпоштою протягом 1–3 днів.'),
    ('payment', 'Оплата', 'Оплата через LiqPay: Visa, Mastercard, Apple Pay, Google Pay.'),
    ('returns', 'Повернення та обмін', 'Повернення товару протягом 14 днів.'),
    ('about', 'Про нас', 'Oyra — сучасний інтернет-магазин корисних товарів.'),
    ('security', 'Політика безпеки', 'Ми захищаємо ваші дані та платежі.'),
    ('offer', 'Публічний договір', 'Умови купівлі-продажу через сайт Oyra.'),
    ('dropshipping', 'Дропшипінг', 'Співпраця для партнерів без власного складу.'),
    ('schedule', 'Графік роботи', 'Пн–Пт: 9:00–18:00. Сб–Нд: вихідний.'),
    ('instructions', 'Інструкції товарів', 'Архів інструкцій з експлуатації.'),
    ('privacy', 'Політика конфіденційності', 'Як ми обробляємо персональні дані.'),
    ('terms', 'Умови використання', 'Правила користування сайтом.'),
    ('cookies', 'Політика cookies', 'Як сайт використовує cookies.'),
    ('faq', 'FAQ', 'Часті питання.'),
]

SAMPLE_PRODUCTS = [
    ('Стелаж металевий 180×90×40', 'G9040', 'stellazhi', 'GoodTool', Decimal('1082.00'), True, False, False),
    ('Стелаж металевий 180×90×40 чорний', 'P9040', 'stellazhi', 'GoodTool', Decimal('1234.00'), True, False, False),
    ('Крісло Bonro B-619 чорне', 'B619', 'ofisni', 'Bonro', Decimal('894.00'), True, False, False),
    ('Крісло для кухні Bonro B-173 біле', 'B173', 'kuxonni', 'Bonro', Decimal('737.00'), True, False, False),
    ('Батут дитячий 374 см Atleto', 'BAT374', 'batuty', 'Atleto', Decimal('7954.00'), True, False, True),
    ('Шезлонг Bonro B2002-4 сірий', 'SP2002', 'vulychni-mebli', 'Bonro', Decimal('1996.00'), False, True, False),
    ('Крісло обіднє Bonro B-016 комплект 4 шт', 'B016', 'kuxonni', 'Bonro', Decimal('3456.00'), False, True, False),
    ('Валіза пластикова 28"', 'VAL28', 'plastikovi', 'Oyra', Decimal('1890.00'), False, True, True),
]


class Command(BaseCommand):
    help = 'Seed demo data for Oyra MVP'

    def handle(self, *args, **options):
        SiteSettings.get_solo()
        self.stdout.write('Site settings OK')

        sort = 0
        cat_map = {}
        for slug, name, children in CATEGORIES:
            sort += 1
            parent, _ = Category.objects.update_or_create(
                slug=slug,
                defaults={'name': name, 'sort_order': sort, 'is_active': True},
            )
            cat_map[slug] = parent
            for i, (cslug, cname) in enumerate(children, 1):
                child, _ = Category.objects.update_or_create(
                    slug=cslug,
                    defaults={
                        'name': cname, 'parent': parent,
                        'sort_order': i, 'is_active': True,
                    },
                )
                cat_map[cslug] = child

        brands = {}
        for bname in ('Bonro', 'GoodTool', 'Atleto', 'Oyra'):
            slug = bname.lower()
            brands[bname], _ = Brand.objects.update_or_create(
                slug=slug, defaults={'name': bname},
            )

        for title, sku, cat_slug, brand, price, top, new, sale in SAMPLE_PRODUCTS:
            cat = cat_map.get(cat_slug) or list(cat_map.values())[0]
            old_price = price * Decimal('1.15') if sale else None
            product, created = Product.objects.update_or_create(
                sku=sku,
                defaults={
                    'name': title,
                    'slug': sku.lower(),
                    'category': cat,
                    'brand': brands.get(brand),
                    'price': price,
                    'old_price': old_price,
                    'is_top_sale': top,
                    'is_new': new,
                    'is_on_sale': sale,
                    'is_active': True,
                    'short_description': f'{title} — якість та надійність від Oyra.',
                    'description': f'Детальний опис товару {title}. Ідеально підходить для щоденного використання.',
                },
            )
            if created:
                ProductAttribute.objects.get_or_create(
                    product=product, name='Матеріал', defaults={'value': 'Метал / текстиль'},
                )
                Review.objects.get_or_create(
                    product=product,
                    author_name='Олена К.',
                    defaults={'rating': 5, 'text': 'Чудова якість, швидка доставка!', 'is_published': True},
                )

        for slug, title, content in STATIC_PAGES:
            StaticPage.objects.update_or_create(
                slug=slug, defaults={'title': title, 'content': content, 'is_published': True},
            )

        FAQItem.objects.get_or_create(
            question='Чи потрібна реєстрація для покупки?',
            defaults={
                'answer': 'Ні, можна оформити замовлення як гість.',
                'sort_order': 1, 'is_published': True,
            },
        )
        FAQItem.objects.get_or_create(
            question='Як оплатити через LiqPay?',
            defaults={
                'answer': 'На останньому кроці checkout натисніть «Оплатити через LiqPay».',
                'sort_order': 2, 'is_published': True,
            },
        )

        PromoCode.objects.update_or_create(
            code='OYRA15',
            defaults={
                'discount_type': PromoCode.TYPE_PERCENT,
                'discount_value': Decimal('15'),
                'is_active': True,
            },
        )

        Post.objects.update_or_create(
            slug='ofisne-krislo-bonro',
            defaults={
                'title': 'Огляд офісного крісла Bonro B-619',
                'excerpt': 'Комфорт для роботи та навчання.',
                'content': 'Детальний огляд популярного офісного крісла.',
                'is_published': True,
                'published_at': timezone.now(),
            },
        )

        if not User.objects.filter(email='admin@oyra.ua').exists():
            User.objects.create_superuser(
                email='admin@oyra.ua',
                password='admin12345',
                first_name='Admin',
            )
            self.stdout.write(self.style.WARNING('Admin: admin@oyra.ua / admin12345'))

        self.stdout.write(self.style.SUCCESS('Seed completed'))
