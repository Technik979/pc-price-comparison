from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name='Название')
    slug = models.SlugField(max_length=120, unique=True, allow_unicode=True)
    icon = models.CharField(max_length=10, default='📦', verbose_name='Иконка')

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['name']

    def __str__(self):
        return self.name


class Store(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name='Название')
    url = models.URLField(blank=True, verbose_name='Сайт')
    color = models.CharField(max_length=20, default='#666', verbose_name='Цвет')

    class Meta:
        verbose_name = 'Магазин'
        verbose_name_plural = 'Магазины'

    def __str__(self):
        return self.name


class Component(models.Model):
    name = models.CharField(max_length=300, unique=True, verbose_name='Название')
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE,
        related_name='components', verbose_name='Категория',
    )
    specs = models.TextField(blank=True, verbose_name='Характеристики')
    slug = models.SlugField(max_length=400, unique=True, allow_unicode=True)

    class Meta:
        verbose_name = 'Комплектующее'
        verbose_name_plural = 'Комплектующие'
        ordering = ['category', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)[:390]
        super().save(*args, **kwargs)

    def get_latest_price(self, store_name):
        return (
            self.prices
            .filter(store__name=store_name)
            .order_by('-scraped_at')
            .values_list('price', flat=True)
            .first()
        )


class PriceHistory(models.Model):
    component = models.ForeignKey(
        Component, on_delete=models.CASCADE,
        related_name='prices', verbose_name='Товар',
    )
    store = models.ForeignKey(
        Store, on_delete=models.CASCADE, verbose_name='Магазин',
    )
    price = models.PositiveIntegerField(verbose_name='Цена, ₽')
    scraped_at = models.DateTimeField(verbose_name='Дата')

    class Meta:
        verbose_name = 'Запись цены'
        verbose_name_plural = 'История цен'
        ordering = ['scraped_at']
        indexes = [
            models.Index(fields=['component', 'scraped_at']),
            models.Index(fields=['component', 'store']),
        ]

    def __str__(self):
        return f'{self.component.name} / {self.store.name}: {self.price} ₽'


class Watchlist(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='watchlist', verbose_name='Пользователь',
    )
    component = models.ForeignKey(
        Component, on_delete=models.CASCADE,
        related_name='watched_by', verbose_name='Товар',
    )
    target_price = models.PositiveIntegerField(
        null=True, blank=True, verbose_name='Целевая цена, ₽',
    )
    added_at = models.DateTimeField(auto_now_add=True, verbose_name='Добавлено')
    is_notified = models.BooleanField(default=False, verbose_name='Уведомлён')

    class Meta:
        verbose_name = 'Запись в списке отслеживания'
        verbose_name_plural = 'Список отслеживания'
        unique_together = ['user', 'component']

    def __str__(self):
        return f'{self.user.username} → {self.component.name}'

    def is_target_reached(self):
        if not self.target_price:
            return False
        prices = [
            self.component.get_latest_price('Citilink'),
            self.component.get_latest_price('DNS'),
        ]
        valid = [p for p in prices if p is not None]
        return bool(valid) and min(valid) <= self.target_price
