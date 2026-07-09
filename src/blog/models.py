from django.db import models
from django.urls import reverse
from django.utils import timezone
from slugify import slugify


class PostQuerySet(models.QuerySet):
    def published(self):
        return self.filter(is_published=True, published_at__lte=timezone.now())


class Post(models.Model):
    title = models.CharField('Заголовок', max_length=300)
    slug = models.SlugField('Slug', max_length=320, unique=True)
    excerpt = models.TextField('Короткий опис', blank=True)
    content = models.TextField('Контент')
    image = models.ImageField('Зображення', upload_to='blog/', blank=True)
    is_published = models.BooleanField('Опубліковано', default=False)
    published_at = models.DateTimeField('Дата публікації', default=timezone.now)
    meta_title = models.CharField('SEO title', max_length=255, blank=True)
    meta_description = models.TextField('SEO description', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = PostQuerySet.as_manager()

    class Meta:
        verbose_name = 'Стаття'
        verbose_name_plural = 'Блог'
        ordering = ['-published_at']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('blog:detail', kwargs={'slug': self.slug})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title, allow_unicode=True)
        super().save(*args, **kwargs)
