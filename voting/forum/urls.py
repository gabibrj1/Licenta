from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Configurare Router
router = DefaultRouter()
router.register(r'categories', views.CategoryViewSet)
router.register(r'topics', views.TopicViewSet)
router.register(r'posts', views.PostViewSet)
router.register(r'attachments', views.AttachmentViewSet)
router.register(r'notifications', views.NotificationViewSet, basename='notification')

urlpatterns = [
    path('', include(router.urls)),
    path('search/', views.SearchView.as_view(), name='forum-search'),
    path('stats/', views.ForumStatsView.as_view(), name='forum-stats'),
    path('user/newsletter-status/', views.NewsletterStatusView.as_view(), name='newsletter-status'),
    path('user/subscribe-newsletter/', views.SubscribeNewsletterView.as_view(), name='subscribe-newsletter'),
    path('user/unsubscribe-newsletter/', views.UnsubscribeNewsletterView.as_view(), name='unsubscribe-newsletter'),
     path('user/notification-preferences/', views.NotificationPreferencesView.as_view(), name='notification-preferences'),
]