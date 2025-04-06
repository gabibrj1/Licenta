from django.urls import path
from .views import VoteSettingsView, AdminVoteSettingsView
from .views import UserVotingEligibilityView, FindVotingSectionView, LocalCandidatesView, SubmitLocalVoteView, CheckUserVoteStatusView,VoteMonitoringView
from .views import ConfirmVoteAndSendReceiptView, GenerateVoteReceiptPDFView
from .views import UserPresidentialVotingEligibilityView, PresidentialCandidatesView, CheckPresidentialVoteStatusView, SubmitPresidentialVoteView, GeneratePresidentialVoteReceiptPDFView
from .views import UserParliamentaryVotingEligibilityView, ParliamentaryPartiesView, CheckParliamentaryVoteStatusView, SubmitParliamentaryVoteView, GenerateParliamentaryVoteReceiptPDFView
urlpatterns = [
    path('vote-settings/', VoteSettingsView.as_view(), name='vote-settings'),
    path('admin/vote-settings/', AdminVoteSettingsView.as_view(), name='admin-vote-settings'),
    path('admin/vote-settings/<int:pk>/', AdminVoteSettingsView.as_view(), name='admin-vote-settings-detail'),
    path('vote/local/eligibility/', UserVotingEligibilityView.as_view(), name='local-eligibility'),
    path('vote/local/find-section/', FindVotingSectionView.as_view(), name='find-voting-section'),
    path('vote/local/candidates/', LocalCandidatesView.as_view(), name='local-candidates'),
    path('vote/local/submit/', SubmitLocalVoteView.as_view(), name='submit-local-vote'),
    path('vote/local/check-status/', CheckUserVoteStatusView.as_view(), name='check-user-vote-status'),
    path('vote/monitoring/', VoteMonitoringView.as_view(), name='vote-monitoring'),
    path('vote/local/confirm-and-send/', ConfirmVoteAndSendReceiptView.as_view(), name='confirm-vote-and-send'),
    path('vote/local/receipt-pdf/', GenerateVoteReceiptPDFView.as_view(), name='generate-vote-receipt-pdf'),    
    path('vote/presidential/eligibility/', UserPresidentialVotingEligibilityView.as_view(), name='presidential-eligibility'),
    path('vote/presidential/candidates/', PresidentialCandidatesView.as_view(), name='presidential-candidates'),
    path('vote/presidential/check-status/', CheckPresidentialVoteStatusView.as_view(), name='check-presidential-vote-status'),
    path('vote/presidential/submit/', SubmitPresidentialVoteView.as_view(), name='submit-presidential-vote'),
    path('vote/presidential/receipt-pdf/', GeneratePresidentialVoteReceiptPDFView.as_view(), name='generate-presidential-vote-receipt-pdf'),
    path('vote/parliamentary/eligibility/', UserParliamentaryVotingEligibilityView.as_view(), name='parliamentary-eligibility'),
    path('vote/parliamentary/parties/', ParliamentaryPartiesView.as_view(), name='parliamentary-parties'),
    path('vote/parliamentary/check-status/', CheckParliamentaryVoteStatusView.as_view(), name='check-parliamentary-vote-status'),
    path('vote/parliamentary/submit/', SubmitParliamentaryVoteView.as_view(), name='submit-parliamentary-vote'),
    path('vote/parliamentary/receipt-pdf/', GenerateParliamentaryVoteReceiptPDFView.as_view(), name='generate-parliamentary-vote-receipt-pdf'),

] 
