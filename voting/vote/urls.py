from django.urls import path
from .views import VoteSettingsView, AdminVoteSettingsView
from .views import UserVotingEligibilityView, FindVotingSectionView, LocalCandidatesView, SubmitLocalVoteView, CheckUserVoteStatusView,VoteMonitoringView
from .views import ConfirmVoteAndSendReceiptView, GenerateVoteReceiptPDFView
from .views import UserPresidentialVotingEligibilityView, PresidentialCandidatesView, CheckPresidentialVoteStatusView, SubmitPresidentialVoteView, GeneratePresidentialVoteReceiptPDFView
from .views import UserParliamentaryVotingEligibilityView, ParliamentaryPartiesView, CheckParliamentaryVoteStatusView, SubmitParliamentaryVoteView, GenerateParliamentaryVoteReceiptPDFView
from .views import CreateVoteSystemView, UserVoteSystemsView, VoteSystemDetailView, SubmitVoteView
from .views import PublicVoteSystemView, PublicSubmitVoteView, PublicVoteResultsView
from .views import ManageVoterEmailsView, SendVoteTokensView, VerifyVoteTokenView, CheckActiveVoteSystemView, VoteSystemResultsUpdateView, ActiveRoundVotingStatisticsView, ActiveRoundUATVotingStatisticsView
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
    path('vote-systems/create/', CreateVoteSystemView.as_view(), name='create-vote-system'),
    path('vote-systems/user/', UserVoteSystemsView.as_view(), name='user-vote-systems'),    
    path('vote-systems/<int:system_id>/', VoteSystemDetailView.as_view(), name='vote-system-detail'),
    path('vote-systems/<int:system_id>/vote/', SubmitVoteView.as_view(), name='submit-vote'),
    path('vote-systems/<int:system_id>/public/', PublicVoteSystemView.as_view(), name='public-vote-system'),
    path('vote-systems/<int:system_id>/public-vote/', PublicSubmitVoteView.as_view(), name='public-submit-vote'),
    path('vote-systems/<int:system_id>/public-results/', PublicVoteResultsView.as_view(), name='public-vote-results'),  
    path('vote-systems/<int:system_id>/manage-emails/', ManageVoterEmailsView.as_view(), name='manage-voter-emails'),
    path('vote-systems/<int:system_id>/send-tokens/', SendVoteTokensView.as_view(), name='send-vote-tokens'),
    path('vote-systems/<int:system_id>/verify-token/', VerifyVoteTokenView.as_view(), name='verify-vote-token'),
    path('vote-systems/check-active/', CheckActiveVoteSystemView.as_view(), name='check-active-vote-system'),
    path('vote-systems/<int:system_id>/results-update/', VoteSystemResultsUpdateView.as_view(), name='vote-system-results-update'),
    path('vote/active-round-statistics/', ActiveRoundVotingStatisticsView.as_view(), name='active-round-statistics'),
    path('vote/active-round-uat-statistics/<str:county_code>/', ActiveRoundUATVotingStatisticsView.as_view(), name='active-round-uat-statistics'),
] 
