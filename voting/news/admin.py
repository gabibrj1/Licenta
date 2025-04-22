from django.contrib import admin
from .models import (
    Category, NewsArticle, ExternalNewsSource,
    ElectionAnalyticsChart, ChartDataset, ChartLabels, ChartDataPoint
)

# Înregistrarea modelelor existente
admin.site.register(Category)
admin.site.register(ExternalNewsSource)

# Admin pentru articole de știri
@admin.register(NewsArticle)
class NewsArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'article_type', 'publish_date', 'is_featured', 'is_published', 'views_count')
    list_filter = ('category', 'article_type', 'is_featured', 'is_published')
    search_fields = ('title', 'content', 'summary')
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'publish_date'
    ordering = ('-publish_date',)

# Admin pentru modele de analiză
class ChartLabelsInline(admin.TabularInline):
    model = ChartLabels
    extra = 1

class ChartDatasetInline(admin.TabularInline):
    model = ChartDataset
    extra = 1

class ChartDataPointInline(admin.TabularInline):
    model = ChartDataPoint
    extra = 1

@admin.register(ElectionAnalyticsChart)
class ElectionAnalyticsChartAdmin(admin.ModelAdmin):
    list_display = ('title', 'chart_type', 'is_active', 'display_order', 'created_at')
    list_filter = ('chart_type', 'is_active')
    search_fields = ('title', 'description')
    inlines = [ChartLabelsInline, ChartDatasetInline]
    ordering = ('display_order', 'created_at')

@admin.register(ChartDataset)
class ChartDatasetAdmin(admin.ModelAdmin):
    list_display = ('chart', 'label', 'display_order')
    list_filter = ('chart',)
    inlines = [ChartDataPointInline]
    ordering = ('chart', 'display_order')