from django.urls import path
from .views import (
    ElectionCycleListView, ElectionCycleDetailView,
    LocalElectionTypeListView, LocalPositionListView,
    LocalElectionRuleListView, SignificantCandidateListView,
    SignificantCandidateDetailView, ImportantEventListView,
    LegislationChangeListView
)

urlpatterns = [
    path('election-cycles/', ElectionCycleListView.as_view(), name='election-cycle-list'),
    path('election-cycles/<int:year>/', ElectionCycleDetailView.as_view(), name='election-cycle-detail'),
    path('election-types/', LocalElectionTypeListView.as_view(), name='election-type-list'),
    path('positions/', LocalPositionListView.as_view(), name='position-list'),
    path('rules/', LocalElectionRuleListView.as_view(), name='election-rule-list'),
    path('significant-candidates/', SignificantCandidateListView.as_view(), name='significant-candidate-list'),
    path('significant-candidates/<int:pk>/', SignificantCandidateDetailView.as_view(), name='significant-candidate-detail-id'),
    path('significant-candidates/<slug:slug>/', SignificantCandidateDetailView.as_view(), name='significant-candidate-detail-slug'),
    path('important-events/', ImportantEventListView.as_view(), name='important-event-list'),
    path('legislation-changes/', LegislationChangeListView.as_view(), name='legislation-change-list'),
]