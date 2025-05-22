from django.urls import path
from .views import VoteStatisticsView, LiveStatisticsView

urlpatterns = [
    path('vote-statistici/', VoteStatisticsView.as_view(), name='vote-statistici'),
    path('live-statistici/', LiveStatisticsView.as_view(), name='live-statistici'),
]