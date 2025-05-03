from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views



urlpatterns = [
    path('profile/', views.UserProfileView.as_view(), name='user-profile'),
    path('profile-image/', views.ProfileImageView.as_view(), name='profile-image'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change-password'),
    path('delete-account/', views.DeleteAccountView.as_view(), name='delete-account'),
    path('settings/', views.AccountSettingsView.as_view(), name='account-settings'),

]