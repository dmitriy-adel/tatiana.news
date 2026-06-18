from django.db import models
from django.utils import timezone

from django.utils.text import slugify


class Source(models.Model):
    """Источник новостей"""
    name = models.CharField(max_length=100, unique=True)
    main_url = models.URLField(max_length=255, blank=True, null=True)
    logo = models.ImageField(upload_to='sources/', blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Источник"
        verbose_name_plural = "Источники"


class NewsClass(models.Model):
    """Категория новости (Политика, Экономика, Спорт, Технологии и т.д.)"""
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Категория новости"
        verbose_name_plural = "Категории новостей"


class News(models.Model):
    """Основная модель новости"""
    
    title = models.CharField(max_length=500, verbose_name="Заголовок")
    text = models.TextField(verbose_name="Текст новости", blank=True)
    url = models.URLField(max_length=1000, verbose_name="Оригинальная ссылка")
    
    # Связи
    source = models.ForeignKey(
        Source, 
        on_delete=models.CASCADE, 
        related_name='news',
        verbose_name="Источник"
    )
    
    news_class = models.ForeignKey(
        NewsClass,                    
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='news',
        verbose_name="Категория"
    )
    
    key_words = models.TextField(blank=True, verbose_name="Ключевые слова")
    tags = models.JSONField(default=list, blank=True, verbose_name="Теги")
    
    external_id = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    published_at = models.DateTimeField(null=True, blank=True)
    
    hash = models.CharField(max_length=64, unique=True, blank=True)

    class Meta:
        verbose_name = "Новость"
        verbose_name_plural = "Новости"
        ordering = ['-published_at', '-created_at']

    def __str__(self):
        return f"{self.title[:80]}... ({self.source})"

    def get_absolute_url(self):
        return f"/news/{self.id}/"
