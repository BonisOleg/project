from django.db import models
from django.db.models import Avg, Count, Q
from django.urls import reverse
from slugify import slugify


class CategoryQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)


class Category(models.Model):
    name = models.CharField('Назва', max_length=200)
    slug = models.SlugField('Slug', max_length=220, unique=True)
    parent = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.CASCADE,
        related_name='children', verbose_name='Батьківська категорія',
    )
    description = models.TextField('Опис', blank=True)
    image = models.ImageField('Зображення', upload_to='categories/', blank=True)
    icon = models.CharField('Іконка (CSS class)', max_length=50, blank=True)
    sort_order = models.PositiveIntegerField('Порядок', default=0)
    is_active = models.BooleanField('Активна', default=True)
    meta_title = models.CharField('SEO title', max_length=255, blank=True)
    meta_description = models.TextField('SEO description', blank=True)

    objects = CategoryQuerySet.as_manager()

    class Meta:
        verbose_name = 'Категорія'
        verbose_name_plural = 'Категорії'
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('catalog:category', kwargs={'slug': self.slug})

    @property
    def is_root(self):
        return self.parent_id is None

    def get_descendant_ids(self):
        ids = [self.pk]
        for child in self.children.filter(is_active=True):
            ids.extend(child.get_descendant_ids())
        return ids


class Brand(models.Model):
    name = models.CharField('Назва', max_length=120)
    slug = models.SlugField('Slug', max_length=140, unique=True)
    is_active = models.BooleanField('Активний', default=True)

    class Meta:
        verbose_name = 'Бренд'
        verbose_name_plural = 'Бренди'
        ordering = ['name']

    def __str__(self):
        return self.name


class ProductQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)

    def top_sales(self):
        return self.active().filter(is_top_sale=True).order_by('-sort_order', '-created_at')

    def new_arrivals(self):
        return self.active().filter(is_new=True).order_by('-created_at')

    def most_viewed(self):
        return self.active().order_by('-views_count', '-created_at')

    def on_sale(self):
        return self.active().filter(old_price__isnull=False, old_price__gt=models.F('price'))

    def with_category(self):
        return self.select_related('category', 'brand').prefetch_related('images')

    def annotate_rating(self):
        return self.annotate(
            avg_rating=Avg('reviews__rating', filter=Q(reviews__is_published=True)),
            review_count=Count('reviews', filter=Q(reviews__is_published=True)),
        )


class Product(models.Model):
    AVAIL_IN_STOCK = 'in_stock'
    AVAIL_OUT = 'out_of_stock'
    AVAIL_EXPECTED = 'expected'
    AVAILABILITY_CHOICES = [
        (AVAIL_IN_STOCK, 'Є в наявності'),
        (AVAIL_OUT, 'Немає в наявності'),
        (AVAIL_EXPECTED, 'Очікується'),
    ]

    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name='products', verbose_name='Категорія',
    )
    brand = models.ForeignKey(
        Brand, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='products', verbose_name='Бренд',
    )
    name = models.CharField('Назва', max_length=300)
    slug = models.SlugField('Slug', max_length=320, unique=True)
    sku = models.CharField('Артикул', max_length=80, unique=True)
    short_description = models.TextField('Короткий опис', blank=True)
    description = models.TextField('Опис', blank=True)
    price = models.DecimalField('Ціна', max_digits=10, decimal_places=2)
    old_price = models.DecimalField('Стара ціна', max_digits=10, decimal_places=2, null=True, blank=True)
    availability = models.CharField(
        'Наявність', max_length=20, choices=AVAILABILITY_CHOICES, default=AVAIL_IN_STOCK,
    )
    is_active = models.BooleanField('Активний', default=True)
    is_top_sale = models.BooleanField('Хіт продажу', default=False)
    is_new = models.BooleanField('Новинка', default=False)
    is_on_sale = models.BooleanField('Акція', default=False)
    has_video = models.BooleanField('Є відео', default=False)
    requires_prepayment = models.BooleanField('Передоплата 100%', default=False)
    youtube_url = models.URLField('YouTube', blank=True)
    video_url = models.URLField('Відео URL', blank=True)
    views_count = models.PositiveIntegerField('Перегляди', default=0)
    sort_order = models.IntegerField('Порядок', default=0)
    sale_ends_at = models.DateTimeField('Акція до', null=True, blank=True)
    meta_title = models.CharField('SEO title', max_length=255, blank=True)
    meta_description = models.TextField('SEO description', blank=True)
    created_at = models.DateTimeField('Створено', auto_now_add=True)
    updated_at = models.DateTimeField('Оновлено', auto_now=True)

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товари'
        ordering = ['-sort_order', '-created_at']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('catalog:product', kwargs={'slug': self.slug})

    @property
    def is_available(self):
        return self.availability == self.AVAIL_IN_STOCK

    @property
    def discount_percent(self):
        if self.old_price and self.old_price > self.price:
            return int((1 - float(self.price) / float(self.old_price)) * 100)
        return 0

    @property
    def main_image(self):
        img = self.images.filter(is_main=True).first()
        if img:
            return img
        return self.images.first()

    def increment_views(self):
        Product.objects.filter(pk=self.pk).update(views_count=models.F('views_count') + 1)


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField('Зображення', upload_to='products/')
    alt_text = models.CharField('Alt', max_length=200, blank=True)
    sort_order = models.PositiveIntegerField('Порядок', default=0)
    is_main = models.BooleanField('Головне', default=False)

    class Meta:
        verbose_name = 'Зображення товару'
        verbose_name_plural = 'Зображення товарів'
        ordering = ['sort_order']


class AttributeGroup(models.Model):
    name = models.CharField('Група', max_length=120)
    sort_order = models.PositiveIntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Група характеристик'
        verbose_name_plural = 'Групи характеристик'
        ordering = ['sort_order']

    def __str__(self):
        return self.name


class ProductAttribute(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='attributes')
    group = models.ForeignKey(
        AttributeGroup, on_delete=models.SET_NULL, null=True, blank=True,
    )
    name = models.CharField('Назва', max_length=120)
    value = models.CharField('Значення', max_length=255)
    sort_order = models.PositiveIntegerField('Порядок', default=0)
    show_in_compare = models.BooleanField('У порівнянні', default=True)

    class Meta:
        verbose_name = 'Характеристика'
        verbose_name_plural = 'Характеристики'
        ordering = ['sort_order', 'name']


def make_slug(instance, source_field='name'):
    base = slugify(getattr(instance, source_field), allow_unicode=True)
    if not base:
        base = 'item'
    slug = base
    counter = 1
    model = instance.__class__
    while model.objects.filter(slug=slug).exclude(pk=instance.pk).exists():
        slug = f'{base}-{counter}'
        counter += 1
    return slug


class TopSaleProduct(Product):
    class Meta:
        proxy = True
        verbose_name = 'Топ продажу'
        verbose_name_plural = 'Топ продажу'


class NewArrivalProduct(Product):
    class Meta:
        proxy = True
        verbose_name = 'Новинка'
        verbose_name_plural = 'Новинки'


class MostViewedProduct(Product):
    class Meta:
        proxy = True
        verbose_name = 'Топ переглядів'
        verbose_name_plural = 'Топ переглядів'


class OnSaleProduct(Product):
    class Meta:
        proxy = True
        verbose_name = 'Товар на акції'
        verbose_name_plural = 'Товари на акції'
