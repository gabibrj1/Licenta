from django.urls import path
from .views import VoteResultsView, LiveResultsView

urlpatterns = [
    path('vote-rezultate/', VoteResultsView.as_view(), name='vote-rezultate'),
    path('live-rezultate/', LiveResultsView.as_view(), name='live-rezultate'),
]