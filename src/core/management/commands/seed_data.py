from datetime import timedelta
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import timezone

from src.accounts.models import User
from src.blog.models import Post
from src.catalog.models import Brand, CatalogFilter, Category, Product, ProductAttribute
from src.catalog.category_icons import SLUG_TO_ICON_KEY
from src.catalog.filter_schema import BONRO_ATTR_FACETS, BONRO_ATTR_FALLBACKS
from src.core.models import SiteSettings, SocialLink
from src.pages.models import FAQItem, StaticPage
from src.pages.static_content import FAQ_ITEMS, STATIC_PAGES
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

# slug, title, excerpt, content, hero filename, days_ago
BLOG_POSTS = (
    (
        'ofisne-krislo-bonro',
        'Огляд офісного крісла Bonro B-619',
        'Комфорт для роботи та навчання.',
        'Детальний огляд популярного офісного крісла Bonro B-619: ергономіка, матеріали та для кого воно підходить.',
        'chair.jpg',
        1,
    ),
    (
        'yak-obraty-ofisne-krislo',
        'Як обрати офісне крісло для довгої роботи',
        'На що звернути увагу перед покупкою.',
        'Пояснюємо, як підібрати висоту сидіння, підтримку попереку та матеріал оббивки, щоб працювати комфортно щодня.',
        'lounger.jpg',
        4,
    ),
    (
        'organizaciya-robochogo-miscya',
        'Організація робочого місця: стелаж і порядок',
        'Практичні поради для дому та офісу.',
        'Як розставити стелаж, звільнити стіл від зайвого і зробити робочу зону зручнішою без великих витрат.',
        'shelf.jpg',
        8,
    ),
)


class Command(BaseCommand):
    help = 'Seed demo data for Oyra MVP'

    def handle(self, *args, **options):
        SiteSettings.get_solo()
        self.stdout.write('Site settings OK')

        defaults = (
            (SocialLink.Network.TELEGRAM, 10),
            (SocialLink.Network.FACEBOOK, 20),
            (SocialLink.Network.INSTAGRAM, 30),
        )
        for network, order in defaults:
            SocialLink.objects.get_or_create(
                network=network,
                defaults={'sort_order': order, 'is_active': True, 'url': ''},
            )
        self.stdout.write('Social links OK')

        sort = 0
        cat_map = {}
        cat_colors = {
            'dim-i-sad': '#2BBD7E', 'valizy': '#2453E0', 'krisla': '#FF6A3D',
            'budivnytstvo': '#2453E0', 'dytiachi': '#FFC93C', 'sport': '#FF6A3D',
            'traktory': '#2BBD7E', 'zootovary': '#C99200', 'utsineni': '#FF3B5C', 'sto': '#2453E0',
        }
        for slug, name, children in CATEGORIES:
            sort += 1
            parent, _ = Category.objects.update_or_create(
                slug=slug,
                defaults={
                    'name': name,
                    'sort_order': sort,
                    'is_active': True,
                    'icon_key': SLUG_TO_ICON_KEY.get(slug, 'grid'),
                    'color': cat_colors.get(slug, '#2453E0'),
                },
            )
            cat_map[slug] = parent
            for i, (cslug, cname) in enumerate(children, 1):
                child, _ = Category.objects.update_or_create(
                    slug=cslug,
                    defaults={
                        'name': cname, 'parent': parent,
                        'sort_order': i, 'is_active': True,
                        'icon_key': SLUG_TO_ICON_KEY.get(slug, 'grid'),
                        'color': cat_colors.get(slug, '#2453E0'),
                    },
                )
                cat_map[cslug] = child

        if not CatalogFilter.objects.exists():
            defaults = [
                ('Бренд', CatalogFilter.TYPE_BRAND, '', '', 10, False),
                ('Ціна, грн', CatalogFilter.TYPE_PRICE, '', '', 20, True),
                ('Вид', CatalogFilter.TYPE_CATEGORY, '', '', 30, False),
            ]
            order = 40
            for aname in BONRO_ATTR_FACETS:
                defaults.append((
                    aname, CatalogFilter.TYPE_ATTRIBUTE, aname,
                    '\n'.join(BONRO_ATTR_FALLBACKS.get(aname, [])), order, False,
                ))
                order += 10
            defaults.append(('Наявність', CatalogFilter.TYPE_IN_STOCK, '', '', 200, False))
            for name, ftype, attr, fallback, sord, opened in defaults:
                CatalogFilter.objects.create(
                    name=name, filter_type=ftype, attribute_name=attr,
                    fallback_values=fallback, sort_order=sord,
                    is_active=True, open_by_default=opened,
                )

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
                attrs = {
                    'Матеріал': 'Метал / текстиль',
                    'Форма': 'Класична',
                    'Колір': 'Чорний' if 'чорн' in title.lower() else (
                        'Білий' if 'біл' in title.lower() else (
                            'Сірий' if 'сір' in title.lower() else 'Бежевий'
                        )
                    ),
                    'Країна-виробник товару': 'Україна',
                    'Країна реєстрації бренду': 'Україна',
                }
                if cat_slug == 'batuty':
                    attrs.update({
                        'Форма': 'Кругла',
                        'Діаметр, см': '374',
                        'Максимальне навантаження': '150 кг',
                    })
                for aname, avalue in attrs.items():
                    ProductAttribute.objects.get_or_create(
                        product=product, name=aname, defaults={'value': avalue},
                    )
                Review.objects.get_or_create(
                    product=product,
                    author_name='Олена К.',
                    defaults={'rating': 5, 'text': 'Чудова якість, швидка доставка!', 'is_published': True},
                )
            else:
                # Оновити атрибути для вже існуючих демо-товарів (Bonro-фільтри)
                defaults_attrs = {
                    'Форма': 'Класична',
                    'Колір': 'Чорний' if 'чорн' in title.lower() else (
                        'Білий' if 'біл' in title.lower() else (
                            'Сірий' if 'сір' in title.lower() else 'Бежевий'
                        )
                    ),
                    'Країна-виробник товару': 'Україна',
                    'Країна реєстрації бренду': 'Україна',
                    'Матеріал': 'Метал / текстиль',
                }
                if cat_slug == 'batuty':
                    defaults_attrs.update({
                        'Форма': 'Кругла',
                        'Діаметр, см': '374',
                        'Максимальне навантаження': '150 кг',
                    })
                for aname, avalue in defaults_attrs.items():
                    ProductAttribute.objects.get_or_create(
                        product=product, name=aname, defaults={'value': avalue},
                    )

        for slug, title, content in STATIC_PAGES:
            StaticPage.objects.update_or_create(
                slug=slug, defaults={'title': title, 'content': content, 'is_published': True},
            )

        for question, answer, order in FAQ_ITEMS:
            FAQItem.objects.update_or_create(
                question=question,
                defaults={
                    'answer': answer,
                    'sort_order': order,
                    'is_published': True,
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

        now = timezone.now()
        hero_dir = Path(settings.BASE_DIR) / 'static' / 'images' / 'hero'
        for slug, title, excerpt, content, image_name, days_ago in BLOG_POSTS:
            post, _ = Post.objects.update_or_create(
                slug=slug,
                defaults={
                    'title': title,
                    'excerpt': excerpt,
                    'content': content,
                    'is_published': True,
                    'published_at': now - timedelta(days=days_ago),
                },
            )
            source = hero_dir / image_name
            if not source.exists():
                self.stderr.write(self.style.ERROR(f'Missing blog image: {source}'))
                continue
            if post.image:
                post.image.delete(save=False)
            post.image.save(
                f'{slug}-{image_name}',
                ContentFile(source.read_bytes()),
                save=True,
            )
            self.stdout.write(self.style.SUCCESS(f'Blog post: {title} ← {image_name}'))

        if not User.objects.filter(email='admin@oyra.ua').exists():
            User.objects.create_superuser(
                email='admin@oyra.ua',
                password='admin12345',
                first_name='Admin',
            )
            self.stdout.write(self.style.WARNING('Admin: admin@oyra.ua / admin12345'))

        call_command('seed_hero_product_images')
        self.stdout.write(self.style.SUCCESS('Seed completed'))
