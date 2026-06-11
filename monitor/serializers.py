from rest_framework import serializers
from .models import PriceHistory, Component


class PriceHistorySerializer(serializers.ModelSerializer):
    store_name = serializers.CharField(source='store.name', read_only=True)
    date = serializers.DateTimeField(source='scraped_at', format='%Y-%m-%d', read_only=True)

    class Meta:
        model = PriceHistory
        fields = ['store_name', 'price', 'date']


class ComponentSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Component
        fields = ['id', 'name', 'category_name', 'specs', 'slug']
