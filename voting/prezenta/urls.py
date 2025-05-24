from django.urls import path
from .views import VotingPresenceView, LivePresenceView

urlpatterns = [
    path('voting-presence/', VotingPresenceView.as_view(), name='voting-presence'),
    path('live-presence/', LivePresenceView.as_view(), name='live-presence'),
]