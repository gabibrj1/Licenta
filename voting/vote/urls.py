from django.urls import path
from .views import VoteSettingsView, AdminVoteSettingsView

urlpatterns = [
    path('vote-settings/', VoteSettingsView.as_view(), name='vote-settings'),
    path('admin/vote-settings/', AdminVoteSettingsView.as_view(), name='admin-vote-settings'),
    path('admin/vote-settings/<int:pk>/', AdminVoteSettingsView.as_view(), name='admin-vote-settings-detail'),
]