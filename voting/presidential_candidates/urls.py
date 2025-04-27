from django.urls import path
from .views import (
    PresidentialCandidateListView, PresidentialCandidateDetailView,
    ElectionYearListView, ElectionYearDetailView,
    HistoricalEventListView, MediaInfluenceListView, ControversyListView
)

urlpatterns = [
    path('candidates/', PresidentialCandidateListView.as_view(), name='presidential-candidate-list'),
    path('candidates/<int:pk>/', PresidentialCandidateDetailView.as_view(), name='presidential-candidate-detail-id'),
    path('candidates/<slug:slug>/', PresidentialCandidateDetailView.as_view(), name='presidential-candidate-detail-slug'),
    path('election-years/', ElectionYearListView.as_view(), name='election-year-list'),
    path('election-years/<int:year>/', ElectionYearDetailView.as_view(), name='election-year-detail'),
    path('historical-events/', HistoricalEventListView.as_view(), name='historical-event-list'),
    path('media-influences/', MediaInfluenceListView.as_view(), name='media-influence-list'),
    path('controversies/', ControversyListView.as_view(), name='controversy-list'),
]