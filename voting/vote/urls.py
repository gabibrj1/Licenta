from django.urls import path
from .views import VoteSettingsView, AdminVoteSettingsView
from .views import UserVotingEligibilityView, FindVotingSectionView, LocalCandidatesView, SubmitLocalVoteView, CheckUserVoteStatusView

urlpatterns = [
    path('vote-settings/', VoteSettingsView.as_view(), name='vote-settings'),
    path('admin/vote-settings/', AdminVoteSettingsView.as_view(), name='admin-vote-settings'),
    path('admin/vote-settings/<int:pk>/', AdminVoteSettingsView.as_view(), name='admin-vote-settings-detail'),
    path('vote/local/eligibility/', UserVotingEligibilityView.as_view(), name='local-eligibility'),
    path('vote/local/find-section/', FindVotingSectionView.as_view(), name='find-voting-section'),
    path('vote/local/candidates/', LocalCandidatesView.as_view(), name='local-candidates'),
    path('vote/local/submit/', SubmitLocalVoteView.as_view(), name='submit-local-vote'),
    path('vote/local/check-status/', CheckUserVoteStatusView.as_view(), name='check-user-vote-status'),
] 
