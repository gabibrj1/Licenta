from rest_framework import serializers
from django.conf import settings
from .models import NewsArticle, Category

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug']

class NewsArticleSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    author_name = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = NewsArticle
        fields = [
            'id', 'title', 'slug', 'summary', 'image', 'image_url', 'publish_date',
            'author_name', 'category', 'article_type', 'source',
            'is_featured', 'views_count'
        ]
    
    def get_author_name(self, obj):
        return f"{obj.author.first_name} {obj.author.last_name}" if obj.author.first_name else obj.author.username
    
    def get_image_url(self, obj):
        # Furnizăm URL-ul complet, fără prefix-ul /api/
        if obj.image:
            # Returnează calea absolută, fără domeniu
            # Aceasta va fi /media/news/images/nume_imagine.jpg
            return f"http://127.0.0.1:8000/media/{obj.image}"
        variant = (obj.id % 6) + 1
        
        # Returnează imagine implicită bazată pe categorie
        if obj.category:
            category_slug = obj.category.slug
            return f"http://127.0.0.1:8000/media/news/variants/{category_slug}_{variant}.jpg"
        return f"http://127.0.0.1:8000/media/news/variants/defaults/default_{variant}.jpg"
    
class NewsArticleDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    author_name = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = NewsArticle
        fields = [
            'id', 'title', 'slug', 'summary', 'content', 'image', 'image_url', 'image_credit',
            'publish_date', 'author_name', 'category', 'article_type', 'source',
            'source_url', 'is_featured', 'views_count'
        ]
    
    def get_author_name(self, obj):
        return f"{obj.author.first_name} {obj.author.last_name}" if obj.author.first_name else obj.author.username
    
    def get_image_url(self, obj):
        if obj.image:
            return f"http://127.0.0.1:8000/media/news/images/{obj.image.name.split('/')[-1]}"
        
        if obj.category:
            return f"http://127.0.0.1:8000/media/news/images/defaults/{obj.category.slug}.jpg"
        return f"http://127.0.0.1:8000/media/news/images/defaults/default.jpg"