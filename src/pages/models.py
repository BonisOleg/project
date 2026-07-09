from django.db import models
from django.urls import reverse


class StaticPage(models.Model):
    SLUG_DELIVERY = 'delivery'
    SLUG_PAYMENT = 'payment'
    SLUG_RETURNS = 'returns'
    SLUG_ABOUT = 'about'
    SLUG_SECURITY = 'security'
    SLUG_OFFER = 'offer'
    SLUG_DROPSHIPPING = 'dropshipping'
    SLUG_SCHEDULE = 'schedule'
    SLUG_INSTRUCTIONS = 'instructions'
    SLUG_PRIVACY = 'privacy'
    SLUG_TERMS = 'terms'
    SLUG_COOKIES = 'cookies'
    SLUG_FAQ = 'faq'

    title = models.CharField('Заголовок', max_length=200)
    slug = models.SlugField('Slug', max_length=220, unique=True)
    content = models.TextField('Контент')
    meta_title = models.CharField('SEO title', max_length=255, blank=True)
    meta_description = models.TextField('SEO description', blank=True)
    is_published = models.BooleanField('Опубліковано', default=True)

    class Meta:
        verbose_name = 'Інфо-сторінка'
        verbose_name_plural = 'Інфо-сторінки'

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('pages:static', kwargs={'slug': self.slug})


class FAQItem(models.Model):
    question = models.CharField('Питання', max_length=300)
    answer = models.TextField('Відповідь')
    sort_order = models.PositiveIntegerField('Порядок', default=0)
    is_published = models.BooleanField('Опубліковано', default=True)

    class Meta:
        verbose_name = 'FAQ'
        verbose_name_plural = 'FAQ'
        ordering = ['sort_order']


class ProductInstruction(models.Model):
    title = models.CharField('Назва', max_length=300)
    sku = models.CharField('Артикул', max_length=80, blank=True)
    file = models.FileField('PDF', upload_to='instructions/', blank=True)
    external_url = models.URLField('Посилання', blank=True)
    is_published = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Інструкція'
        verbose_name_plural = 'Інструкції'


class DropshippingApplication(models.Model):
    STATUS_NEW = 'new'
    STATUS_PROCESSING = 'processing'
    STATUS_DONE = 'done'
    STATUS_CHOICES = [
        (STATUS_NEW, 'Нова'),
        (STATUS_PROCESSING, 'В обробці'),
        (STATUS_DONE, 'Завершена'),
    ]

    name = models.CharField('Імʼя', max_length=120)
    phone = models.CharField('Телефон', max_length=30)
    email = models.EmailField('Email')
    city = models.CharField('Місто', max_length=120)
    comment = models.TextField('Коментар', blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_NEW)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Заявка дропшипінг'
        verbose_name_plural = 'Заявки дропшипінг'
        ordering = ['-created_at']


class NewsletterSubscription(models.Model):
    email = models.EmailField(unique=True)
    discount_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Підписка'
        verbose_name_plural = 'Підписки'
