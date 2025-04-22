from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    
    class Meta:
        verbose_name_plural = "Categories"
    
    def __str__(self):
        return self.name

class NewsArticle(models.Model):
    ARTICLE_TYPES = (
        ('news', 'Știre'),
        ('analysis', 'Analiză'),
        ('opinion', 'Opinie'),
        ('interview', 'Interviu'),
    )
    
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    content = models.TextField()
    summary = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='news/images/', blank=True, null=True)
    image_credit = models.CharField(max_length=255, blank=True, null=True)
    publish_date = models.DateTimeField(default=timezone.now)
    updated_date = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='articles')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='articles')
    article_type = models.CharField(max_length=20, choices=ARTICLE_TYPES, default='news')
    source = models.CharField(max_length=255, blank=True, null=True)
    source_url = models.URLField(blank=True, null=True)
    is_featured = models.BooleanField(default=False)
    is_published = models.BooleanField(default=True)
    views_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['-publish_date']
    
    def __str__(self):
        return self.title

class ExternalNewsSource(models.Model):
    name = models.CharField(max_length=100)
    url = models.URLField()
    logo = models.ImageField(upload_to='news/sources/logos/', blank=True, null=True)
    api_key = models.CharField(max_length=255, blank=True, null=True)
    api_endpoint = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name