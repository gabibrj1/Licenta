from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
import json

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
    
class ElectionAnalyticsChart(models.Model):
    """Model pentru grafice analitice electorale"""
    CHART_TYPES = (
        ('line', 'Linie'),
        ('bar', 'Bare'),
        ('pie', 'Pie'),
        ('doughnut', 'Doughnut'),
        ('radar', 'Radar'),
    )
    
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    chart_type = models.CharField(max_length=20, choices=CHART_TYPES)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    display_order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['display_order', 'created_at']
        verbose_name = "Grafic Analitic"
        verbose_name_plural = "Grafice Analitice"
    
    def __str__(self):
        return self.title
    
    def get_data(self):
        """Returnează setul de date complet pentru acest grafic"""
        data = {
            'labels': [dataset.label for dataset in self.chartlabels_set.all().order_by('position')],
            'datasets': []
        }
        
        datasets = {}
        # Grupează datele după setul de date
        for datapoint in self.chartdatapoint_set.all():
            if datapoint.dataset_id not in datasets:
                datasets[datapoint.dataset_id] = {
                    'label': datapoint.dataset.label,
                    'data': [],
                    'backgroundColor': datapoint.dataset.background_color.split(',') if datapoint.dataset.background_color else None,
                    'borderColor': datapoint.dataset.border_color,
                    'fill': datapoint.dataset.fill
                }
            datasets[datapoint.dataset_id]['data'].append(datapoint.value)
        
        # Adaugă seturile de date în ordinea corectă
        for dataset_id, dataset_data in datasets.items():
            data['datasets'].append(dataset_data)
            
        return data
    
    def to_dict(self):
        """Convertește graficul într-un dicționar pentru API"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'type': self.chart_type,
            'data': self.get_data()
        }


class ChartDataset(models.Model):
    """Model pentru seturile de date din grafice"""
    chart = models.ForeignKey(ElectionAnalyticsChart, on_delete=models.CASCADE)
    label = models.CharField(max_length=255)
    background_color = models.CharField(max_length=255, blank=True, null=True, 
                                       help_text="Culori separate prin virgulă, ex: #ff6b6b,#5f27cd,#1dd1a1")
    border_color = models.CharField(max_length=50, blank=True, null=True)
    fill = models.BooleanField(default=False)
    display_order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['display_order']
        verbose_name = "Set de Date"
        verbose_name_plural = "Seturi de Date"
    
    def __str__(self):
        return f"{self.chart.title} - {self.label}"


class ChartLabels(models.Model):
    """Model pentru etichetele din grafice"""
    chart = models.ForeignKey(ElectionAnalyticsChart, on_delete=models.CASCADE)
    label = models.CharField(max_length=50)
    position = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['position']
        verbose_name = "Etichetă"
        verbose_name_plural = "Etichete"
    
    def __str__(self):
        return f"{self.chart.title} - {self.label}"


class ChartDataPoint(models.Model):
    """Model pentru punctele de date din grafice"""
    chart = models.ForeignKey(ElectionAnalyticsChart, on_delete=models.CASCADE)
    dataset = models.ForeignKey(ChartDataset, on_delete=models.CASCADE)
    label = models.ForeignKey(ChartLabels, on_delete=models.CASCADE)
    value = models.FloatField()
    
    class Meta:
        unique_together = ('dataset', 'label')
        verbose_name = "Punct de Date"
        verbose_name_plural = "Puncte de Date"
    
    def __str__(self):
        return f"{self.dataset.label} - {self.label.label}: {self.value}"