from django.db import models


class SiteSettings(models.Model):
    site_name = models.CharField('Назва сайту', max_length=100, default='Oyra')
    email = models.EmailField('Email', default='info@oyra.ua')
    address = models.CharField('Адреса', max_length=255, default='м. Львів, Україна')
    legal_address = models.CharField(
        'Юридична адреса',
        max_length=255,
        default='Львів, вул. Генерала Юнаківа, 9',
        blank=True,
    )
    work_hours = models.CharField('Години роботи', max_length=255, default='Пн–Пт: 9:00–18:00')
    facebook_url = models.URLField('Facebook', blank=True)
    youtube_url = models.URLField('YouTube', blank=True)
    instagram_url = models.URLField('Instagram', blank=True)
    newsletter_discount = models.PositiveSmallIntegerField('Знижка за підписку %', default=15)
    free_delivery_from = models.DecimalField(
        'Безкоштовна доставка від', max_digits=10, decimal_places=2, null=True, blank=True
    )
    meta_description = models.TextField('Meta description головної', blank=True)

    # Сповіщення про нові замовлення (дублікати на глобальні контакти)
    notify_emails = models.TextField(
        'Email для сповіщень про замовлення',
        blank=True,
        help_text='Одна або кілька адрес через кому чи з нового рядка.',
    )
    notify_phones = models.TextField(
        'Телефони для Viber/SMS (TurboSMS)',
        blank=True,
        help_text='Номери для дублюючих сповіщень. Через кому або з нового рядка.',
    )

    # Реквізити для безготівкового розрахунку
    bank_recipient = models.CharField('Отримувач (ФОП/ТОВ)', max_length=255, blank=True)
    bank_iban = models.CharField('IBAN', max_length=34, blank=True)
    bank_edrpou = models.CharField('ЄДРПОУ / ІПН', max_length=20, blank=True)
    bank_name = models.CharField('Банк', max_length=255, blank=True)
    bank_details_note = models.TextField(
        'Додаткова інструкція до оплати',
        blank=True,
        help_text='Текст, який побачить клієнт при виборі безготівкового розрахунку.',
    )

    class Meta:
        verbose_name = 'Налаштування сайту'
        verbose_name_plural = 'Налаштування сайту'

    def __str__(self):
        return self.site_name

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    @classmethod
    def load(cls):
        return cls.get_solo()

    @property
    def phone(self) -> str:
        first = (
            self.phones.filter(is_active=True)
            .order_by('sort_order', 'id')
            .values_list('phone', flat=True)
            .first()
        )
        return first or ''

    def active_phones(self) -> list[str]:
        return list(
            self.phones.filter(is_active=True)
            .order_by('sort_order', 'id')
            .values_list('phone', flat=True)
        )


class SitePhone(models.Model):
    settings = models.ForeignKey(
        SiteSettings,
        on_delete=models.CASCADE,
        related_name='phones',
        verbose_name='Налаштування сайту',
    )
    phone = models.CharField('Телефон', max_length=30)
    sort_order = models.PositiveSmallIntegerField('Порядок', default=0)
    is_active = models.BooleanField('Активний', default=True)

    class Meta:
        ordering = ['sort_order', 'id']
        verbose_name = 'Телефон'
        verbose_name_plural = 'Телефони'

    def __str__(self) -> str:
        return self.phone


class SiteBlock(models.Model):
    class ContentType(models.TextChoices):
        TEXT = 'text', 'Текст'
        IMAGE = 'image', 'Фото'

    class Page(models.TextChoices):
        HOME = 'home', 'Головна'
        SITE = 'site', 'Сайт'

    page = models.CharField(max_length=32, choices=Page.choices, verbose_name='Сторінка')
    key = models.CharField(max_length=64, verbose_name='Ключ блоку')
    label = models.CharField(max_length=128, verbose_name='Назва в адмінці')
    content_type = models.CharField(
        max_length=16,
        choices=ContentType.choices,
        default=ContentType.TEXT,
        verbose_name='Тип контенту',
    )
    text_html = models.TextField(blank=True, verbose_name='Текст')
    image = models.ImageField(upload_to='blocks/', blank=True, verbose_name='Зображення')
    sort_order = models.PositiveSmallIntegerField(default=0, verbose_name='Порядок')
    is_active = models.BooleanField(default=True, verbose_name='Активний')

    class Meta:
        ordering = ['page', 'sort_order', 'key']
        verbose_name = 'Блок контенту'
        verbose_name_plural = 'Блоки контенту'
        constraints = [
            models.UniqueConstraint(fields=['page', 'key'], name='unique_site_block_page_key'),
        ]

    def __str__(self) -> str:
        return f'{self.get_page_display()} · {self.label}'

    @property
    def cache_key(self) -> str:
        return f'{self.page}.{self.key}'


class HeroSlide(models.Model):
    image = models.ImageField('Фото', upload_to='hero/')
    alt_text = models.CharField('Alt-текст', max_length=200, blank=True)
    sort_order = models.PositiveIntegerField('Порядок', default=0)
    is_active = models.BooleanField('Активний', default=True)

    class Meta:
        ordering = ['sort_order', 'id']
        verbose_name = 'Слайд hero'
        verbose_name_plural = 'Слайди hero'

    def __str__(self) -> str:
        if self.alt_text:
            return self.alt_text
        if self.image:
            return self.image.name
        return f'Слайд #{self.pk or "новий"}'


class HomeHeroSettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = 'Головна — Hero'
        verbose_name_plural = 'Головна — Hero'


class HomeProductsSettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = 'Головна — Товари'
        verbose_name_plural = 'Головна — Товари'


class HomeCategoriesSettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = 'Головна — Категорії'
        verbose_name_plural = 'Головна — Категорії'


class HomeBenefitsSettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = 'Головна — Переваги'
        verbose_name_plural = 'Головна — Переваги'


class HomeAboutSettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = 'Головна — Про нас'
        verbose_name_plural = 'Головна — Про нас'


class HomeBlogSettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = 'Головна — Блог'
        verbose_name_plural = 'Головна — Блог'


class SiteHeaderSettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = 'Меню навігації'
        verbose_name_plural = 'Меню навігації'


class SiteFooterSettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = 'Нижній блок сайту'
        verbose_name_plural = 'Нижній блок сайту'


class OfferRequisitesSettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = 'Оферта — Реквізити'
        verbose_name_plural = 'Оферта — Реквізити'


class SocialLink(models.Model):
    class Network(models.TextChoices):
        TELEGRAM = 'telegram', 'Telegram'
        FACEBOOK = 'facebook', 'Facebook'
        INSTAGRAM = 'instagram', 'Instagram'
        TIKTOK = 'tiktok', 'TikTok'
        VIBER = 'viber', 'Viber'
        WHATSAPP = 'whatsapp', 'WhatsApp'
        YOUTUBE = 'youtube', 'YouTube'

    network = models.CharField(
        'Мережа',
        max_length=20,
        choices=Network.choices,
    )
    url = models.URLField('Посилання', blank=True)
    sort_order = models.PositiveSmallIntegerField('Порядок', default=0)
    is_active = models.BooleanField('Активне', default=True)

    class Meta:
        ordering = ['sort_order', 'id']
        verbose_name = 'Соцмережа'
        verbose_name_plural = 'Соцмережі'

    def __str__(self):
        return self.get_network_display()

    @property
    def label(self):
        return self.get_network_display()
