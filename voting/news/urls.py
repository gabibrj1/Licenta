from django.urls import path
from . import views

urlpatterns = [
    path('', views.news_home, name='news_home'),
    path('article/<slug:slug>/', views.article_detail, name='article_detail'),
    path('category/<slug:slug>/', views.category_articles, name='category_articles'),
    path('api/latest/', views.LatestNewsAPI.as_view(), name='api_latest_news'),
    path('api/external/', views.ExternalNewsAPI.as_view(), name='api_external_news'),
    path('api/analytics/', views.ElectionAnalyticsAPI.as_view(), name='api_election_analytics'),
    path('api/article/<slug:slug>/', views.ArticleDetailAPI.as_view(), name='api_article_detail'),
    path('api/opinions/', views.OpinionsAPI.as_view(), name='api_opinions'),
]