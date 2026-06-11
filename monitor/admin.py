from django.contrib import admin
from .models import Category, Store, Component, PriceHistory, Watchlist


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'slug']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ['name', 'url', 'color']
    search_fields = ['name']


@admin.register(Component)
class ComponentAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'slug']
    search_fields = ['name', 'specs']
    list_filter = ['category']


@admin.register(PriceHistory)
class PriceHistoryAdmin(admin.ModelAdmin):
    list_display = ['component', 'store', 'price', 'scraped_at']
    search_fields = ['component__name']
    list_filter = ['store', 'scraped_at']
    date_hierarchy = 'scraped_at'


@admin.register(Watchlist)
class WatchlistAdmin(admin.ModelAdmin):
    list_display = ['user', 'component', 'target_price', 'added_at', 'is_notified']
    search_fields = ['user__username', 'component__name']
    list_filter = ['is_notified']
